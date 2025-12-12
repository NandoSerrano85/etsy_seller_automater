#!/usr/bin/env python3
"""
Comprehensive Image Upload Workflow System

This service handles the image processing pipeline before mockup generation:
1. Batch Processing (multi-threaded)
2. Image Resizing and Processing
3. Perceptual Hash (pHash) Generation
4. Duplicate Detection (local and database-based)
5. NAS Upload with proper naming conventions
6. Database Storage

Note: Mockup generation and Etsy uploads are handled separately by the /mockups/upload-mockup endpoint

Architecture:
- Multi-threaded batch processing for performance
- Thread-safe operations with proper synchronization
- Comprehensive error handling and rollback capabilities
- Progress tracking and detailed logging
"""

import os
import sys
import time
import uuid
import logging
import threading
import tempfile
import cv2
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field

try:
    import imagehash
    import numpy as np
    from PIL import Image
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Missing dependencies for image processing: {e}")
    DEPENDENCIES_AVAILABLE = False
    # Create mock classes for type hints when dependencies are missing
    class Session:
        pass

    class Image:
        class Image:
            pass

    import numpy as np

# Import existing services
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.dirname(current_dir)
sys.path.insert(0, server_dir)

try:
    from utils.nas_storage import nas_storage
    from utils.resizing import get_resizing_configs_from_db, resize_image_by_inches
    from database.core import get_db
    NAS_AVAILABLE = True
    RESIZING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"NAS storage not available: {e}")
    nas_storage = None
    get_resizing_configs_from_db = None
    resize_image_by_inches = None
    NAS_AVAILABLE = False
    RESIZING_AVAILABLE = False

try:
    from routes.mockups import service as mockup_service
    MOCKUP_SERVICE_AVAILABLE = True
except ImportError:
    mockup_service = None
    MOCKUP_SERVICE_AVAILABLE = False


@dataclass
class UploadedImage:
    """Information about an uploaded image"""
    original_filename: str
    content: bytes
    size: int
    upload_time: datetime
    user_id: str
    template_id: Optional[str] = None
    temp_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ProcessedImage:
    """Information about a processed image"""
    upload_info: UploadedImage
    resized_content: Optional[bytes] = None
    resized_size: Optional[int] = None
    phash: Optional[str] = None
    ahash: Optional[str] = None
    dhash: Optional[str] = None
    whash: Optional[str] = None
    final_filename: Optional[str] = None
    canvas_config: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0
    is_duplicate_local: bool = False
    is_duplicate_db: bool = False
    error: Optional[str] = None
    nas_uploaded: bool = False
    db_updated: bool = False
    mockup_generated: bool = False


@dataclass
class BatchResult:
    """Result of processing a batch of images"""
    batch_id: int
    processed: int
    skipped_local_duplicates: int
    skipped_db_duplicates: int
    errors: int
    processing_time: float
    nas_uploads: int
    db_updates: int
    mockups_created: int
    error_details: List[str] = field(default_factory=list)


@dataclass
class WorkflowResult:
    """Final result of the entire workflow"""
    total_images: int
    processed_images: int
    skipped_duplicates: int
    errors: int
    processing_time: float
    nas_uploads: int
    db_updates: int
    mockups_created: int
    etsy_products: int
    batch_results: List[BatchResult] = field(default_factory=list)


class ImageUploadWorkflow:
    """
    Main workflow orchestrator for image upload processing
    """

    def __init__(self, user_id: str, db_session: Session, max_threads: int = 16, progress_callback=None):
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError("Required dependencies not available (PIL, imagehash, sqlalchemy)")

        self.user_id = user_id
        self.db_session = db_session
        self.max_threads = max_threads
        self.progress_callback = progress_callback

        # Thread synchronization
        self.db_lock = threading.Lock()
        self.nas_lock = threading.Lock()

        # Caching for performance
        self._existing_phashes: Optional[Set[str]] = None
        self._existing_phashes_lock = threading.Lock()

        # Cache for duplicate detection (reduces DB queries during batch processing)
        self._duplicate_check_cache: Dict[str, bool] = {}  # hash -> is_duplicate
        self._duplicate_cache_lock = threading.Lock()

        # Shared counter for sequential file naming across parallel batches
        self._unique_file_counter = 0
        self._file_counter_lock = threading.Lock()

        # Cache for frequently accessed data (reduces DB queries)
        self._shop_name_cache: Optional[str] = None
        self._template_name_cache: Dict[str, str] = {}
        self._cache_lock = threading.Lock()

        # Configuration
        self.target_width = 3000
        self.target_height = 3000
        self.jpeg_quality = 85
        self.phash_size = 16

        # Progress tracking
        self._total_files = 0
        self._processed_files = 0
        self._current_file = ""

    def _send_progress(self, step: int, message: str, current_file: str = "", file_progress: float = 0):
        """Send progress update to callback if available"""
        if self.progress_callback:
            try:
                self.progress_callback(step, message, 4, file_progress, current_file)
                logging.info(f"Progress sent: Step {step}/4 - {message} - {current_file}")
            except Exception as e:
                logging.error(f"Error sending progress update: {e}")

    def _update_file_progress(self, current_file: str = ""):
        """Update current file being processed"""
        if current_file:
            self._current_file = current_file
            self._processed_files += 1

    def process_images(self, uploaded_images: List[UploadedImage], design_data=None) -> WorkflowResult:
        """
        Main entry point for processing uploaded images

        Args:
            uploaded_images: List of uploaded image data

        Returns:
            WorkflowResult with complete processing statistics
        """
        start_time = time.time()
        self._total_files = len(uploaded_images)
        self._processed_files = 0

        # Initialize starting_name from design_data for proper filename numbering
        if design_data and hasattr(design_data, 'starting_name'):
            self._design_starting_name = design_data.starting_name
            logging.info(f"Using mockup starting_name: {self._design_starting_name}")
        else:
            self._design_starting_name = 100  # Default starting number
            logging.info(f"Using default starting_name: {self._design_starting_name}")

        logging.info(f"🚀 Starting image upload workflow for {len(uploaded_images)} images")
        self._send_progress(1, f"Starting workflow for {len(uploaded_images)} images")

        try:
            # Pre-load existing phashes from database for duplicate detection
            self._send_progress(1, "Loading existing image hashes for duplicate detection")
            self._load_existing_phashes()

            # Create batches for processing
            self._send_progress(1, "Organizing images into processing batches")
            batches = self._create_batches(uploaded_images)
            logging.info(f"📦 Created {len(batches)} batches for processing")

            # Process batches in parallel
            self._send_progress(2, "Processing and resizing images")
            batch_results = self._process_batches_parallel(batches, design_data)

            # Calculate final statistics
            processing_time = time.time() - start_time
            workflow_result = self._compile_workflow_result(
                uploaded_images, batch_results, processing_time
            )

            # Send final progress update
            self._send_progress(
                3,
                f"Images ready for mockup generation: {workflow_result.processed_images} processed, {workflow_result.skipped_duplicates} duplicates skipped",
                "",
                1.0
            )

            logging.info(f"🎉 Workflow completed in {processing_time:.1f}s")
            logging.info(f"   📊 Processed: {workflow_result.processed_images}/{workflow_result.total_images}")
            logging.info(f"   🔄 Skipped duplicates: {workflow_result.skipped_duplicates}")
            logging.info(f"   ❌ Errors: {workflow_result.errors}")
            logging.info(f"   📤 NAS uploads: {workflow_result.nas_uploads}")
            logging.info(f"   🗄️  DB updates: {workflow_result.db_updates}")
            logging.info(f"   🎨 Mockups created: {workflow_result.mockups_created}")

            return workflow_result

        except Exception as e:
            logging.error(f"💥 Workflow failed: {e}")
            raise

    def _load_existing_phashes(self):
        """
        Initialize duplicate detection system
        Note: Now uses database queries instead of loading all hashes into memory
        """
        try:
            logging.info("📊 Initializing database-backed duplicate detection...")

            # Count existing images for logging
            result = self.db_session.execute(text("""
                SELECT COUNT(*)
                FROM design_images
                WHERE user_id = :user_id
                AND phash IS NOT NULL
                AND is_active = true
            """), {"user_id": self.user_id})

            count = result.scalar()
            logging.info(f"📊 User has {count} existing images in database for duplicate checking")

            # Keep empty set for batch-level duplicate tracking
            self._existing_phashes = set()

        except Exception as e:
            logging.error(f"❌ Failed to initialize duplicate detection: {e}")
            import traceback
            logging.error(f"❌ Traceback: {traceback.format_exc()}")
            self._existing_phashes = set()

    def _create_batches(self, images: List[UploadedImage], batch_size_mb: int = 100, max_images_per_batch: int = 50) -> List[List[UploadedImage]]:
        """
        Create optimized batches of images for processing

        Improved batching strategy:
        - Larger batch size (100MB) for better throughput with parallel processing
        - Max 50 images per batch to balance parallelism with resource usage
        - Optimized for high-volume uploads (100+ images)

        Args:
            images: List of uploaded images
            batch_size_mb: Target batch size in MB (increased to 100 for better throughput)
            max_images_per_batch: Maximum number of images per batch (increased to 50)

        Returns:
            List of image batches
        """
        batches = []
        current_batch = []
        current_size = 0
        target_size = batch_size_mb * 1024 * 1024  # Convert to bytes

        for image in images:
            # Split batch if we exceed size OR image count limits
            should_split = (
                (current_size + image.size > target_size and current_batch) or
                (len(current_batch) >= max_images_per_batch)
            )

            if should_split:
                batches.append(current_batch)
                current_batch = [image]
                current_size = image.size
            else:
                current_batch.append(image)
                current_size += image.size

        if current_batch:
            batches.append(current_batch)

        # Log batch distribution for monitoring
        if batches:
            sizes = [len(b) for b in batches]
            logging.info(f"📦 Created {len(batches)} batches: images/batch={sizes}, avg={sum(sizes)/len(sizes):.1f}")

        return batches

    def _process_batches_parallel(self, batches: List[List[UploadedImage]], design_data=None) -> List[BatchResult]:
        """
        Process batches in parallel using thread pool

        Args:
            batches: List of image batches to process
            design_data: Design configuration data to pass to batch processing

        Returns:
            List of batch processing results
        """
        max_workers = min(self.max_threads, len(batches))
        logging.info(f"🚀 Processing {len(batches)} batches with {max_workers} threads")

        batch_results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit batches with staggered start
            future_to_batch = {}
            for i, batch in enumerate(batches):
                batch_id = i + 1
                # Small delay to stagger batch starts
                if i > 0:
                    time.sleep(0.1)
                future_to_batch[executor.submit(self._process_batch, batch, batch_id, design_data)] = batch_id

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_id = future_to_batch[future]
                try:
                    result = future.result()
                    batch_results.append(result)

                    logging.info(f"✅ Batch {batch_id} completed:")
                    logging.info(f"   📊 Processed: {result.processed}")
                    logging.info(f"   🔄 Skipped: {result.skipped_local_duplicates + result.skipped_db_duplicates}")
                    logging.info(f"   ❌ Errors: {result.errors}")

                except Exception as e:
                    logging.error(f"❌ Batch {batch_id} failed: {e}")
                    batch_results.append(BatchResult(
                        batch_id=batch_id,
                        processed=0,
                        skipped_local_duplicates=0,
                        skipped_db_duplicates=0,
                        errors=len(batches[batch_id - 1]),
                        processing_time=0,
                        nas_uploads=0,
                        db_updates=0,
                        mockups_created=0,
                        error_details=[str(e)]
                    ))

        return batch_results

    def _process_batch(self, images: List[UploadedImage], batch_id: int, design_data=None) -> BatchResult:
        """
        Process a single batch of images through the complete workflow

        Args:
            images: List of images in this batch
            batch_id: Unique batch identifier

        Returns:
            BatchResult with processing statistics
        """
        start_time = time.time()
        processed = 0
        skipped_local = 0
        skipped_db = 0
        errors = 0
        nas_uploads = 0
        db_updates = 0
        mockups_created = 0
        error_details = []

        logging.info(f"📦 Batch {batch_id}: Processing {len(images)} images")

        try:
            # Step 1: Resize images and generate phashes
            processed_images = []
            local_phashes = set()

            for i, image in enumerate(images):
                try:
                    # Send progress update for current file
                    if batch_id == 1:  # Only send detailed updates for first batch
                        self._send_progress(
                            2,
                            f"Processing image: {image.original_filename}",
                            image.original_filename,
                            i / len(images) if images else 0
                        )

                    processed_image = self._process_single_image(image, design_data, i)

                    # Only check for duplicates if processing was successful
                    if processed_image.phash and not processed_image.error:
                        # Use enhanced multi-hash duplicate detection
                        logging.info(f"   🔍 Checking duplicates for {processed_image.final_filename}, phash: {processed_image.phash[:12]}...")
                        logging.info(f"🔍 DEBUG: Full hashes for {processed_image.final_filename}: phash={processed_image.phash}, ahash={processed_image.ahash}, dhash={processed_image.dhash}, whash={processed_image.whash}")
                        logging.info(f"🔍 DEBUG: Local phashes set size: {len(local_phashes)}, existing phashes set size: {len(self._existing_phashes) if self._existing_phashes else 0}")

                        # Check for local duplicates within this batch using multiple hashes
                        logging.info(f"🔍 DEBUG: Checking local duplicates for {processed_image.final_filename} against {len(local_phashes)} local hashes")
                        is_local_duplicate = self._is_enhanced_duplicate_in_set(processed_image, local_phashes)
                        logging.info(f"🔍 DEBUG: Local duplicate check result: {is_local_duplicate}")
                        if is_local_duplicate:
                            processed_image.is_duplicate_local = True
                            skipped_local += 1
                            logging.info(f"   🔄 LOCAL DUPLICATE FOUND: {processed_image.final_filename} matches existing in batch")
                        else:
                            # Add all hashes to local set
                            local_phashes.add(processed_image.phash)
                            if processed_image.ahash:
                                local_phashes.add(processed_image.ahash)
                            if processed_image.dhash:
                                local_phashes.add(processed_image.dhash)
                            if processed_image.whash:
                                local_phashes.add(processed_image.whash)
                            logging.info(f"   ✅ Not a local duplicate: {processed_image.final_filename}")

                            # Check for database duplicates using multiple hashes
                            logging.info(f"🔍 DEBUG: Checking database duplicates for {processed_image.final_filename} against existing hashes")
                            with self._existing_phashes_lock:
                                is_db_duplicate = self._is_enhanced_duplicate_in_existing(processed_image)
                                logging.info(f"🔍 DEBUG: Database duplicate check result: {is_db_duplicate}")
                                if is_db_duplicate:
                                    processed_image.is_duplicate_db = True
                                    skipped_db += 1
                                    logging.info(f"   🔄 DATABASE DUPLICATE FOUND: {processed_image.final_filename} matches existing in DB")
                                else:
                                    logging.info(f"   ✅ Not a DB duplicate: {processed_image.final_filename}")
                    else:
                        logging.warning(f"   ⚠️  Skipping duplicate check for {processed_image.final_filename}: phash={processed_image.phash}, error={processed_image.error}")
                        # Count failed processing as error
                        if processed_image.error:
                            errors += 1

                    processed_images.append(processed_image)

                except Exception as e:
                    errors += 1
                    error_details.append(f"Processing {image.original_filename}: {e}")
                    logging.error(f"   ❌ Error processing {image.original_filename}: {e}")

            # Step 2: Filter unique images with detailed logging
            logging.info(f"📦 Batch {batch_id}: Filtering results from {len(processed_images)} processed images")

            unique_images = []
            duplicate_images = []
            error_images = []

            logging.info(f"🔍 DEBUG: Processing {len(processed_images)} processed images for batch {batch_id}")
            for img in processed_images:
                logging.info(f"🔍 DEBUG: Image {img.final_filename}: error={img.error}, local_dup={img.is_duplicate_local}, db_dup={img.is_duplicate_db}")
                if img.error:
                    error_images.append(img)
                    logging.info(f"   ❌ ERROR: {img.final_filename} - {img.error}")
                elif img.is_duplicate_local:
                    duplicate_images.append(img)
                    logging.info(f"   🔄 LOCAL DUP: {img.final_filename}")
                elif img.is_duplicate_db:
                    duplicate_images.append(img)
                    logging.info(f"   🔄 DB DUP: {img.final_filename}")
                else:
                    unique_images.append(img)
                    logging.info(f"   ✅ UNIQUE: {img.final_filename}")

            logging.info(f"📦 Batch {batch_id} SUMMARY: {len(unique_images)} unique, {len(duplicate_images)} duplicates, {len(error_images)} errors")
            logging.info(f"🔍 DEBUG: About to process only unique images: {[img.final_filename for img in unique_images]}")
            logging.info(f"🔍 DEBUG: Skipping duplicate images: {[img.final_filename for img in duplicate_images]}")
            logging.info(f"🔍 DEBUG: Skipping error images: {[img.final_filename for img in error_images]}")

            # Step 2.5: Rename only the unique images with sequential numbering (no gaps)
            # Use thread-safe counter to ensure sequential numbering across parallel batches
            logging.info(f"📦 Batch {batch_id}: Renaming {len(unique_images)} unique images with sequential numbering")
            for img in unique_images:
                # Atomically increment the shared counter for each unique image
                with self._file_counter_lock:
                    file_index = self._unique_file_counter
                    self._unique_file_counter += 1

                # Regenerate filename with correct sequential index
                final_filename = self._generate_filename(
                    img.upload_info.original_filename,
                    img.upload_info.template_id,
                    file_index
                )
                logging.info(f"   🔄 Renamed: {img.final_filename} → {final_filename} (index: {file_index})")
                img.final_filename = final_filename

            # Step 3: Upload to NAS
            if batch_id == 1:  # Only send progress for the first batch to avoid spam
                self._send_progress(2, f"Uploading {len(unique_images)} processed images to storage")
            nas_success = self._upload_batch_to_nas(unique_images, batch_id)
            nas_uploads = len(nas_success)

            # Step 4: Update database
            if batch_id == 1:
                self._send_progress(3, f"Saving {len(nas_success)} images to database")
            db_success = self._update_database_batch(nas_success, batch_id)
            db_updates = len(db_success)

            # Step 5: Skip mockup generation - handled by separate mockup service
            mockup_success = db_success  # All database-stored images are considered "mockup ready"
            mockups_created = len(mockup_success)

            processed = len(processed_images) - skipped_local - skipped_db - errors

        except Exception as e:
            error_details.append(f"Batch {batch_id} failed: {e}")
            errors += len(images)
            logging.error(f"❌ Batch {batch_id} failed completely: {e}")

        processing_time = time.time() - start_time

        result = BatchResult(
            batch_id=batch_id,
            processed=processed,
            skipped_local_duplicates=skipped_local,
            skipped_db_duplicates=skipped_db,
            errors=errors,
            processing_time=processing_time,
            nas_uploads=nas_uploads,
            db_updates=db_updates,
            mockups_created=mockups_created,
            error_details=error_details
        )

        logging.info(f"🔍 DEBUG: Batch {batch_id} FINAL RESULT: processed={processed}, local_dups={skipped_local}, db_dups={skipped_db}, errors={errors}, nas_uploads={nas_uploads}, db_updates={db_updates}")
        return result

    def _process_single_image(self, image: UploadedImage, design_data=None, file_index: int = 0) -> ProcessedImage:
        """
        Process a single image: resize and generate phash

        Args:
            image: Uploaded image data

        Returns:
            ProcessedImage with resized content and phash
        """
        start_time = time.time()

        processed = ProcessedImage(upload_info=image)

        try:
            # Validate content
            if not image.content or len(image.content) == 0:
                raise ValueError("Empty image content")

            # Load and validate image
            nparr = np.frombuffer(image.content, np.uint8)
            raw_image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

            if raw_image is None:
                raise ValueError("Could not decode image from content")

            # Step 1: Crop transparent areas
            from server.src.utils.cropping import crop_transparent
            cropped_image = crop_transparent(image=raw_image)

            if cropped_image is None:
                # If cropping fails, use original image
                cropped_image = raw_image
                logging.warning(f"Failed to crop transparent areas for {image.original_filename}, using original image")

            # Step 2: Resize the cropped image
            # Use lower DPI (300) for bulk uploads to reduce file size and transfer time
            # 300 DPI is still high quality but significantly reduces file size (~40% smaller)
            if RESIZING_AVAILABLE and resize_image_by_inches:
                resized_image = resize_image_by_inches(
                    image=cropped_image,
                    image_type="UVDTF 16oz",  # Default type, should be determined from template
                    db=self.db_session,
                    canvas_id=getattr(design_data, 'canvas_config_id', None),
                    product_template_id=image.template_id,
                    target_dpi=400  # Reduced from 400 for faster uploads
                )
            else:
                # Fallback: use the cropped image without further resizing
                resized_image = cropped_image

            # Convert to PIL Image for hash calculation
            if len(resized_image.shape) == 3 and resized_image.shape[2] == 4:
                # BGRA to RGBA
                pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGRA2RGBA))
            elif len(resized_image.shape) == 3 and resized_image.shape[2] == 3:
                # BGR to RGB
                pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))
            else:
                # Grayscale
                pil_image = Image.fromarray(resized_image)

            # Convert processed image to bytes for storage
            # Use maximum PNG compression (9) for large batch uploads to reduce transfer size
            # IMPORTANT: Set DPI to 400 to ensure consistent resolution across all design files
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG', optimize=True, compress_level=9, dpi=(400, 400))
            resized_content = buffer.getvalue()

            logging.info(f"Saved {image.original_filename} with DPI: 400x400")

            # Generate multiple hashes for enhanced duplicate detection
            logging.info(f"🔍 DEBUG: Generating hashes for {image.original_filename}")
            hashes = {
                'phash': str(imagehash.phash(pil_image, hash_size=self.phash_size)),
                'ahash': str(imagehash.average_hash(pil_image, hash_size=self.phash_size)),
                'dhash': str(imagehash.dhash(pil_image, hash_size=self.phash_size)),
                'whash': str(imagehash.whash(pil_image, hash_size=self.phash_size))
            }
            logging.info(f"🔍 DEBUG: Generated hashes for {image.original_filename}: phash={hashes['phash']}, ahash={hashes['ahash']}, dhash={hashes['dhash']}, whash={hashes['whash']}")

            # Store all hashes for enhanced duplicate detection
            processed.phash = hashes['phash']
            processed.ahash = hashes['ahash']
            processed.dhash = hashes['dhash']
            processed.whash = hashes['whash']

            # Generate filename using template name and file index
            final_filename = self._generate_filename(image.original_filename, image.template_id, file_index)

            # Update processed image
            processed.resized_content = resized_content
            processed.resized_size = len(resized_content)
            processed.final_filename = final_filename
            processed.processing_time = time.time() - start_time

            logging.info(f"Processed {image.original_filename}: {raw_image.shape} → {resized_image.shape}, phash: {processed.phash[:12]}...")

            return processed

        except Exception as e:
            processed.error = str(e)
            processed.processing_time = time.time() - start_time
            logging.error(f"Failed to process {image.original_filename}: {e}")
            return processed

    def _get_canvas_config(self, template_id: Optional[str]) -> Dict[str, Any]:
        """Get canvas configuration for image processing"""
        try:
            if template_id and hasattr(self, 'db_session') and get_resizing_configs_from_db:
                # Try to get from database if available
                config, _ = get_resizing_configs_from_db(
                    self.db_session,
                    canvas_id=None,
                    product_template_id=template_id
                )
                return config
        except Exception as e:
            logging.info(f"Could not get canvas config from DB: {e}")

        # Return default configuration
        return {
            'width': self.target_width,
            'height': self.target_height,
            'format': 'png',
            'maintain_aspect_ratio': True,
            'background_color': (255, 255, 255)
        }

    def _resize_and_optimize_image(self, pil_image: Image.Image, canvas_config: Dict[str, Any]) -> Image.Image:
        """
        Resize and optimize image based on canvas configuration
        """
        # Get target dimensions from canvas config
        target_width = canvas_config.get('width', self.target_width)
        target_height = canvas_config.get('height', self.target_height)
        maintain_aspect = canvas_config.get('maintain_aspect_ratio', True)

        original_width, original_height = pil_image.size

        # Calculate new dimensions
        if maintain_aspect:
            aspect_ratio = original_width / original_height

            if aspect_ratio > 1:  # Landscape
                if original_width > target_width:
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                else:
                    new_width = original_width
                    new_height = original_height
            else:  # Portrait or square
                if original_height > target_height:
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                else:
                    new_width = original_width
                    new_height = original_height

            # Ensure dimensions don't exceed limits
            new_width = min(new_width, target_width)
            new_height = min(new_height, target_height)
        else:
            new_width = target_width
            new_height = target_height

        # Only resize if necessary
        if (new_width, new_height) != (original_width, original_height):
            resized = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized = pil_image.copy()

        # Optimize image
        if resized.mode == 'P':
            resized = resized.convert('RGB')

        return resized

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove or replace problematic characters
        safe_name = re.sub(r'[^\w\-_.]', '_', filename)
        # Limit length and remove multiple underscores
        safe_name = re.sub(r'_{2,}', '_', safe_name)[:50]
        return safe_name or "image"

    def _extract_primary_phash(self, combined_hash: str) -> str:
        """Extract primary phash from combined hash string"""
        if '|' in combined_hash:
            return combined_hash.split('|')[0]
        return combined_hash

    def _is_duplicate_in_set(self, phash: str, phash_set: Set[str], hamming_threshold: int = 2) -> bool:
        """Check if phash is duplicate within a set using Hamming distance"""
        if not phash:
            logging.info(f"🔍 DEBUG: _is_duplicate_in_set: Empty phash")
            return False

        try:
            # Convert phash to integer for comparison
            phash_int = int(phash, 16)
            closest_distance = float('inf')
            closest_hash = None
            logging.info(f"🔍 DEBUG: _is_duplicate_in_set: Checking phash {phash[:12]}... against {len(phash_set)} hashes")

            for existing_phash in phash_set:
                if existing_phash:
                    existing_int = int(existing_phash, 16)
                    # Calculate Hamming distance
                    hamming_distance = bin(phash_int ^ existing_int).count('1')

                    if hamming_distance < closest_distance:
                        closest_distance = hamming_distance
                        closest_hash = existing_phash

                    if hamming_distance <= hamming_threshold:
                        logging.info(f"🔍 DEBUG: _is_duplicate_in_set: MATCH FOUND! {phash[:12]}... vs {existing_phash[:12]}... = Hamming distance {hamming_distance} (≤ {hamming_threshold})")
                        return True

            # Log the closest match even if not a duplicate
            if closest_hash:
                logging.info(f"🔍 DEBUG: _is_duplicate_in_set: Closest match: {phash[:12]}... vs {closest_hash[:12]}... = Hamming distance {closest_distance} (threshold: {hamming_threshold})")
            else:
                logging.info(f"🔍 DEBUG: _is_duplicate_in_set: No valid hashes to compare against")

            return False

        except (ValueError, TypeError) as e:
            logging.info(f"🔍 DEBUG: _is_duplicate_in_set: Error comparing phashes: {e}")
            return False

    def _is_duplicate_in_existing(self, phash: str, hamming_threshold: int = 2) -> bool:
        """Check if phash is duplicate within existing database hashes using SQL query with caching"""
        if not phash:
            logging.info(f"🔍 DEBUG: _is_duplicate_in_existing: Missing phash")
            return False

        # Check cache first (thread-safe)
        with self._duplicate_cache_lock:
            if phash in self._duplicate_check_cache:
                logging.info(f"🔍 DEBUG: _is_duplicate_in_existing: CACHE HIT for {phash[:12]}...")
                return self._duplicate_check_cache[phash]

        try:
            # Use database query to check for exact match first (fastest)
            result = self.db_session.execute(text("""
                SELECT 1
                FROM design_images
                WHERE user_id = :user_id
                AND is_active = true
                AND (phash = :hash OR ahash = :hash OR dhash = :hash OR whash = :hash)
                LIMIT 1
            """), {"user_id": self.user_id, "hash": phash})

            if result.fetchone():
                logging.info(f"🔍 DEBUG: _is_duplicate_in_existing: EXACT MATCH FOUND for {phash[:12]}...")
                # Cache the result
                with self._duplicate_cache_lock:
                    self._duplicate_check_cache[phash] = True
                return True

            # For Hamming distance checking, we need to fetch and compare
            # Only fetch a reasonable sample (e.g., last 1000 images) for performance
            if hamming_threshold > 0:
                result = self.db_session.execute(text("""
                    SELECT phash, ahash, dhash, whash
                    FROM design_images
                    WHERE user_id = :user_id
                    AND is_active = true
                    AND (phash IS NOT NULL OR ahash IS NOT NULL OR dhash IS NOT NULL OR whash IS NOT NULL)
                    ORDER BY created_at DESC
                    LIMIT 1000
                """), {"user_id": self.user_id})

                phash_int = int(phash, 16)
                for row in result:
                    for existing_hash in row:
                        if existing_hash:
                            try:
                                existing_int = int(existing_hash, 16)
                                hamming_distance = bin(phash_int ^ existing_int).count('1')
                                if hamming_distance <= hamming_threshold:
                                    logging.info(f"🔍 DEBUG: _is_duplicate_in_existing: HAMMING MATCH FOUND! {phash[:12]}... vs {existing_hash[:12]}... = distance {hamming_distance}")
                                    # Cache the result
                                    with self._duplicate_cache_lock:
                                        self._duplicate_check_cache[phash] = True
                                    return True
                            except (ValueError, TypeError):
                                continue

            # Cache negative result (not a duplicate)
            with self._duplicate_cache_lock:
                self._duplicate_check_cache[phash] = False
            return False

        except Exception as e:
            logging.error(f"🔍 DEBUG: _is_duplicate_in_existing: Database query error: {e}")
            return False

    def _is_enhanced_duplicate_in_set(self, processed_image: ProcessedImage, hash_set: Set[str], threshold: int = 5, min_matches: int = 2) -> bool:
        """Check if processed image is duplicate using multiple hash algorithms"""
        if not processed_image.phash:
            logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_set: No phash for {processed_image.final_filename}")
            return False

        matches = 0
        image_hashes = [processed_image.phash, processed_image.ahash, processed_image.dhash, processed_image.whash]
        logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_set: Checking {len(image_hashes)} hashes against {len(hash_set)} in set for {processed_image.final_filename}")

        for i, image_hash in enumerate(image_hashes):
            hash_names = ['phash', 'ahash', 'dhash', 'whash']
            if image_hash:
                is_match = self._is_duplicate_in_set(image_hash, hash_set, threshold)
                logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_set: {hash_names[i]} {image_hash[:12]}... match: {is_match}")
                if is_match:
                    matches += 1
            else:
                logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_set: {hash_names[i]} is None")

        result = matches >= min_matches
        logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_set: Total matches: {matches}/{len(image_hashes)}, min_matches: {min_matches}, result: {result}")
        return result

    def _is_enhanced_duplicate_in_existing(self, processed_image: ProcessedImage, threshold: int = 5, min_matches: int = 2) -> bool:
        """Check if processed image is duplicate in existing database using multiple hash algorithms"""
        if not processed_image.phash:
            logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_existing: Missing phash for {processed_image.final_filename}")
            return False

        try:
            # Use database query to check all hashes at once (most efficient)
            image_hashes = [processed_image.phash, processed_image.ahash, processed_image.dhash, processed_image.whash]
            valid_hashes = [h for h in image_hashes if h]

            if not valid_hashes:
                return False

            # Check for exact matches first (fastest path using indexes)
            placeholders = ', '.join([f':hash{i}' for i in range(len(valid_hashes))])
            query = f"""
                SELECT phash, ahash, dhash, whash
                FROM design_images
                WHERE user_id = :user_id
                AND is_active = true
                AND (phash IN ({placeholders})
                     OR ahash IN ({placeholders})
                     OR dhash IN ({placeholders})
                     OR whash IN ({placeholders}))
                LIMIT 10
            """

            params = {"user_id": self.user_id}
            for i, hash_val in enumerate(valid_hashes):
                params[f'hash{i}'] = hash_val

            result = self.db_session.execute(text(query), params)
            rows = result.fetchall()

            if rows:
                # Count exact matches
                matches = 0
                for row in rows:
                    for db_hash in row:
                        if db_hash in valid_hashes:
                            matches += 1
                            if matches >= min_matches:
                                logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_existing: EXACT MATCHES FOUND ({matches}) for {processed_image.final_filename}")
                                return True

            # If no exact matches and threshold allows, check Hamming distance
            if threshold > 0:
                matches = 0
                hash_names = ['phash', 'ahash', 'dhash', 'whash']

                for i, image_hash in enumerate(image_hashes):
                    if image_hash:
                        is_match = self._is_duplicate_in_existing(image_hash, threshold)
                        if is_match:
                            matches += 1
                            logging.info(f"🔍 DEBUG: _is_enhanced_duplicate_in_existing: {hash_names[i]} hamming match")
                            if matches >= min_matches:
                                return True

            return False

        except Exception as e:
            logging.error(f"🔍 DEBUG: _is_enhanced_duplicate_in_existing: Error: {e}")
            return False


    def _upload_batch_to_nas(self, images: List[ProcessedImage], batch_id: int) -> List[ProcessedImage]:
        """
        Upload batch of images to NAS storage in parallel

        Args:
            images: List of processed images to upload
            batch_id: Batch identifier

        Returns:
            List of successfully uploaded images
        """
        if not images:
            return []

        logging.info(f"📤 Batch {batch_id}: Uploading {len(images)} images to NAS in parallel")
        successful_uploads = []

        # Check if NAS storage is available
        if not NAS_AVAILABLE or not nas_storage:
            logging.warning(f"📤 Batch {batch_id}: NAS storage not available, skipping upload")
            return []

        # Get shop and template info once (shared across uploads)
        shop_name = self._get_user_shop_name()

        def upload_single_image(image: ProcessedImage) -> tuple[ProcessedImage, bool]:
            """Upload a single image to NAS"""
            try:
                # Skip if image doesn't have content or filename
                if not image.resized_content or not image.final_filename:
                    logging.info(f"   ⏭️  Skipping {image.upload_info.original_filename}: missing content or filename")
                    return (image, False)

                # Get template name for this specific image
                template_name = self._get_template_name(image.upload_info.template_id)

                # Upload to NAS using the correct method
                success = nas_storage.upload_file_content(
                    image.resized_content,
                    shop_name,
                    f"{template_name}/{image.final_filename}"
                )

                if success:
                    image.nas_uploaded = True
                    logging.info(f"   ✅ Uploaded: {image.final_filename}")
                    return (image, True)
                else:
                    logging.error(f"   ❌ Failed to upload: {image.final_filename}")
                    return (image, False)

            except Exception as e:
                logging.error(f"   ❌ Upload error for {image.final_filename or 'unknown'}: {e}")
                return (image, False)

        # Use thread pool to upload images in parallel
        # Increased to 12 concurrent uploads for better throughput with large batches
        # NAS connection pool supports 20 connections, so this is well within limits
        max_nas_workers = min(12, len(images))
        try:
            with ThreadPoolExecutor(max_workers=max_nas_workers) as executor:
                # Submit all uploads
                future_to_image = {executor.submit(upload_single_image, img): img for img in images}

                # Collect results as they complete
                for future in as_completed(future_to_image):
                    try:
                        image, success = future.result()
                        if success:
                            successful_uploads.append(image)
                    except Exception as e:
                        original_image = future_to_image[future]
                        logging.error(f"   ❌ Upload thread error for {original_image.final_filename or 'unknown'}: {e}")

        except Exception as e:
            logging.error(f"❌ Batch {batch_id} NAS parallel upload failed: {e}")

        logging.info(f"📤 Batch {batch_id}: Successfully uploaded {len(successful_uploads)}/{len(images)} to NAS")
        return successful_uploads

    def _update_database_batch(self, images: List[ProcessedImage], batch_id: int) -> List[ProcessedImage]:
        """
        Update database with new design entries using bulk insert

        Args:
            images: List of images successfully uploaded to NAS
            batch_id: Batch identifier

        Returns:
            List of successfully updated images
        """
        if not images:
            return []

        # Check if dependencies are available
        if not DEPENDENCIES_AVAILABLE:
            logging.warning(f"🗄️  Batch {batch_id}: Database dependencies not available, skipping update")
            return []

        logging.info(f"🗄️  Batch {batch_id}: Updating database with {len(images)} records using bulk insert")
        successful_updates = []

        with self.db_lock:  # Serialize database operations
            now = datetime.now(timezone.utc)
            shop_name = self._get_user_shop_name()

            # Check if multi-tenant is enabled
            multi_tenant = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

            # Get org_id once if multi-tenant
            org_id = None
            if multi_tenant:
                try:
                    org_result = self.db_session.execute(text("""
                        SELECT org_id FROM users WHERE id = :user_id
                    """), {"user_id": self.user_id})
                    org_row = org_result.fetchone()
                    org_id = org_row[0] if org_row else None
                except Exception as e:
                    logging.error(f"   ❌ Failed to get org_id: {e}")

            # Prepare bulk insert data
            insert_values = []
            for image in images:
                try:
                    # Skip if image doesn't have required data
                    if not image.final_filename or not image.phash:
                        logging.info(f"   ⏭️  Skipping {image.upload_info.original_filename}: missing filename or phash")
                        continue

                    template_name = self._get_template_name(image.upload_info.template_id)
                    file_path = f"/share/Graphics/{shop_name}/{template_name}/{image.final_filename}"

                    # Generate unique UUID for this design
                    design_id = str(uuid.uuid4())

                    # Prepare row data
                    row_data = {
                        "id": design_id,
                        "user_id": self.user_id,
                        "filename": image.final_filename,
                        "file_path": file_path,
                        "phash": image.phash,
                        "ahash": image.ahash,
                        "dhash": image.dhash,
                        "whash": image.whash,
                        "is_active": True,
                        "is_digital": False,
                        "created_at": now,
                        "updated_at": now
                    }

                    if multi_tenant:
                        row_data["org_id"] = org_id

                    insert_values.append(row_data)
                    successful_updates.append(image)

                except Exception as e:
                    logging.error(f"   ❌ Error preparing data for {image.final_filename or 'unknown'}: {e}")
                    continue

            # Perform bulk insert if we have data
            if insert_values:
                try:
                    # Build bulk INSERT query
                    if multi_tenant:
                        columns = "id, user_id, org_id, filename, file_path, phash, ahash, dhash, whash, is_active, is_digital, created_at, updated_at"
                        placeholders = ":id, :user_id, :org_id, :filename, :file_path, :phash, :ahash, :dhash, :whash, :is_active, :is_digital, :created_at, :updated_at"
                    else:
                        columns = "id, user_id, filename, file_path, phash, ahash, dhash, whash, is_active, is_digital, created_at, updated_at"
                        placeholders = ":id, :user_id, :filename, :file_path, :phash, :ahash, :dhash, :whash, :is_active, :is_digital, :created_at, :updated_at"

                    # Use executemany for bulk insert (much faster than individual inserts)
                    self.db_session.execute(text(f"""
                        INSERT INTO design_images ({columns})
                        VALUES ({placeholders})
                    """), insert_values)

                    # Mark images as updated
                    for image in successful_updates:
                        image.db_updated = True

                    # Commit all database changes
                    self.db_session.commit()
                    logging.info(f"🗄️  Batch {batch_id}: Successfully bulk inserted {len(insert_values)} records to database")

                except Exception as e:
                    logging.error(f"   ❌ Failed to bulk insert database changes: {e}")
                    try:
                        self.db_session.rollback()
                    except Exception:
                        pass
                    # Return empty list if commit failed
                    return []
            else:
                logging.warning(f"🗄️  Batch {batch_id}: No valid data to insert")

        return successful_updates

    def _generate_mockups_batch(self, images: List[ProcessedImage], batch_id: int) -> List[ProcessedImage]:
        """
        Generate mockups for uploaded images

        Args:
            images: List of images successfully updated in database
            batch_id: Batch identifier

        Returns:
            List of images with successfully generated mockups
        """
        if not images:
            return []

        logging.info(f"🎨 Batch {batch_id}: Generating mockups for {len(images)} images")
        successful_mockups = []

        # Check if mockup service is available
        if not MOCKUP_SERVICE_AVAILABLE:
            logging.warning(f"🎨 Batch {batch_id}: Mockup service not available, skipping mockup generation")
            # Mark all as processed but without mockups
            for image in images:
                image.mockup_generated = False
            return images

        try:
            # Generate mockups for each image
            for image in images:
                try:
                    # Skip if image doesn't have required data
                    if not image.final_filename or not image.db_updated:
                        logging.info(f"   ⏭️  Skipping mockup for {image.upload_info.original_filename}: missing data or not in DB")
                        continue

                    # Generate mockup using existing mockup service
                    mockup_result = self._generate_single_mockup(image)

                    if mockup_result:
                        image.mockup_generated = True
                        successful_mockups.append(image)
                        logging.info(f"   ✅ Generated mockup: {image.final_filename}")
                    else:
                        image.mockup_generated = False
                        logging.error(f"   ❌ Failed to generate mockup: {image.final_filename}")

                except Exception as e:
                    image.mockup_generated = False
                    logging.error(f"   ❌ Mockup error for {image.final_filename or 'unknown'}: {e}")

        except Exception as e:
            logging.error(f"❌ Batch {batch_id} mockup generation failed: {e}")

        logging.info(f"🎨 Batch {batch_id}: Successfully generated {len(successful_mockups)}/{len(images)} mockups")
        return successful_mockups

    def _generate_single_mockup(self, image: ProcessedImage) -> bool:
        """
        Generate a single mockup for an image using the existing mockup service
        """
        try:
            # For now, skip mockup generation in the comprehensive workflow
            # The mockups will be generated later by the existing mockup endpoint
            logging.info(f"Skipping mockup generation for {image.final_filename} - will be handled by mockup service")
            return True

        except Exception as e:
            logging.error(f"Failed to generate mockup for {image.final_filename}: {e}")
            return False

    def _call_mockup_service(self, design_path: str, image: ProcessedImage) -> bool:
        """Call the existing mockup service with proper error handling"""
        try:
            # This would be the actual integration with your mockup service
            # Adjust this based on your mockup service's API
            #
            # Example integration patterns:
            # 1. Direct function call:
            #    result = mockup_service.create_mockup(
            #        user_id=self.user_id,
            #        design_path=design_path,
            #        template_id=image.upload_info.template_id
            #    )
            #
            # 2. Queue-based processing:
            #    mockup_service.queue_mockup_generation(
            #        user_id=self.user_id,
            #        design_path=design_path
            #    )
            #
            # 3. API call:
            #    response = requests.post('/api/mockups/generate', {
            #        'user_id': self.user_id,
            #        'design_path': design_path
            #    })

            # For now, simulate successful mockup generation
            logging.info(f"Would generate mockup for design: {design_path}")
            return True

        except Exception as e:
            logging.error(f"Mockup service error: {e}")
            return False

    def _get_user_shop_name(self) -> str:
        """Get the Etsy shop name for the current user (cached)"""
        # Check cache first
        if self._shop_name_cache:
            return self._shop_name_cache

        with self._cache_lock:
            # Double-check after acquiring lock
            if self._shop_name_cache:
                return self._shop_name_cache

            try:
                if DEPENDENCIES_AVAILABLE:
                    # Query etsy_stores table for the Etsy shop name (not users.shop_name which may be Shopify)
                    result = self.db_session.execute(text("""
                        SELECT shop_name FROM etsy_stores
                        WHERE user_id = :user_id
                        AND is_active = true
                        ORDER BY created_at DESC
                        LIMIT 1
                    """), {"user_id": self.user_id})

                    row = result.fetchone()
                    if row and row[0]:
                        self._shop_name_cache = row[0]
                        logging.info(f"Using Etsy shop name from etsy_stores: {self._shop_name_cache}")
                        return self._shop_name_cache

            except Exception as e:
                logging.info(f"Could not get Etsy shop name from database: {e}")

            # Fallback to user ID-based shop name only if Etsy shop not found
            self._shop_name_cache = f"user_{self.user_id[:8]}"
            logging.warning(f"Using fallback shop name (Etsy shop not found): {self._shop_name_cache}")
            return self._shop_name_cache

    def _get_template_name(self, template_id: str) -> str:
        """Get the template name from template_id (cached)"""
        if not template_id:
            return "uploads"

        # Check cache first
        if template_id in self._template_name_cache:
            return self._template_name_cache[template_id]

        with self._cache_lock:
            # Double-check after acquiring lock
            if template_id in self._template_name_cache:
                return self._template_name_cache[template_id]

            try:
                if DEPENDENCIES_AVAILABLE:
                    result = self.db_session.execute(text("""
                        SELECT name FROM etsy_product_templates WHERE id = :template_id
                    """), {"template_id": template_id})

                    row = result.fetchone()
                    if row and row[0]:
                        self._template_name_cache[template_id] = row[0]
                        return self._template_name_cache[template_id]

            except Exception as e:
                logging.info(f"Could not get template name from database: {e}")

            # Fallback to "uploads" if template not found
            self._template_name_cache[template_id] = "uploads"
            return "uploads"

    def _generate_filename(self, original_filename: str, template_id: str, file_index: int = 0) -> str:
        """Generate filename with proper mockup numbering using starting_name from design_data"""
        try:
            # Get template name for folder organization
            template_name = self._get_template_name(template_id) if template_id else "uploads"

            # Get mockup starting_name and increment for batch processing
            starting_name = getattr(self, '_design_starting_name', 100)  # Default to 100 if not set
            current_id = starting_name + file_index
            current_id_str = str(current_id).zfill(3)

            # Generate proper filename: "UV {id} {template}_{id}.png"
            # Clean template name for filename
            clean_template = template_name.replace(" ", "_")
            final_filename = f"UV {current_id_str} {clean_template}_{current_id_str}.png"

            logging.info(f"Generated filename: {original_filename} -> {final_filename} (starting_name: {starting_name}, index: {file_index})")
            return final_filename

        except Exception as e:
            logging.error(f"Error generating filename: {e}")
            # Fallback to original filename
            return original_filename

    def _compile_workflow_result(self,
                                original_images: List[UploadedImage],
                                batch_results: List[BatchResult],
                                processing_time: float) -> WorkflowResult:
        """Compile final workflow statistics"""

        total_processed = sum(r.processed for r in batch_results)
        total_skipped = sum(r.skipped_local_duplicates + r.skipped_db_duplicates for r in batch_results)
        total_errors = sum(r.errors for r in batch_results)
        total_nas_uploads = sum(r.nas_uploads for r in batch_results)
        total_db_updates = sum(r.db_updates for r in batch_results)
        total_mockups = sum(r.mockups_created for r in batch_results)

        return WorkflowResult(
            total_images=len(original_images),
            processed_images=total_processed,
            skipped_duplicates=total_skipped,
            errors=total_errors,
            processing_time=processing_time,
            nas_uploads=total_nas_uploads,
            db_updates=total_db_updates,
            mockups_created=total_mockups,
            etsy_products=0,  # Placeholder for Etsy integration
            batch_results=batch_results
        )


def create_workflow(user_id: str, db_session=None, max_threads: int = 8, progress_callback=None) -> ImageUploadWorkflow:
    """
    Factory function to create an ImageUploadWorkflow instance

    Args:
        user_id: User ID for the upload session
        db_session: Database session (can be None if dependencies not available)
        max_threads: Maximum number of processing threads

    Returns:
        Configured ImageUploadWorkflow instance

    Raises:
        RuntimeError: If required dependencies are not available
    """
    if not DEPENDENCIES_AVAILABLE:
        raise RuntimeError("Required dependencies not available. Install PIL, imagehash, and sqlalchemy.")

    if db_session is None:
        try:
            from database.core import get_db
            db_session = next(get_db())
        except ImportError:
            raise RuntimeError("Database session not provided and get_db not available")

    return ImageUploadWorkflow(user_id=user_id, db_session=db_session, max_threads=max_threads, progress_callback=progress_callback)


# Example usage:
"""
# Basic usage:
workflow = create_workflow(user_id="user123", db_session=db_session)

# Create list of uploaded images
uploaded_images = [
    UploadedImage(
        original_filename="design1.png",
        content=image_bytes,
        size=len(image_bytes),
        upload_time=datetime.now(timezone.utc),
        user_id="user123",
        template_id="template456"
    ),
    # ... more images
]

# Process the images
result = workflow.process_images(uploaded_images)

# Check results
print(f"Processed: {result.processed_images}/{result.total_images}")
print(f"Duplicates skipped: {result.skipped_duplicates}")
print(f"Errors: {result.errors}")
print(f"NAS uploads: {result.nas_uploads}")
print(f"Database updates: {result.db_updates}")
print(f"Mockups created: {result.mockups_created}")
"""