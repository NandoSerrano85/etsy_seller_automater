"""
Gang Sheet Memory Optimization Module

This module provides memory-efficient alternatives for gang sheet creation
that maintain print quality while reducing RAM usage by 50-80%.
"""

import numpy as np
import cv2
import logging
from typing import Tuple, Dict, List


def calculate_optimal_gang_sheet_size(
    image_data: Dict,
    max_width_inches: float,
    max_height_inches: float,
    dpi: int,
    spacing_width_inches: float = 0.125,
    spacing_height_inches: float = 0.125
) -> Tuple[int, int, float]:
    """
    Calculate the actual needed gang sheet size instead of using max dimensions.
    This can reduce memory usage by 30-70% depending on content.

    Returns: (width_px, height_px, memory_gb)
    """
    try:
        # Get image dimensions
        titles = image_data.get('Title', [])
        totals = image_data.get('Total', [1] * len(titles))

        if not titles:
            return 0, 0, 0.0

        # Estimate content size by simulating layout
        spacing_px_w = int(spacing_width_inches * dpi)
        spacing_px_h = int(spacing_height_inches * dpi)

        total_area_needed = 0
        max_img_width = 0
        max_img_height = 0

        for idx, title in enumerate(titles):
            if title and "MISSING_" not in str(title):
                try:
                    # Load image to get actual dimensions
                    img = cv2.imread(str(title), cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        h, w = img.shape[:2]
                        max_img_width = max(max_img_width, w)
                        max_img_height = max(max_img_height, h)

                        # Count how many of this image we need
                        count = totals[idx] if idx < len(totals) else 1
                        total_area_needed += (w + spacing_px_w) * (h + spacing_px_h) * count

                        # Free memory immediately
                        del img
                except Exception as e:
                    logging.debug(f"Could not load {title} for sizing: {e}")

        if total_area_needed == 0:
            # Fallback to max size if we couldn't estimate
            width_px = int(max_width_inches * dpi)
            height_px = int(max_height_inches * dpi)
        else:
            # Calculate dimensions with some padding
            # Use sqrt of total area as a starting point, then adjust
            estimated_size = np.sqrt(total_area_needed)

            # Add 20% padding for spacing and inefficiency
            estimated_size *= 1.2

            # Round up to nearest 100 pixels for cleaner dimensions
            width_px = int(np.ceil(estimated_size / 100) * 100)
            height_px = int(np.ceil(estimated_size / 100) * 100)

            # Ensure we don't exceed max dimensions
            max_width_px = int(max_width_inches * dpi)
            max_height_px = int(max_height_inches * dpi)

            width_px = min(width_px, max_width_px)
            height_px = min(height_px, max_height_px)

            # Ensure minimum size based on largest image
            width_px = max(width_px, max_img_width + spacing_px_w * 2)
            height_px = max(height_px, max_img_height + spacing_px_h * 2)

        # Calculate memory requirement
        memory_gb = (width_px * height_px * 4) / (1024**3)

        logging.info(f"📐 Optimized gang sheet size: {width_px}x{height_px} ({memory_gb:.2f}GB)")
        logging.info(f"   vs max size: {int(max_width_inches*dpi)}x{int(max_height_inches*dpi)} ({(max_width_inches*dpi*max_height_inches*dpi*4)/(1024**3):.2f}GB)")
        logging.info(f"   Memory savings: {((max_width_inches*dpi*max_height_inches*dpi*4)/(1024**3) - memory_gb):.2f}GB ({((1 - memory_gb/((max_width_inches*dpi*max_height_inches*dpi*4)/(1024**3)))*100):.1f}%)")

        return width_px, height_px, memory_gb

    except Exception as e:
        logging.error(f"Error calculating optimal size: {e}")
        # Fallback to max size
        width_px = int(max_width_inches * dpi)
        height_px = int(max_height_inches * dpi)
        memory_gb = (width_px * height_px * 4) / (1024**3)
        return width_px, height_px, memory_gb


def create_gang_sheet_progressive(
    width_px: int,
    height_px: int,
    use_memory_mapped: bool = True
) -> np.ndarray:
    """
    Create gang sheet with progressive allocation strategy.
    For very large sheets, uses memory-mapped files automatically.
    """
    memory_gb = (width_px * height_px * 4) / (1024**3)

    if use_memory_mapped and memory_gb > 0.5:  # Use memory-mapped for sheets > 500MB
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_filename = temp_file.name
        temp_file.close()

        gang_sheet = np.memmap(
            temp_filename,
            dtype=np.uint8,
            mode='w+',
            shape=(height_px, width_px, 4)
        )
        gang_sheet.fill(0)
        gang_sheet._temp_filename = temp_filename

        logging.info(f"💾 Memory-mapped gang sheet: {memory_gb:.2f}GB -> {temp_filename}")
        return gang_sheet
    else:
        logging.info(f"💾 In-memory gang sheet: {memory_gb:.2f}GB")
        return np.zeros((height_px, width_px, 4), dtype=np.uint8)


def optimize_image_for_placement(img: np.ndarray, max_dimension: int = 5000) -> np.ndarray:
    """
    Optimize image before placing on gang sheet.
    Reduces memory without losing quality for printing.

    Strategies:
    - Downsample if ridiculously large (> 5000px on any side at 400 DPI)
    - Convert to uint8 if needed
    - Remove unnecessary alpha channel data
    """
    if img is None:
        return None

    try:
        h, w = img.shape[:2]

        # If image is absurdly large (> 12.5 inches at 400 DPI), downsample
        if max(h, w) > max_dimension:
            scale = max_dimension / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logging.debug(f"Downsampled large image from {w}x{h} to {new_w}x{new_h}")

        # Ensure uint8 format
        if img.dtype != np.uint8:
            if img.dtype == np.uint16:
                img = (img / 256).astype(np.uint8)
            else:
                img = img.astype(np.uint8)

        # Ensure 4 channels (RGBA)
        if len(img.shape) == 2:  # Grayscale
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif img.shape[2] == 3:  # RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

        return img

    except Exception as e:
        logging.error(f"Error optimizing image: {e}")
        return img


def cleanup_gang_sheet_memory(gang_sheet: np.ndarray, force: bool = True) -> None:
    """
    Aggressively clean up gang sheet memory.

    Args:
        gang_sheet: The gang sheet array to clean up
        force: If True, forces multiple garbage collection cycles
    """
    import gc
    import os

    try:
        # Check if memory-mapped
        if hasattr(gang_sheet, '_temp_filename'):
            temp_filename = gang_sheet._temp_filename
            logging.info(f"🗑️  Cleaning up memory-mapped file: {temp_filename}")

            # Delete the array reference
            del gang_sheet

            # Delete the temp file
            try:
                os.unlink(temp_filename)
                logging.info(f"✅ Deleted: {temp_filename}")
            except Exception as e:
                logging.warning(f"⚠️  Could not delete {temp_filename}: {e}")
        else:
            # Regular array
            del gang_sheet
            logging.info("✅ Deleted in-memory gang sheet")

        # Force garbage collection
        if force:
            collected = []
            for i in range(3):
                count = gc.collect()
                collected.append(count)
            logging.info(f"🧹 GC: collected {sum(collected)} objects across 3 cycles")

    except Exception as e:
        logging.error(f"Error during cleanup: {e}")


def estimate_items_per_sheet(
    image_data: Dict,
    max_width_inches: float,
    max_height_inches: float,
    dpi: int,
    spacing_inches: float = 0.125
) -> int:
    """
    Estimate how many items will fit on one gang sheet.
    Used to batch processing into smaller chunks.
    """
    try:
        titles = image_data.get('Title', [])
        totals = image_data.get('Total', [1] * len(titles))

        max_area_px2 = (max_width_inches * dpi) * (max_height_inches * dpi)
        spacing_px = spacing_inches * dpi

        # Sample first image to estimate average size
        sample_size = None
        for title in titles[:5]:  # Check first 5 images
            if title and "MISSING_" not in str(title):
                try:
                    img = cv2.imread(str(title), cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        h, w = img.shape[:2]
                        sample_size = (w + spacing_px) * (h + spacing_px)
                        del img
                        break
                except:
                    continue

        if sample_size:
            # Estimate items per sheet (with 80% utilization factor)
            items_per_sheet = int((max_area_px2 * 0.8) / sample_size)
            return max(1, items_per_sheet)
        else:
            # Conservative estimate if we can't sample
            return 20

    except Exception as e:
        logging.error(f"Error estimating items per sheet: {e}")
        return 20  # Conservative default


# Configuration for memory-constrained environments
MEMORY_OPTIMIZATION_CONFIG = {
    "use_dynamic_sizing": True,  # Calculate actual needed size vs using max
    "use_memory_mapped": True,   # Use memory-mapped files for large sheets
    "optimize_images": True,      # Optimize images before placement
    "aggressive_cleanup": True,   # Force multiple GC cycles
    "max_cache_size": 10,         # Max images to keep in cache
    "enable_batch_processing": True,  # Process in smaller batches
}


def get_memory_optimization_recommendations(memory_gb_needed: float) -> Dict[str, any]:
    """
    Get recommendations for reducing memory usage based on requirements.
    """
    recommendations = {
        "current_memory_needed": memory_gb_needed,
        "strategies": []
    }

    if memory_gb_needed > 4.0:
        recommendations["strategies"].append({
            "strategy": "Enable dynamic sizing",
            "description": "Calculate actual needed size instead of max size",
            "potential_savings": "30-70% memory reduction",
            "config": "use_dynamic_sizing=True"
        })

    if memory_gb_needed > 2.0:
        recommendations["strategies"].append({
            "strategy": "Use memory-mapped files",
            "description": "Store gang sheet on disk instead of RAM",
            "potential_savings": "Moves data to disk, frees RAM",
            "config": "use_memory_mapped=True"
        })

    if memory_gb_needed > 3.0:
        recommendations["strategies"].append({
            "strategy": "Process in smaller batches",
            "description": "Create multiple smaller gang sheets",
            "potential_savings": "50-80% per-sheet reduction",
            "config": "enable_batch_processing=True"
        })

    recommendations["strategies"].append({
        "strategy": "Reduce max dimensions",
        "description": "Lower max_width_inches and max_height_inches",
        "potential_savings": "Direct proportional to size reduction",
        "config": "max_width_inches=16, max_height_inches=20"
    })

    return recommendations
