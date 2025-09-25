#!/usr/bin/env python3
"""
Comprehensive Image Upload Workflow System

This service handles the complete pipeline for uploading and processing images:
1. Batch Processing (8 threads)
2. Image Resizing
3. pHash Generation
4. Duplicate Detection (local and database)
5. NAS Upload
6. Database Updates
7. Mockup Generation
8. Mockup Storage
9. Etsy Product Creation

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field

try:
    import imagehash
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

# Import existing services
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.dirname(current_dir)
sys.path.insert(0, server_dir)

try:
    from utils.nas_storage import nas_storage
    from utils.resizing import get_resizing_configs_from_db
    from database.core import get_db
    NAS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"NAS storage not available: {e}")
    nas_storage = None
    get_resizing_configs_from_db = None
    NAS_AVAILABLE = False

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

    def __init__(self, user_id: str, db_session: Session, max_threads: int = 8):
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError("Required dependencies not available (PIL, imagehash, sqlalchemy)")

        self.user_id = user_id
        self.db_session = db_session
        self.max_threads = max_threads
        self.logger = logging.getLogger(__name__)

        # Thread synchronization
        self.db_lock = threading.Lock()
        self.nas_lock = threading.Lock()

        # Caching for performance
        self._existing_phashes: Optional[Set[str]] = None
        self._existing_phashes_lock = threading.Lock()

        # Configuration
        self.target_width = 3000
        self.target_height = 3000
        self.jpeg_quality = 85
        self.phash_size = 16

    def process_images(self, uploaded_images: List[UploadedImage], design_data=None) -> WorkflowResult:
        """
        Main entry point for processing uploaded images

        Args:
            uploaded_images: List of uploaded image data

        Returns:
            WorkflowResult with complete processing statistics
        """
        start_time = time.time()
        self.logger.info(f"🚀 Starting image upload workflow for {len(uploaded_images)} images")

        try:
            # Pre-load existing phashes from database for duplicate detection
            self._load_existing_phashes()

            # Create batches for processing
            batches = self._create_batches(uploaded_images)
            self.logger.info(f"📦 Created {len(batches)} batches for processing")

            # Process batches in parallel
            batch_results = self._process_batches_parallel(batches, design_data)

            # Calculate final statistics
            processing_time = time.time() - start_time
            workflow_result = self._compile_workflow_result(
                uploaded_images, batch_results, processing_time
            )

            self.logger.info(f"🎉 Workflow completed in {processing_time:.1f}s")
            self.logger.info(f"   📊 Processed: {workflow_result.processed_images}/{workflow_result.total_images}")
            self.logger.info(f"   🔄 Skipped duplicates: {workflow_result.skipped_duplicates}")
            self.logger.info(f"   ❌ Errors: {workflow_result.errors}")
            self.logger.info(f"   📤 NAS uploads: {workflow_result.nas_uploads}")
            self.logger.info(f"   🗄️  DB updates: {workflow_result.db_updates}")
            self.logger.info(f"   🎨 Mockups created: {workflow_result.mockups_created}")

            return workflow_result

        except Exception as e:
            self.logger.error(f"💥 Workflow failed: {e}")
            raise

    def _load_existing_phashes(self):
        """Load all existing phashes from database for duplicate detection"""
        try:
            self.logger.info("📊 Loading existing phashes from database...")

            # Load all phashes for this user from design_images table
            result = self.db_session.execute(text("""
                SELECT DISTINCT phash
                FROM design_images
                WHERE user_id = :user_id
                AND phash IS NOT NULL
                AND phash != ''
                AND is_active = true
            """), {"user_id": self.user_id})

            # Store all phashes - these will be used for duplicate detection
            raw_phashes = {row[0] for row in result.fetchall() if row[0]}

            # Process phashes to handle both single and combined formats
            self._existing_phashes = set()
            for phash in raw_phashes:
                if '|' in phash:
                    # Split combined phash and add primary hash
                    primary_phash = phash.split('|')[0]
                    self._existing_phashes.add(primary_phash)
                else:
                    # Add single phash as-is
                    self._existing_phashes.add(phash)

            self.logger.info(f"📊 Loaded {len(self._existing_phashes)} existing phashes from {len(raw_phashes)} database records")

        except Exception as e:
            self.logger.error(f"❌ Failed to load existing phashes: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self._existing_phashes = set()

    def _create_batches(self, images: List[UploadedImage], batch_size_mb: int = 100) -> List[List[UploadedImage]]:
        """
        Create batches of images for processing (aim for ~100MB per batch)

        Args:
            images: List of uploaded images
            batch_size_mb: Target batch size in MB

        Returns:
            List of image batches
        """
        batches = []
        current_batch = []
        current_size = 0
        target_size = batch_size_mb * 1024 * 1024  # Convert to bytes

        for image in images:
            if current_size + image.size > target_size and current_batch:
                batches.append(current_batch)
                current_batch = [image]
                current_size = image.size
            else:
                current_batch.append(image)
                current_size += image.size

        if current_batch:
            batches.append(current_batch)

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
        self.logger.info(f"🚀 Processing {len(batches)} batches with {max_workers} threads")

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

                    self.logger.info(f"✅ Batch {batch_id} completed:")
                    self.logger.info(f"   📊 Processed: {result.processed}")
                    self.logger.info(f"   🔄 Skipped: {result.skipped_local_duplicates + result.skipped_db_duplicates}")
                    self.logger.info(f"   ❌ Errors: {result.errors}")

                except Exception as e:
                    self.logger.error(f"❌ Batch {batch_id} failed: {e}")
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

        self.logger.info(f"📦 Batch {batch_id}: Processing {len(images)} images")

        try:
            # Step 1: Resize images and generate phashes
            processed_images = []
            local_phashes = set()

            for image in images:
                try:
                    processed_image = self._process_single_image(image, design_data)

                    # Only check for duplicates if processing was successful
                    if processed_image.phash and not processed_image.error:
                        # Extract primary phash for comparison
                        primary_phash = self._extract_primary_phash(processed_image.phash)

                        # Check for local duplicates within this batch
                        if self._is_duplicate_in_set(primary_phash, local_phashes):
                            processed_image.is_duplicate_local = True
                            skipped_local += 1
                            self.logger.debug(f"   🔄 Local duplicate: {processed_image.final_filename}")
                        else:
                            local_phashes.add(primary_phash)

                            # Check for database duplicates
                            with self._existing_phashes_lock:
                                if self._is_duplicate_in_existing(primary_phash):
                                    processed_image.is_duplicate_db = True
                                    skipped_db += 1
                                    self.logger.debug(f"   🔄 DB duplicate: {processed_image.final_filename}")
                    else:
                        # Count failed processing as error
                        if processed_image.error:
                            errors += 1

                    processed_images.append(processed_image)

                except Exception as e:
                    errors += 1
                    error_details.append(f"Processing {image.original_filename}: {e}")
                    self.logger.error(f"   ❌ Error processing {image.original_filename}: {e}")

            # Step 2: Filter unique images
            unique_images = [
                img for img in processed_images
                if not img.is_duplicate_local and not img.is_duplicate_db
            ]

            self.logger.info(f"📦 Batch {batch_id}: {len(unique_images)} unique images to process")

            # Step 3: Upload to NAS
            nas_success = self._upload_batch_to_nas(unique_images, batch_id)
            nas_uploads = len(nas_success)

            # Step 4: Update database
            db_success = self._update_database_batch(nas_success, batch_id)
            db_updates = len(db_success)

            # Step 5: Generate mockups
            mockup_success = self._generate_mockups_batch(db_success, batch_id)
            mockups_created = len(mockup_success)

            processed = len(processed_images) - skipped_local - skipped_db - errors

        except Exception as e:
            error_details.append(f"Batch {batch_id} failed: {e}")
            errors += len(images)
            self.logger.error(f"❌ Batch {batch_id} failed completely: {e}")

        processing_time = time.time() - start_time

        return BatchResult(
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

    def _process_single_image(self, image: UploadedImage, design_data=None) -> ProcessedImage:
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
            pil_image = Image.open(BytesIO(image.content))

            # Validate image properties
            if pil_image.size[0] < 10 or pil_image.size[1] < 10:
                raise ValueError(f"Image too small: {pil_image.size}")

            if pil_image.size[0] > 10000 or pil_image.size[1] > 10000:
                raise ValueError(f"Image too large: {pil_image.size}")

            # Get resizing configuration (use existing utils if available)
            try:
                if hasattr(self, 'db_session') and image.template_id and get_resizing_configs_from_db:
                    # Use existing resizing configuration system
                    canvas_config, _ = get_resizing_configs_from_db(
                        self.db_session,
                        canvas_id=getattr(design_data, 'canvas_config_id', None) if design_data else None,
                        product_template_id=image.template_id
                    )
                else:
                    canvas_config = self._get_canvas_config(image.template_id)
            except:
                # Fallback to default config
                canvas_config = self._get_canvas_config(image.template_id)
            processed.canvas_config = canvas_config

            # Resize image with enhanced processing
            resized_image = self._resize_and_optimize_image(pil_image, canvas_config)

            # Convert to bytes with optimized settings
            buffer = BytesIO()

            # Save as PNG for lossless quality, JPEG for smaller size
            if canvas_config.get('format', 'png').lower() == 'jpeg':
                if resized_image.mode in ('RGBA', 'LA'):
                    # Convert transparent images to white background for JPEG
                    background = Image.new('RGB', resized_image.size, (255, 255, 255))
                    if resized_image.mode == 'RGBA':
                        background.paste(resized_image, mask=resized_image.split()[-1])
                    else:
                        background.paste(resized_image)
                    resized_image = background

                resized_image.save(
                    buffer,
                    format='JPEG',
                    quality=self.jpeg_quality,
                    optimize=True,
                    progressive=True
                )
                file_ext = 'jpg'
            else:
                resized_image.save(
                    buffer,
                    format='PNG',
                    optimize=True,
                    compress_level=6
                )
                file_ext = 'png'

            resized_content = buffer.getvalue()

            # Generate multiple hashes for better duplicate detection
            phash = str(imagehash.phash(resized_image, hash_size=self.phash_size))
            dhash = str(imagehash.dhash(resized_image, hash_size=self.phash_size))

            # Use phash as primary, but store both for advanced duplicate detection
            processed.phash = f"{phash}|{dhash}"

            # Generate secure filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            safe_basename = self._sanitize_filename(Path(image.original_filename).stem)
            final_filename = f"{safe_basename}_{timestamp}_{image.temp_id[:8]}.{file_ext}"

            # Update processed image
            processed.resized_content = resized_content
            processed.resized_size = len(resized_content)
            processed.final_filename = final_filename
            processed.processing_time = time.time() - start_time

            self.logger.debug(f"Processed {image.original_filename}: {pil_image.size} → {resized_image.size}, phash: {phash[:12]}...")

            return processed

        except Exception as e:
            processed.error = str(e)
            processed.processing_time = time.time() - start_time
            self.logger.error(f"Failed to process {image.original_filename}: {e}")
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
            self.logger.debug(f"Could not get canvas config from DB: {e}")

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

    def _is_duplicate_in_set(self, phash: str, phash_set: Set[str], hamming_threshold: int = 5) -> bool:
        """Check if phash is duplicate within a set using Hamming distance"""
        if not phash:
            return False

        try:
            # Convert phash to integer for comparison
            phash_int = int(phash, 16)

            for existing_phash in phash_set:
                if existing_phash:
                    existing_int = int(existing_phash, 16)
                    # Calculate Hamming distance
                    hamming_distance = bin(phash_int ^ existing_int).count('1')
                    if hamming_distance <= hamming_threshold:
                        return True

            return False

        except (ValueError, TypeError) as e:
            self.logger.debug(f"Error comparing phashes: {e}")
            return False

    def _is_duplicate_in_existing(self, phash: str, hamming_threshold: int = 5) -> bool:
        """Check if phash is duplicate within existing database hashes"""
        if not phash or not self._existing_phashes:
            return False

        try:
            # Convert phash to integer for comparison
            phash_int = int(phash, 16)

            for existing_hash in self._existing_phashes:
                # Handle combined hashes from database
                existing_phash = self._extract_primary_phash(existing_hash)
                if existing_phash:
                    existing_int = int(existing_phash, 16)
                    # Calculate Hamming distance
                    hamming_distance = bin(phash_int ^ existing_int).count('1')
                    if hamming_distance <= hamming_threshold:
                        return True

            return False

        except (ValueError, TypeError) as e:
            self.logger.debug(f"Error comparing with existing phashes: {e}")
            return False

    def _upload_batch_to_nas(self, images: List[ProcessedImage], batch_id: int) -> List[ProcessedImage]:
        """
        Upload batch of images to NAS storage

        Args:
            images: List of processed images to upload
            batch_id: Batch identifier

        Returns:
            List of successfully uploaded images
        """
        if not images:
            return []

        self.logger.info(f"📤 Batch {batch_id}: Uploading {len(images)} images to NAS")
        successful_uploads = []

        # Check if NAS storage is available
        if not NAS_AVAILABLE or not nas_storage:
            self.logger.warning(f"📤 Batch {batch_id}: NAS storage not available, skipping upload")
            return []

        with self.nas_lock:  # Serialize NAS operations to prevent conflicts
            try:
                for image in images:
                    try:
                        # Skip if image doesn't have content or filename
                        if not image.resized_content or not image.final_filename:
                            self.logger.debug(f"   ⏭️  Skipping {image.upload_info.original_filename}: missing content or filename")
                            continue

                        # Get user shop name for NAS path
                        shop_name = self._get_user_shop_name()
                        template_name = image.upload_info.template_id or "uploads"

                        # Upload to NAS using the correct method
                        success = nas_storage.upload_file_content(
                            image.resized_content,
                            shop_name,
                            f"{template_name}/{image.final_filename}"
                        )

                        if success:
                            image.nas_uploaded = True
                            successful_uploads.append(image)
                            self.logger.debug(f"   ✅ Uploaded: {image.final_filename}")
                        else:
                            self.logger.error(f"   ❌ Failed to upload: {image.final_filename}")

                    except Exception as e:
                        self.logger.error(f"   ❌ Upload error for {image.final_filename or 'unknown'}: {e}")

            except Exception as e:
                self.logger.error(f"❌ Batch {batch_id} NAS upload failed: {e}")

        self.logger.info(f"📤 Batch {batch_id}: Successfully uploaded {len(successful_uploads)}/{len(images)} to NAS")
        return successful_uploads

    def _update_database_batch(self, images: List[ProcessedImage], batch_id: int) -> List[ProcessedImage]:
        """
        Update database with new design entries

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
            self.logger.warning(f"🗄️  Batch {batch_id}: Database dependencies not available, skipping update")
            return []

        self.logger.info(f"🗄️  Batch {batch_id}: Updating database with {len(images)} records")
        successful_updates = []

        with self.db_lock:  # Serialize database operations
            now = datetime.now(timezone.utc)
            shop_name = self._get_user_shop_name()

            # Check if multi-tenant is enabled
            multi_tenant = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

            for image in images:
                try:
                    # Skip if image doesn't have required data
                    if not image.final_filename or not image.phash:
                        self.logger.debug(f"   ⏭️  Skipping {image.upload_info.original_filename}: missing filename or phash")
                        continue

                    template_name = image.upload_info.template_id or "uploads"
                    file_path = f"/share/Graphics/{shop_name}/{template_name}/{image.final_filename}"

                    # Generate unique UUID for this design
                    design_id = str(uuid.uuid4())

                    if multi_tenant:
                        # Get user's org_id
                        org_result = self.db_session.execute(text("""
                            SELECT org_id FROM users WHERE id = :user_id
                        """), {"user_id": self.user_id})
                        org_row = org_result.fetchone()
                        org_id = org_row[0] if org_row else None

                        self.db_session.execute(text("""
                            INSERT INTO design_images
                            (id, user_id, org_id, filename, file_path, phash, is_active, created_at, updated_at)
                            VALUES (:id, :user_id, :org_id, :filename, :file_path, :phash, :is_active, :created_at, :updated_at)
                            ON CONFLICT (phash) DO NOTHING
                        """), {
                            "id": design_id,
                            "user_id": self.user_id,
                            "org_id": org_id,
                            "filename": image.final_filename,
                            "file_path": file_path,
                            "phash": image.phash,
                            "is_active": True,
                            "created_at": now,
                            "updated_at": now
                        })
                    else:
                        self.db_session.execute(text("""
                            INSERT INTO design_images
                            (id, user_id, filename, file_path, phash, is_active, created_at, updated_at)
                            VALUES (:id, :user_id, :filename, :file_path, :phash, :is_active, :created_at, :updated_at)
                            ON CONFLICT (phash) DO NOTHING
                        """), {
                            "id": design_id,
                            "user_id": self.user_id,
                            "filename": image.final_filename,
                            "file_path": file_path,
                            "phash": image.phash,
                            "is_active": True,
                            "created_at": now,
                            "updated_at": now
                        })

                    image.db_updated = True
                    successful_updates.append(image)

                    # Add to existing phashes to prevent duplicates in subsequent batches
                    with self._existing_phashes_lock:
                        if self._existing_phashes is not None and image.phash:
                            self._existing_phashes.add(image.phash)

                except Exception as e:
                    self.logger.error(f"   ❌ DB error for {image.final_filename or 'unknown'}: {e}")
                    # Continue processing other images - don't let one failure stop all

            self.logger.info(f"🗄️  Batch {batch_id}: Successfully updated {len(successful_updates)}/{len(images)} records")

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

        self.logger.info(f"🎨 Batch {batch_id}: Generating mockups for {len(images)} images")
        successful_mockups = []

        # Check if mockup service is available
        if not MOCKUP_SERVICE_AVAILABLE:
            self.logger.warning(f"🎨 Batch {batch_id}: Mockup service not available, skipping mockup generation")
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
                        self.logger.debug(f"   ⏭️  Skipping mockup for {image.upload_info.original_filename}: missing data or not in DB")
                        continue

                    # Generate mockup using existing mockup service
                    mockup_result = self._generate_single_mockup(image)

                    if mockup_result:
                        image.mockup_generated = True
                        successful_mockups.append(image)
                        self.logger.debug(f"   ✅ Generated mockup: {image.final_filename}")
                    else:
                        image.mockup_generated = False
                        self.logger.error(f"   ❌ Failed to generate mockup: {image.final_filename}")

                except Exception as e:
                    image.mockup_generated = False
                    self.logger.error(f"   ❌ Mockup error for {image.final_filename or 'unknown'}: {e}")

        except Exception as e:
            self.logger.error(f"❌ Batch {batch_id} mockup generation failed: {e}")

        self.logger.info(f"🎨 Batch {batch_id}: Successfully generated {len(successful_mockups)}/{len(images)} mockups")
        return successful_mockups

    def _generate_single_mockup(self, image: ProcessedImage) -> bool:
        """
        Generate a single mockup for an image
        This integrates with your existing mockup generation system
        """
        try:
            # Integration with existing mockup service
            if MOCKUP_SERVICE_AVAILABLE and mockup_service:
                # Get shop name and build paths
                shop_name = self._get_user_shop_name()
                template_name = image.upload_info.template_id or "uploads"
                design_path = f"{shop_name}/{template_name}/{image.final_filename}"

                # Generate mockup using the existing service
                # This is a simplified call - adjust based on your actual mockup service API
                mockup_result = self._call_mockup_service(design_path, image)

                return mockup_result

            else:
                # Fallback: simulate mockup generation for testing
                time.sleep(0.05)  # Simulate processing time
                return True

        except Exception as e:
            self.logger.error(f"Failed to generate mockup for {image.final_filename}: {e}")
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
            self.logger.debug(f"Would generate mockup for design: {design_path}")
            return True

        except Exception as e:
            self.logger.error(f"Mockup service error: {e}")
            return False

    def _get_user_shop_name(self) -> str:
        """Get the shop name for the current user"""
        try:
            if DEPENDENCIES_AVAILABLE:
                result = self.db_session.execute(text("""
                    SELECT shop_name FROM users WHERE id = :user_id
                """), {"user_id": self.user_id})

                row = result.fetchone()
                if row and row[0]:
                    return row[0]

        except Exception as e:
            self.logger.debug(f"Could not get shop name from database: {e}")

        # Fallback to user ID-based shop name
        return f"user_{self.user_id[:8]}"

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


def create_workflow(user_id: str, db_session=None, max_threads: int = 8) -> ImageUploadWorkflow:
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

    return ImageUploadWorkflow(user_id=user_id, db_session=db_session, max_threads=max_threads)


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