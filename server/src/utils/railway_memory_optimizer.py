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
import gc
import ctypes
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Railway 8GB plan limits
RAILWAY_TOTAL_MEMORY_GB = 8.0
RAILWAY_SYSTEM_OVERHEAD_GB = 0.5  # OS + Node.js/Python baseline
RAILWAY_EFFECTIVE_MEMORY_GB = RAILWAY_TOTAL_MEMORY_GB - RAILWAY_SYSTEM_OVERHEAD_GB  # 7.5GB

# Memory thresholds (percentage of EFFECTIVE memory, not total)
MEMORY_WARNING_THRESHOLD = 0.70  # 70% of 7.5GB = 5.25GB - Start monitoring closely
MEMORY_CRITICAL_THRESHOLD = 0.80  # 80% of 7.5GB = 6.00GB - Abort new allocations
MEMORY_PAUSE_THRESHOLD = 0.87     # 87% of 7.5GB = 6.50GB - PAUSE work, cleanup, resume
MEMORY_EMERGENCY_THRESHOLD = 0.93 # 93% of 7.5GB = 7.00GB - Emergency cleanup or abort
MEMORY_OOM_THRESHOLD = 0.95       # 95% of 8.0GB = 7.60GB - Railway will OOM kill soon

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
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
        self.peak_memory_gb = 0.0
        self.warning_count = 0
        self.pause_count = 0
        self.cleanup_count = 0

    def get_memory_stats(self):
        """Get current memory statistics"""
        if not PSUTIL_AVAILABLE or not self.process:
            return None

        try:
            memory_info = self.process.memory_info()
            virtual_memory = psutil.virtual_memory()

            current_gb = memory_info.rss / (1024**3)
            total_gb = virtual_memory.total / (1024**3)
            available_gb = virtual_memory.available / (1024**3)
            percent = (current_gb / RAILWAY_EFFECTIVE_MEMORY_GB) * 100  # Percent of EFFECTIVE memory

            # Track peak
            if current_gb > self.peak_memory_gb:
                self.peak_memory_gb = current_gb

            return {
                'current_gb': current_gb,
                'total_gb': total_gb,
                'available_gb': available_gb,
                'percent': percent,  # Percent of effective memory (7.5GB)
                'peak_gb': self.peak_memory_gb,
                'effective_gb': RAILWAY_EFFECTIVE_MEMORY_GB
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

    def force_memory_release(self, wait_for_target_gb=None, max_wait_seconds=30):
        """
        Aggressively free memory back to OS

        Args:
            wait_for_target_gb: If specified, wait until memory drops below this value
            max_wait_seconds: Maximum time to wait for target (default 30s)

        Returns:
            bool: True if target achieved or no target set, False if timeout
        """
        try:
            memory_before = self.get_memory_stats()
            if not memory_before:
                return True  # Can't check, assume success

            logger.info(f"🧹 AGGRESSIVE MEMORY CLEANUP (Railway Optimization)")
            logger.info(f"   Before: {memory_before['current_gb']:.2f}GB ({memory_before['percent']:.1f}%)")

            # Step 1: Full garbage collection (all generations, multiple cycles)
            logger.info(f"   Running full GC...")
            collected_total = 0
            cycle_num = 0
            for cycle_num in range(10):  # Up to 10 cycles
                collected = gc.collect(generation=2)
                collected_total += collected
                if collected == 0:
                    break
                logger.debug(f"   GC cycle {cycle_num + 1}: {collected} objects")

            logger.info(f"   GC collected {collected_total} objects in {cycle_num + 1} cycles")

            # Step 2: Force malloc to return memory to OS (Linux only)
            try:
                libc = ctypes.CDLL('libc.so.6')
                bytes_freed = libc.malloc_trim(0)
                logger.info(f"   malloc_trim: freed memory to OS (returned {bytes_freed})")
            except Exception as e:
                logger.debug(f"   malloc_trim not available (non-Linux): {e}")

            # Step 3: Clear Python internal caches
            try:
                import sys
                # Use the non-deprecated method if available
                if hasattr(sys, '_clear_internal_caches'):
                    sys._clear_internal_caches()
                else:
                    sys._clear_type_cache()
                logger.info(f"   Cleared Python internal caches")
            except Exception as e:
                logger.debug(f"   Could not clear caches: {e}")

            # Check immediate result
            memory_after = self.get_memory_stats()
            if memory_after:
                freed_gb = memory_before['current_gb'] - memory_after['current_gb']
                logger.info(f"   After cleanup: {memory_after['current_gb']:.2f}GB ({memory_after['percent']:.1f}%)")
                if freed_gb > 0.01:
                    logger.info(f"   ✅ Freed {freed_gb:.2f}GB immediately")
                else:
                    logger.warning(f"   ⚠️  Only freed {freed_gb:.3f}GB immediately")

                # If target specified, wait for memory to drop further
                if wait_for_target_gb:
                    logger.info(f"   🎯 Target: {wait_for_target_gb:.2f}GB, waiting up to {max_wait_seconds}s...")

                    start_time = time.time()
                    wait_cycles = 0
                    elapsed = 0.0

                    while memory_after['current_gb'] > wait_for_target_gb:
                        elapsed = time.time() - start_time
                        if elapsed > max_wait_seconds:
                            logger.warning(f"   ⏱️  Timeout after {max_wait_seconds}s")
                            logger.warning(f"   Current: {memory_after['current_gb']:.2f}GB, Target: {wait_for_target_gb:.2f}GB")
                            return False

                        # Wait a bit for OS to release memory
                        time.sleep(1)
                        wait_cycles += 1

                        # Additional GC every 5 seconds
                        if wait_cycles % 5 == 0:
                            gc.collect(generation=2)

                        memory_after = self.get_memory_stats()
                        if not memory_after:
                            return True  # Can't check, assume success

                    # Update elapsed time after loop
                    elapsed = time.time() - start_time
                    total_freed = memory_before['current_gb'] - memory_after['current_gb']
                    logger.info(f"   ✅ Target achieved in {elapsed:.1f}s")
                    logger.info(f"   Final: {memory_after['current_gb']:.2f}GB ({memory_after['percent']:.1f}%)")
                    logger.info(f"   Total freed: {total_freed:.2f}GB")
                    return True

            self.cleanup_count += 1
            return True

        except Exception as e:
            logger.error(f"Error during aggressive memory cleanup: {e}")
            return False

    def pause_and_cleanup_if_needed(self, current_phase=""):
        """
        Check if we need to pause work and cleanup memory

        Args:
            current_phase: Description of current phase (for logging)

        Returns:
            bool: True if safe to continue, False if should abort
        """
        stats = self.get_memory_stats()
        if not stats:
            return True  # Can't check, allow to continue

        current_gb = stats['current_gb']
        percent = stats['percent']

        # Check if we need to pause and cleanup
        if percent >= MEMORY_PAUSE_THRESHOLD * 100:
            self.pause_count += 1
            logger.warning(f"⏸️  PAUSE {self.pause_count}: Memory at {current_gb:.2f}GB ({percent:.1f}%)")
            logger.warning(f"   Phase: {current_phase}")
            logger.warning(f"   Threshold: {MEMORY_PAUSE_THRESHOLD * 100:.1f}% ({MEMORY_PAUSE_THRESHOLD * RAILWAY_EFFECTIVE_MEMORY_GB:.2f}GB)")

            # Target: drop to 70% (5.25GB) or at least below 80% (6.0GB)
            target_gb = MEMORY_WARNING_THRESHOLD * RAILWAY_EFFECTIVE_MEMORY_GB  # 5.25GB
            fallback_gb = MEMORY_CRITICAL_THRESHOLD * RAILWAY_EFFECTIVE_MEMORY_GB  # 6.0GB

            logger.info(f"   🧹 Attempting cleanup to {target_gb:.2f}GB...")
            success = self.force_memory_release(wait_for_target_gb=target_gb, max_wait_seconds=30)

            # Check result
            stats_after = self.get_memory_stats()
            if stats_after:
                if stats_after['current_gb'] <= target_gb:
                    logger.info(f"   ✅ Cleanup successful, resuming work")
                    return True
                elif stats_after['current_gb'] <= fallback_gb:
                    logger.warning(f"   ⚠️  Partial cleanup ({stats_after['current_gb']:.2f}GB), continuing carefully")
                    return True
                else:
                    logger.error(f"   ❌ Cleanup insufficient: {stats_after['current_gb']:.2f}GB > {fallback_gb:.2f}GB")
                    logger.error(f"   Cannot continue - would risk OOM")
                    return False

            return success

        # Below pause threshold, safe to continue
        return True


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
