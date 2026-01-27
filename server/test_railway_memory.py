#!/usr/bin/env python3
"""
Test Railway Memory Detection

Run this script in Railway to diagnose memory detection issues:
  python server/test_railway_memory.py

Or add as an endpoint in your API to call remotely.
"""

import sys
import logging
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚂 RAILWAY MEMORY DETECTION TEST")
    print("="*70 + "\n")

    # Run diagnostics
    from src.utils.railway_diagnostics import log_railway_environment, check_memory_monitoring_works

    log_railway_environment()
    check_memory_monitoring_works()

    print("\n" + "="*70)
    print("✅ Diagnostic complete!")
    print("="*70 + "\n")

    # Additional check: Can we pause?
    from src.utils.railway_memory_optimizer import get_railway_memory_monitor

    monitor = get_railway_memory_monitor()
    stats = monitor.get_memory_stats()

    if stats:
        print(f"Current memory: {stats['current_gb']:.2f}GB / {stats['total_gb']:.2f}GB ({stats['percent']:.1f}%)")
        print(f"Detection: {stats.get('source', 'unknown')}")

        # Test pause threshold
        from src.utils.railway_memory_optimizer import MEMORY_PAUSE_THRESHOLD
        pause_at_gb = MEMORY_PAUSE_THRESHOLD * stats.get('effective_gb', stats['total_gb'])

        print(f"\nPause configuration:")
        print(f"  Pause threshold: {MEMORY_PAUSE_THRESHOLD * 100:.1f}%")
        print(f"  Will pause at: {pause_at_gb:.2f}GB")
        print(f"  Current status: {'🟢 OK' if stats['current_gb'] < pause_at_gb else '🔴 WOULD PAUSE NOW'}")
    else:
        print("❌ ERROR: Cannot detect memory")
        print("Memory monitoring will NOT work - OOM protection disabled!")

    print("")
