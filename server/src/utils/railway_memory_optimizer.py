"""
Railway Memory Optimizer for Gang Sheet Creation

Comprehensive memory management for Railway's 8GB limit.
Prevents OOM crashes through:
- Batch processing
- Progressive monitoring
- Auto-dimension adjustment
- Emergency cleanup
"""

import os
import logging
import psutil
import gc
import ctypes

logger = logging.getLogger(__name__)

# Railway 8GB plan limits
RAILWAY_TOTAL_MEMORY_GB = 8.0
RAILWAY_SYSTEM_OVERHEAD_GB = 0.5  # OS + Node.js/Python baseline
RAILWAY_EFFECTIVE_MEMORY_GB = RAILWAY_TOTAL_MEMORY_GB - RAILWAY_SYSTEM_OVERHEAD_GB  # 7.5GB

# Memory thresholds
MEMORY_WARNING_THRESHOLD = 0.70  # 70% - Start monitoring closely
MEMORY_CRITICAL_THRESHOLD = 0.80  # 80% - Abort new allocations
MEMORY_EMERGENCY_THRESHOLD = 0.85  # 85% - Emergency cleanup
MEMORY_OOM_THRESHOLD = 0.95  # 95% - Railway will OOM kill soon

# Gang sheet limits
MAX_DPI = 400  # Enforce 400 DPI max (memory grows with DPI²)
MAX_GANG_SHEET_MEMORY_GB = 3.0  # Single gang sheet max size
MAX_GANG_SHEET_DIMENSION_PIXELS = 100000  # 100k pixels max per dimension

# Batch processing
DESIGN_DOWNLOAD_BATCH_SIZE = 10  # Download 10 designs at a time
DESIGN_PROCESS_BATCH_SIZE = 20  # Process 20 designs before memory check


class RailwayMemoryMonitor:
    """Monitor and manage memory usage on Railway"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.peak_memory_gb = 0.0
        self.warning_count = 0

    def get_memory_stats(self):
        """Get current memory statistics"""
        try:
            memory_info = self.process.memory_info()
            virtual_memory = psutil.virtual_memory()

            current_gb = memory_info.rss / (1024**3)
            total_gb = virtual_memory.total / (1024**3)
            available_gb = virtual_memory.available / (1024**3)
            percent = (current_gb / total_gb) * 100

            # Track peak
            if current_gb > self.peak_memory_gb:
                self.peak_memory_gb = current_gb

            return {
                'current_gb': current_gb,
                'total_gb': total_gb,
                'available_gb': available_gb,
                'percent': percent,
                'peak_gb': self.peak_memory_gb
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return None

    def check_memory_safe(self, required_gb=0.0):
        """Check if we have enough memory for operation"""
        stats = self.get_memory_stats()
        if not stats:
            return True  # If can't check, allow operation

        current_percent = stats['percent']
        projected_gb = stats['current_gb'] + required_gb
        projected_percent = (projected_gb / RAILWAY_EFFECTIVE_MEMORY_GB) * 100

        # Critical: Already using too much
        if current_percent >= MEMORY_CRITICAL_THRESHOLD * 100:
            logger.error(f"❌ CRITICAL: Memory at {current_percent:.1f}% (>{MEMORY_CRITICAL_THRESHOLD*100}%)")
            logger.error(f"   Current: {stats['current_gb']:.2f}GB / {RAILWAY_EFFECTIVE_MEMORY_GB:.2f}GB")
            return False

        # Check if allocation would push us over limit
        if required_gb > 0 and projected_percent >= MEMORY_EMERGENCY_THRESHOLD * 100:
            logger.error(f"❌ Cannot allocate {required_gb:.2f}GB")
            logger.error(f"   Would push memory to {projected_percent:.1f}% (>{MEMORY_EMERGENCY_THRESHOLD*100}%)")
            logger.error(f"   Current: {stats['current_gb']:.2f}GB, Projected: {projected_gb:.2f}GB")
            return False

        # Warning threshold
        if current_percent >= MEMORY_WARNING_THRESHOLD * 100:
            self.warning_count += 1
            logger.warning(f"⚠️  Memory at {current_percent:.1f}% (warning threshold)")
            logger.warning(f"   Current: {stats['current_gb']:.2f}GB / {RAILWAY_EFFECTIVE_MEMORY_GB:.2f}GB")

        return True

    def force_memory_release(self):
        """Aggressively free memory back to OS"""
        try:
            memory_before = self.get_memory_stats()
            if not memory_before:
                return

            logger.info(f"🧹 AGGRESSIVE MEMORY CLEANUP (Railway Optimization)")
            logger.info(f"   Before: {memory_before['current_gb']:.2f}GB")

            # Step 1: Full garbage collection (all generations)
            collected_total = 0
            for i in range(5):
                collected = gc.collect(generation=2)
                collected_total += collected
                if collected == 0:
                    break

            logger.info(f"   GC collected {collected_total} objects")

            # Step 2: Force malloc to return memory to OS (Linux only)
            try:
                libc = ctypes.CDLL('libc.so.6')
                bytes_freed = libc.malloc_trim(0)
                logger.info(f"   malloc_trim returned: {bytes_freed}")
            except Exception as e:
                logger.debug(f"   malloc_trim not available (non-Linux): {e}")

            # Step 3: Clear Python internal caches
            try:
                import sys
                sys._clear_type_cache()
                logger.info(f"   Cleared Python type cache")
            except Exception as e:
                logger.debug(f"   Could not clear type cache: {e}")

            # Check result
            memory_after = self.get_memory_stats()
            if memory_after:
                freed_gb = memory_before['current_gb'] - memory_after['current_gb']
                logger.info(f"   After: {memory_after['current_gb']:.2f}GB")
                if freed_gb > 0.01:
                    logger.info(f"   ✅ Freed {freed_gb:.2f}GB")
                else:
                    logger.warning(f"   ⚠️  No significant memory freed")

        except Exception as e:
            logger.error(f"Error during aggressive memory cleanup: {e}")


class GangSheetMemoryOptimizer:
    """Optimize gang sheet dimensions for Railway memory limits"""

    @staticmethod
    def validate_and_adjust_dimensions(width_inches, height_inches, dpi):
        """
        Validate and adjust gang sheet dimensions to fit Railway memory.
        Returns: (width_px, height_px, dpi, memory_gb, adjusted)
        """

        # Enforce max DPI
        original_dpi = dpi
        if dpi > MAX_DPI:
            logger.warning(f"DPI {dpi} exceeds max {MAX_DPI}, reducing to {MAX_DPI}")
            dpi = MAX_DPI

        # Calculate pixel dimensions
        width_px = int(width_inches * dpi)
        height_px = int(height_inches * dpi)

        # Calculate memory requirement (RGBA = 4 bytes per pixel)
        memory_gb = (width_px * height_px * 4) / (1024**3)

        adjusted = False

        # Check if single dimension is too large
        if width_px > MAX_GANG_SHEET_DIMENSION_PIXELS:
            logger.warning(f"Width {width_px}px exceeds max {MAX_GANG_SHEET_DIMENSION_PIXELS}px")
            width_px = MAX_GANG_SHEET_DIMENSION_PIXELS
            width_inches = width_px / dpi
            memory_gb = (width_px * height_px * 4) / (1024**3)
            adjusted = True

        if height_px > MAX_GANG_SHEET_DIMENSION_PIXELS:
            logger.warning(f"Height {height_px}px exceeds max {MAX_GANG_SHEET_DIMENSION_PIXELS}px")
            height_px = MAX_GANG_SHEET_DIMENSION_PIXELS
            height_inches = height_px / dpi
            memory_gb = (width_px * height_px * 4) / (1024**3)
            adjusted = True

        # Check if total memory exceeds limit
        if memory_gb > MAX_GANG_SHEET_MEMORY_GB:
            logger.warning(f"Gang sheet memory {memory_gb:.2f}GB exceeds max {MAX_GANG_SHEET_MEMORY_GB}GB")

            # Calculate reduction factor
            reduction_factor = (MAX_GANG_SHEET_MEMORY_GB / memory_gb) ** 0.5

            # Reduce height (preserve width for design fit)
            new_height_px = int(height_px * reduction_factor)
            new_height_inches = new_height_px / dpi

            logger.warning(f"Reducing height from {height_inches:.1f}\" to {new_height_inches:.1f}\"")

            height_px = new_height_px
            height_inches = new_height_inches
            memory_gb = (width_px * height_px * 4) / (1024**3)
            adjusted = True

        if adjusted:
            logger.info(f"📐 Adjusted dimensions: {width_inches:.1f}\"×{height_inches:.1f}\" = {width_px}×{height_px}px @ {dpi} DPI")
            logger.info(f"   Memory requirement: {memory_gb:.2f}GB")
        else:
            logger.info(f"📐 Dimensions OK: {width_inches:.1f}\"×{height_inches:.1f}\" = {width_px}×{height_px}px @ {dpi} DPI")
            logger.info(f"   Memory requirement: {memory_gb:.2f}GB")

        return width_px, height_px, dpi, memory_gb, adjusted


class BatchProcessor:
    """Process designs in batches to control memory usage"""

    def __init__(self, monitor: RailwayMemoryMonitor):
        self.monitor = monitor
        self.batch_size = DESIGN_DOWNLOAD_BATCH_SIZE

    def process_in_batches(self, items, process_func, description="items"):
        """
        Process items in batches with memory monitoring.

        Args:
            items: List of items to process
            process_func: Function to process each item (item, index) -> result
            description: Description for logging

        Returns:
            List of results
        """
        total_items = len(items)
        results = []

        logger.info(f"📦 Processing {total_items} {description} in batches of {self.batch_size}")

        for batch_start in range(0, total_items, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_items)
            batch_num = (batch_start // self.batch_size) + 1
            total_batches = (total_items + self.batch_size - 1) // self.batch_size

            logger.info(f"📦 Batch {batch_num}/{total_batches}: Processing {description} {batch_start+1}-{batch_end}")

            # Check memory before batch
            if not self.monitor.check_memory_safe():
                logger.error(f"❌ Insufficient memory for batch {batch_num}, aborting")
                break

            # Process batch
            batch_results = []
            for i in range(batch_start, batch_end):
                try:
                    result = process_func(items[i], i)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {description} {i}: {e}")
                    batch_results.append(None)

            results.extend(batch_results)

            # Memory check after batch
            stats = self.monitor.get_memory_stats()
            if stats:
                logger.info(f"   Memory after batch: {stats['current_gb']:.2f}GB ({stats['percent']:.1f}%)")

                # Emergency cleanup if memory high
                if stats['percent'] >= MEMORY_EMERGENCY_THRESHOLD * 100:
                    logger.warning(f"⚠️  Memory at {stats['percent']:.1f}%, running emergency cleanup")
                    self.monitor.force_memory_release()

        return results


# Convenience functions
def get_railway_memory_monitor():
    """Get or create global memory monitor"""
    global _railway_monitor
    if '_railway_monitor' not in globals():
        _railway_monitor = RailwayMemoryMonitor()
    return _railway_monitor


def check_railway_memory_safe(required_gb=0.0):
    """Quick check if memory is safe for operation"""
    monitor = get_railway_memory_monitor()
    return monitor.check_memory_safe(required_gb)


def force_railway_memory_release():
    """Force aggressive memory cleanup"""
    monitor = get_railway_memory_monitor()
    monitor.force_memory_release()


def validate_gang_sheet_dimensions(width_inches, height_inches, dpi):
    """Validate and auto-adjust gang sheet dimensions for Railway"""
    optimizer = GangSheetMemoryOptimizer()
    return optimizer.validate_and_adjust_dimensions(width_inches, height_inches, dpi)


def create_batch_processor():
    """Create batch processor with memory monitoring"""
    monitor = get_railway_memory_monitor()
    return BatchProcessor(monitor)
