"""
Emergency Memory Protection Module

Prevents OOM (Out of Memory) kills by proactively monitoring
and limiting memory usage before Railway terminates the process.
"""

import logging
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory protection disabled")


class MemoryGuard:
    """Monitors memory and prevents OOM kills"""

    def __init__(self, max_memory_percent: float = 85.0):
        """
        Initialize memory guard.

        Args:
            max_memory_percent: Maximum allowed memory usage (default 85%)
                Railway typically OOM kills at ~95%, so we stop at 85% for safety
        """
        self.max_memory_percent = max_memory_percent
        self.total_memory_gb = None

        if PSUTIL_AVAILABLE:
            try:
                self.total_memory_gb = psutil.virtual_memory().total / (1024**3)
                logging.info(f"🛡️  Memory Guard initialized: {self.total_memory_gb:.2f}GB total, {max_memory_percent}% limit")
            except:
                pass

    def check_memory(self) -> dict:
        """
        Check current memory status.

        Returns:
            dict with memory info: {
                'current_gb': float,
                'total_gb': float,
                'percent': float,
                'available_gb': float,
                'safe': bool
            }
        """
        if not PSUTIL_AVAILABLE:
            return {'safe': True, 'reason': 'monitoring_disabled'}

        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            vm = psutil.virtual_memory()

            current_gb = memory_info.rss / (1024**3)
            total_gb = vm.total / (1024**3)
            available_gb = vm.available / (1024**3)
            percent = (current_gb / total_gb) * 100

            is_safe = percent < self.max_memory_percent

            return {
                'current_gb': current_gb,
                'total_gb': total_gb,
                'available_gb': available_gb,
                'percent': percent,
                'safe': is_safe,
                'reason': 'ok' if is_safe else f'usage_{percent:.1f}%_exceeds_limit_{self.max_memory_percent}%'
            }
        except Exception as e:
            logging.error(f"Memory check failed: {e}")
            return {'safe': True, 'reason': 'check_failed'}

    def can_allocate(self, size_gb: float) -> tuple[bool, str]:
        """
        Check if we can safely allocate size_gb without OOM kill.

        Args:
            size_gb: Size to allocate in GB

        Returns:
            (can_allocate: bool, reason: str)
        """
        status = self.check_memory()

        if not status.get('safe'):
            return False, f"Already at {status['percent']:.1f}% memory usage"

        if 'percent' not in status:
            # Monitoring disabled, allow allocation
            return True, "monitoring_disabled"

        current_gb = status['current_gb']
        total_gb = status['total_gb']

        projected_gb = current_gb + size_gb
        projected_percent = (projected_gb / total_gb) * 100

        if projected_percent > self.max_memory_percent:
            return False, f"Would reach {projected_percent:.1f}% (limit: {self.max_memory_percent}%)"

        if projected_percent > 75:
            logging.warning(f"⚠️  High projected memory: {projected_percent:.1f}%")

        return True, f"safe_{projected_percent:.1f}%"

    def emergency_cleanup(self):
        """Force aggressive garbage collection"""
        import gc

        before = self.check_memory()

        logging.warning("🚨 EMERGENCY CLEANUP: Forcing aggressive GC...")

        # Run GC 5 times
        collected_total = 0
        for i in range(5):
            collected = gc.collect()
            collected_total += collected
            logging.info(f"   GC cycle {i+1}: collected {collected} objects")

        after = self.check_memory()

        if 'current_gb' in before and 'current_gb' in after:
            freed = before['current_gb'] - after['current_gb']
            logging.warning(f"🚨 Emergency cleanup freed: {freed:.2f}GB")
            logging.warning(f"   Before: {before['current_gb']:.2f}GB ({before['percent']:.1f}%)")
            logging.warning(f"   After:  {after['current_gb']:.2f}GB ({after['percent']:.1f}%)")

        return after

    def get_recommendations(self, needed_gb: float) -> list:
        """Get recommendations for reducing memory usage"""
        status = self.check_memory()
        recommendations = []

        current_percent = status.get('percent', 0)

        if current_percent > 70:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Enable aggressive memory optimizations',
                'config': 'GANGSHEET_MEMMAP_THRESHOLD_GB=0.2, GANGSHEET_CACHE_LIMIT=2'
            })

        if current_percent > 60:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Process fewer orders per batch',
                'config': 'Select fewer orders (10-15 instead of 30+)'
            })

        if needed_gb > 2.0:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Enable dynamic gang sheet sizing',
                'config': 'GANGSHEET_DYNAMIC_SIZING=true'
            })

        if current_percent > 50:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Upgrade Railway plan',
                'config': 'Hobby plan ($5/mo) has 8GB, Pro ($20/mo) has 32GB'
            })

        return recommendations


def get_max_safe_batch_size(item_count: int, avg_item_memory_mb: float = 50) -> int:
    """
    Calculate maximum safe batch size based on available memory.

    Args:
        item_count: Total items to process
        avg_item_memory_mb: Average memory per item in MB

    Returns:
        Recommended batch size
    """
    guard = MemoryGuard()
    status = guard.check_memory()

    if not status.get('safe') or 'available_gb' not in status:
        # Conservative default
        return min(15, item_count)

    available_mb = status['available_gb'] * 1024

    # Use only 60% of available memory for safety
    usable_mb = available_mb * 0.6

    max_items = int(usable_mb / avg_item_memory_mb)

    # Cap at reasonable limits
    max_items = min(max_items, 30)  # Don't exceed 30 items per batch
    max_items = max(max_items, 5)   # Always allow at least 5 items

    batch_size = min(max_items, item_count)

    logging.info(f"📊 Calculated safe batch size: {batch_size} items (out of {item_count} total)")
    logging.info(f"   Available memory: {available_mb:.0f}MB, Using: {usable_mb:.0f}MB (60%)")

    return batch_size


def log_memory_warning(current_percent: float):
    """Log appropriate warning based on memory usage"""

    if current_percent > 90:
        logging.error(f"🔥 CRITICAL: {current_percent:.1f}% memory - OOM KILL IMMINENT!")
        logging.error(f"🔥 Railway will kill this process at ~95%")
        logging.error(f"🔥 STOP PROCESSING IMMEDIATELY")
    elif current_percent > 85:
        logging.error(f"❌ DANGER: {current_percent:.1f}% memory - approaching OOM kill threshold")
        logging.error(f"❌ Reduce batch size or enable aggressive optimizations")
    elif current_percent > 75:
        logging.warning(f"⚠️  HIGH: {current_percent:.1f}% memory usage")
        logging.warning(f"⚠️  Consider reducing batch size")
    elif current_percent > 60:
        logging.info(f"📊 Moderate memory usage: {current_percent:.1f}%")


# Global memory guard instance
_memory_guard = None

def get_memory_guard() -> MemoryGuard:
    """Get or create global memory guard instance"""
    global _memory_guard
    if _memory_guard is None:
        _memory_guard = MemoryGuard(max_memory_percent=85.0)
    return _memory_guard
