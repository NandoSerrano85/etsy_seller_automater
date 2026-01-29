"""
Memory-Aware Batch Splitter for Railway

Automatically splits large order batches into smaller sub-batches
to prevent OOM in Railway's 8GB containers.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MemoryAwareBatchSplitter:
    """Split order batches based on memory constraints"""

    def __init__(self, max_items_per_batch=15, max_memory_per_batch_gb=2.5):
        """
        Args:
            max_items_per_batch: Maximum number of unique designs per batch
            max_memory_per_batch_gb: Target max memory for gang sheet (default 2.5GB)
        """
        self.max_items_per_batch = max_items_per_batch
        self.max_memory_per_batch_gb = max_memory_per_batch_gb

    def should_split_batch(self, order_items_data: Dict, dpi: int, max_height_inches: float) -> bool:
        """
        Check if batch should be split based on estimated memory usage

        Args:
            order_items_data: Dict with 'Title', 'Size', etc.
            dpi: Gang sheet DPI
            max_height_inches: Gang sheet max height

        Returns:
            True if batch should be split
        """
        total_items = len(order_items_data.get('Title', []))
        unique_items = len(set(order_items_data.get('Title', [])))

        # Estimate gang sheet memory (very rough)
        # Assume designs fill ~70% of gang sheet height on average
        estimated_height_inches = min(max_height_inches * 0.7, 100)  # Cap estimate at 100"
        estimated_width_inches = 16  # Typical width

        estimated_memory_gb = (estimated_width_inches * dpi * estimated_height_inches * dpi * 4) / (1024**3)

        logger.info(f"📊 Batch analysis:")
        logger.info(f"   Total items: {total_items}")
        logger.info(f"   Unique designs: {unique_items}")
        logger.info(f"   Estimated gang sheet: {estimated_memory_gb:.2f}GB")

        # Split if:
        # 1. Too many unique items (memory for loading designs)
        # 2. Estimated gang sheet too large
        should_split = (
            unique_items > self.max_items_per_batch or
            estimated_memory_gb > self.max_memory_per_batch_gb
        )

        if should_split:
            logger.warning(f"⚠️  Batch too large, will split:")
            if unique_items > self.max_items_per_batch:
                logger.warning(f"   - {unique_items} unique items > {self.max_items_per_batch} max")
            if estimated_memory_gb > self.max_memory_per_batch_gb:
                logger.warning(f"   - {estimated_memory_gb:.2f}GB estimated > {self.max_memory_per_batch_gb:.2f}GB max")

        return should_split

    def split_order_items_data(self, order_items_data: Dict, max_items_per_split: int = 15) -> List[Dict]:
        """
        Split order_items_data into smaller batches

        Args:
            order_items_data: Dict with 'Title', 'Size', 'Total', etc.
            max_items_per_split: Max items per sub-batch

        Returns:
            List of order_items_data dicts (sub-batches)
        """
        total_items = len(order_items_data.get('Title', []))

        if total_items <= max_items_per_split:
            logger.info(f"✅ Batch size OK: {total_items} items")
            return [order_items_data]

        # Split into sub-batches
        num_splits = (total_items + max_items_per_split - 1) // max_items_per_split
        logger.info(f"📦 Splitting {total_items} items into {num_splits} sub-batches of ~{max_items_per_split} items")

        sub_batches = []
        keys = list(order_items_data.keys())

        for split_num in range(num_splits):
            start_idx = split_num * max_items_per_split
            end_idx = min(start_idx + max_items_per_split, total_items)

            sub_batch = {}
            for key in keys:
                if isinstance(order_items_data[key], (list, tuple)):
                    sub_batch[key] = order_items_data[key][start_idx:end_idx]
                else:
                    sub_batch[key] = order_items_data[key]

            sub_batches.append(sub_batch)
            logger.info(f"   Sub-batch {split_num + 1}: {end_idx - start_idx} items")

        return sub_batches


def process_with_memory_aware_splitting(
    order_items_data: Dict,
    create_gang_sheets_func,
    **gang_sheet_kwargs
) -> Dict[str, Any]:
    """
    Wrapper that automatically splits batches if needed

    Args:
        order_items_data: Order items to process
        create_gang_sheets_func: Function to create gang sheets
        **gang_sheet_kwargs: Arguments to pass to create_gang_sheets

    Returns:
        Combined result dict
    """
    splitter = MemoryAwareBatchSplitter()

    # Check if we should split
    dpi = gang_sheet_kwargs.get('dpi', 400)
    max_height = gang_sheet_kwargs.get('max_height_inches', 215)

    if not splitter.should_split_batch(order_items_data, dpi, max_height):
        # Process normally
        return create_gang_sheets_func(
            image_data=order_items_data,
            **gang_sheet_kwargs
        )

    # Split and process each sub-batch
    logger.info(f"")
    logger.info(f"{'='*70}")
    logger.info(f"🔄 MEMORY-AWARE BATCH SPLITTING ACTIVE")
    logger.info(f"{'='*70}")

    total_items = len(order_items_data.get('Title', []))
    max_items = splitter.max_items_per_batch

    sub_batches = splitter.split_order_items_data(order_items_data, max_items)

    all_results = []
    total_sheets = 0

    for batch_num, sub_batch in enumerate(sub_batches, 1):
        logger.info(f"")
        logger.info(f"{'='*70}")
        logger.info(f"📦 PROCESSING SUB-BATCH {batch_num}/{len(sub_batches)}")
        logger.info(f"{'='*70}")
        logger.info(f"Items in this sub-batch: {len(sub_batch.get('Title', []))}")

        # Process sub-batch
        result = create_gang_sheets_func(
            image_data=sub_batch,
            **gang_sheet_kwargs
        )

        if result and result.get('success'):
            sheets = result.get('sheets_created', 0)
            total_sheets += sheets
            all_results.append(result)
            logger.info(f"✅ Sub-batch {batch_num} complete: {sheets} gang sheets created")
        else:
            error = result.get('error', 'Unknown error') if result else 'No result'
            logger.error(f"❌ Sub-batch {batch_num} failed: {error}")
            return {
                'success': False,
                'error': f'Sub-batch {batch_num} failed: {error}',
                'completed_batches': batch_num - 1,
                'total_batches': len(sub_batches)
            }

        # Force cleanup between batches
        logger.info(f"🧹 Cleanup between sub-batches...")
        import gc
        for _ in range(3):
            gc.collect()

        try:
            import ctypes
            libc = ctypes.CDLL('libc.so.6')
            libc.malloc_trim(0)
        except:
            pass

    logger.info(f"")
    logger.info(f"{'='*70}")
    logger.info(f"✅ ALL SUB-BATCHES COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"Total sub-batches processed: {len(sub_batches)}")
    logger.info(f"Total gang sheets created: {total_sheets}")
    logger.info(f"Original items: {total_items}")
    logger.info(f"{'='*70}")

    return {
        'success': True,
        'sheets_created': total_sheets,
        'sub_batches_processed': len(sub_batches),
        'total_items': total_items
    }
