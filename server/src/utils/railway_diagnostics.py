"""
Railway Container Diagnostics

Run this to understand the memory environment in Railway
"""

import os
import logging

logger = logging.getLogger(__name__)


def log_railway_environment():
    """Log Railway container environment for debugging"""

    logger.info("="*70)
    logger.info("🚂 RAILWAY CONTAINER DIAGNOSTICS")
    logger.info("="*70)

    # Check if running in container
    in_container = os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')
    logger.info(f"Running in container: {in_container}")

    # Check cgroup version and limits
    logger.info("")
    logger.info("📊 CGROUP MEMORY LIMITS:")

    # cgroup v1
    if os.path.exists('/sys/fs/cgroup/memory/memory.limit_in_bytes'):
        try:
            with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
                limit = int(f.read().strip())
            with open('/sys/fs/cgroup/memory/memory.usage_in_bytes', 'r') as f:
                usage = int(f.read().strip())

            limit_gb = limit / (1024**3)
            usage_gb = usage / (1024**3)

            logger.info(f"   cgroup v1 detected: ✅")
            logger.info(f"   Container memory limit: {limit_gb:.2f}GB")
            logger.info(f"   Current usage: {usage_gb:.2f}GB ({(usage_gb/limit_gb)*100:.1f}%)")

            if limit_gb > 100:
                logger.warning(f"   ⚠️  Limit seems unlimited ({limit_gb:.0f}GB), using Railway default")
        except Exception as e:
            logger.warning(f"   cgroup v1 error: {e}")

    # cgroup v2
    elif os.path.exists('/sys/fs/cgroup/memory.max'):
        try:
            with open('/sys/fs/cgroup/memory.max', 'r') as f:
                limit = f.read().strip()
            with open('/sys/fs/cgroup/memory.current', 'r') as f:
                usage = int(f.read().strip())

            if limit == 'max':
                logger.info(f"   cgroup v2 detected: ✅")
                logger.info(f"   Container memory limit: unlimited (using Railway default)")
            else:
                limit_bytes = int(limit)
                limit_gb = limit_bytes / (1024**3)
                usage_gb = usage / (1024**3)

                logger.info(f"   cgroup v2 detected: ✅")
                logger.info(f"   Container memory limit: {limit_gb:.2f}GB")
                logger.info(f"   Current usage: {usage_gb:.2f}GB ({(usage_gb/limit_gb)*100:.1f}%)")
        except Exception as e:
            logger.warning(f"   cgroup v2 error: {e}")
    else:
        logger.warning(f"   No cgroup memory limits found")
        logger.warning(f"   Will use psutil (may show host memory, not container)")

    # Check psutil
    logger.info("")
    logger.info("📊 PSUTIL DETECTION:")
    try:
        import psutil
        vm = psutil.virtual_memory()
        logger.info(f"   psutil available: ✅")
        logger.info(f"   Total memory (may be host): {vm.total / (1024**3):.2f}GB")
        logger.info(f"   Available: {vm.available / (1024**3):.2f}GB")
        logger.info(f"   Used: {(vm.total - vm.available) / (1024**3):.2f}GB")

        if vm.total / (1024**3) > 100:
            logger.warning(f"   ⚠️  Showing host memory (container memory limits not detected by psutil)")
    except ImportError:
        logger.warning(f"   psutil not available: ❌")
    except Exception as e:
        logger.warning(f"   psutil error: {e}")

    # Check Railway environment variables
    logger.info("")
    logger.info("🌍 RAILWAY ENVIRONMENT:")
    railway_vars = {
        'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT'),
        'RAILWAY_SERVICE_NAME': os.getenv('RAILWAY_SERVICE_NAME'),
        'RAILWAY_DEPLOYMENT_ID': os.getenv('RAILWAY_DEPLOYMENT_ID'),
    }
    for key, value in railway_vars.items():
        if value:
            logger.info(f"   {key}: {value}")

    # Memory files check
    logger.info("")
    logger.info("📁 MEMORY INFO FILES:")
    memory_files = [
        '/proc/meminfo',
        '/sys/fs/cgroup/memory/memory.limit_in_bytes',
        '/sys/fs/cgroup/memory/memory.usage_in_bytes',
        '/sys/fs/cgroup/memory.max',
        '/sys/fs/cgroup/memory.current',
    ]
    for filepath in memory_files:
        exists = "✅" if os.path.exists(filepath) else "❌"
        logger.info(f"   {exists} {filepath}")

    # /proc/meminfo
    if os.path.exists('/proc/meminfo'):
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()[:3]  # First 3 lines
            logger.info("")
            logger.info("📄 /proc/meminfo (first 3 lines):")
            for line in lines:
                logger.info(f"   {line.strip()}")
        except:
            pass

    logger.info("="*70)


def check_memory_monitoring_works():
    """Test if memory monitoring is working"""
    from .railway_memory_optimizer import get_railway_memory_monitor

    logger.info("")
    logger.info("🧪 TESTING MEMORY MONITOR:")

    monitor = get_railway_memory_monitor()
    stats = monitor.get_memory_stats()

    if stats:
        source = stats.get('source', 'unknown')
        logger.info(f"   ✅ Memory monitoring working")
        logger.info(f"   Detection method: {source}")
        logger.info(f"   Current: {stats['current_gb']:.2f}GB / {stats['total_gb']:.2f}GB")
        logger.info(f"   Percent: {stats['percent']:.1f}%")

        if source.startswith('cgroup'):
            logger.info(f"   ✅ Using container limits (ACCURATE)")
        else:
            logger.warning(f"   ⚠️  Using psutil fallback (MAY BE INACCURATE)")
    else:
        logger.error(f"   ❌ Memory monitoring NOT working")
        logger.error(f"   Cannot detect memory - monitoring disabled")

    logger.info("="*70)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    log_railway_environment()
    check_memory_monitoring_works()
