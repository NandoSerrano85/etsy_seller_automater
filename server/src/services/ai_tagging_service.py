"""
Automatic Image Tagging Service

Supports two modes:
1. AI Mode (OpenAI Vision API) - Premium, AI-powered tagging ($0.01/image)
2. Basic Mode (OCR + Color Detection) - FREE, no API required

Generates tags including:
- Text extraction (OCR using Tesseract)
- Filename parsing
- Color palette analysis
- Basic image properties
- [AI only] Object/subject identification
- [AI only] Style and aesthetic tags
"""

import os
import logging
import json
import re
from typing import Dict, Optional, Any, List
import base64
import time
from functools import wraps
from io import BytesIO

# Core image libraries (always available)
try:
    import numpy as np
    from PIL import Image
    import cv2
    CORE_LIBS_AVAILABLE = True
except ImportError:
    CORE_LIBS_AVAILABLE = False
    logging.error("Core libraries (numpy, PIL, cv2) not available")

# OCR library (free text extraction)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract not installed. OCR will be disabled. Run: pip install pytesseract")

# OpenAI library (premium AI tagging)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.info("OpenAI SDK not installed. Using basic tagging mode. (Optional: pip install openai)")

def retry_on_error(max_retries=3, delay=1.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Final attempt failed - re-raise
                        raise
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

class AITaggingService:
    """Service for automatic image tag generation (AI or Basic mode)"""

    def __init__(self):
        # Configuration from environment
        self.enabled = os.getenv('ENABLE_AI_TAGGING', 'true').lower() == 'true'
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
        self.timeout = int(os.getenv('OPENAI_TIMEOUT', '30'))

        # Determine mode: AI or Basic
        self.use_ai_mode = False
        if self.enabled and OPENAI_AVAILABLE and self.api_key:
            self.use_ai_mode = True
            self.client = OpenAI(api_key=self.api_key)
            logging.info(f"✓ AI Tagging Service initialized (AI MODE) with model: {self.model}")
        elif self.enabled:
            self.client = None
            logging.info("✓ AI Tagging Service initialized (BASIC MODE - Free, no API required)")
            logging.info("  - OCR text extraction: " + ("✓" if TESSERACT_AVAILABLE else "✗"))
            logging.info("  - Color detection: ✓")
            logging.info("  - Filename parsing: ✓")
        else:
            self.client = None
            logging.info("AI Tagging Service disabled")

    def generate_tags(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Generate comprehensive tags for an image

        Args:
            image_bytes: Raw image bytes (PNG/JPEG)
            filename: Original filename for context

        Returns:
            {
                'tags': ['tag1', 'tag2', ...],
                'metadata': {
                    'mode': 'ai' or 'basic',
                    'processing_time': 1.23,
                    'categories': {...}
                }
            }
        """
        if not self.enabled:
            return {
                'tags': [],
                'metadata': {'error': 'Tagging disabled'}
            }

        start_time = time.time()

        try:
            if self.use_ai_mode:
                # Premium AI-powered tagging
                result = self._generate_tags_ai(image_bytes, filename, start_time)
            else:
                # Free basic tagging
                result = self._generate_tags_basic(image_bytes, filename, start_time)

            logging.info(
                f"✓ Generated {len(result['tags'])} tags for {filename} "
                f"in {result['metadata']['processing_time']:.2f}s "
                f"(mode: {result['metadata'].get('mode', 'unknown')})"
            )

            return result

        except Exception as e:
            logging.error(f"✗ Tagging failed for {filename}: {e}")
            return {
                'tags': [],
                'metadata': {
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
            }

    @retry_on_error(max_retries=3, delay=1.0)
    def _generate_tags_ai(self, image_bytes: bytes, filename: str, start_time: float) -> Dict[str, Any]:
        """AI-powered tagging using OpenAI Vision API"""
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Build comprehensive tagging prompt
        prompt = self._build_ai_tagging_prompt(filename)

        # Call OpenAI Vision API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low"  # Cost optimization
                            }
                        }
                    ]
                }
            ],
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )

        processing_time = time.time() - start_time

        # Parse and structure response
        result = self._parse_ai_vision_response(
            response.choices[0].message.content,
            processing_time
        )

        # Log usage for cost tracking
        estimated_cost = 0.01
        logging.info(
            f"API Usage: {filename} | {processing_time:.2f}s | "
            f"{len(result['tags'])} tags | ~${estimated_cost:.4f}"
        )

        result['metadata']['mode'] = 'ai'
        return result

    def _generate_tags_basic(self, image_bytes: bytes, filename: str, start_time: float) -> Dict[str, Any]:
        """Free basic tagging using OCR, colors, and filename parsing"""
        all_tags = []
        categories = {
            'text': [],
            'filename': [],
            'colors': [],
            'properties': []
        }

        try:
            # Load image
            pil_image = Image.open(BytesIO(image_bytes))

            # 1. Extract text using OCR (if available)
            if TESSERACT_AVAILABLE:
                try:
                    text_tags = self._extract_text_ocr(pil_image)
                    categories['text'] = text_tags
                    all_tags.extend(text_tags)
                except Exception as e:
                    logging.warning(f"OCR failed: {e}")

            # 2. Parse filename for keywords
            filename_tags = self._parse_filename(filename)
            categories['filename'] = filename_tags
            all_tags.extend(filename_tags)

            # 3. Detect dominant colors
            if CORE_LIBS_AVAILABLE:
                try:
                    color_tags = self._detect_colors(image_bytes)
                    categories['colors'] = color_tags
                    all_tags.extend(color_tags)
                except Exception as e:
                    logging.warning(f"Color detection failed: {e}")

            # 4. Basic image properties
            property_tags = self._extract_properties(pil_image)
            categories['properties'] = property_tags
            all_tags.extend(property_tags)

            # Normalize: lowercase, deduplicate, trim
            all_tags = list(set([tag.lower().strip() for tag in all_tags if tag and len(tag) > 1]))

            processing_time = time.time() - start_time

            return {
                'tags': all_tags,
                'metadata': {
                    'mode': 'basic',
                    'processing_time': round(processing_time, 2),
                    'categories': categories,
                    'total_tags': len(all_tags),
                    'ocr_available': TESSERACT_AVAILABLE
                }
            }

        except Exception as e:
            logging.error(f"Basic tagging failed: {e}")
            processing_time = time.time() - start_time
            return {
                'tags': [],
                'metadata': {
                    'mode': 'basic',
                    'error': str(e),
                    'processing_time': processing_time
                }
            }

    def _extract_text_ocr(self, pil_image: Image.Image) -> List[str]:
        """Extract text from image using Tesseract OCR"""
        try:
            # Convert to grayscale for better OCR
            gray_image = pil_image.convert('L')

            # Extract text
            text = pytesseract.image_to_string(gray_image, config='--psm 6')

            # Clean and split into words
            words = re.findall(r'\b[a-zA-Z]{2,}\b', text)

            # Remove common stop words
            stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'let', 'put', 'say', 'she', 'too', 'use'}
            filtered_words = [w for w in words if w.lower() not in stop_words]

            # Return unique words (limit to 20)
            return list(set(filtered_words))[:20]

        except Exception as e:
            logging.warning(f"OCR extraction failed: {e}")
            return []

    def _parse_filename(self, filename: str) -> List[str]:
        """Extract keywords from filename"""
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]

        # Split on common separators and extract words
        words = re.findall(r'[a-zA-Z]{2,}', name_without_ext)

        # Remove common prefixes/suffixes
        common_words = {'dtf', 'uvdtf', 'png', 'jpg', 'jpeg', 'design', 'img', 'image', 'file', 'uv'}
        filtered = [w for w in words if w.lower() not in common_words]

        return list(set(filtered))[:10]

    def _detect_colors(self, image_bytes: bytes) -> List[str]:
        """Detect dominant colors in image"""
        try:
            # Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return []

            # Resize for faster processing
            small = cv2.resize(img, (100, 100))

            # Convert to RGB
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            # Reshape to list of pixels
            pixels = rgb.reshape(-1, 3)

            # Calculate average color
            avg_color = pixels.mean(axis=0)

            # Detect dominant colors by clustering
            colors = []

            # Simple color detection based on RGB values
            r, g, b = avg_color

            # Determine main color
            if r > 200 and g > 200 and b > 200:
                colors.append('white')
            elif r < 50 and g < 50 and b < 50:
                colors.append('black')
            elif r > g and r > b:
                if r > 150:
                    colors.append('red')
                else:
                    colors.append('brown')
            elif g > r and g > b:
                colors.append('green')
            elif b > r and b > g:
                colors.append('blue')
            elif r > 150 and g > 150:
                colors.append('yellow')
            elif r > 150 and b > 150:
                colors.append('pink')
            elif g > 150 and b > 150:
                colors.append('cyan')

            # Check for grayscale
            if abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
                if 100 < r < 200:
                    colors.append('gray')

            return list(set(colors))

        except Exception as e:
            logging.warning(f"Color detection failed: {e}")
            return []

    def _extract_properties(self, pil_image: Image.Image) -> List[str]:
        """Extract basic image properties"""
        properties = []

        try:
            width, height = pil_image.size

            # Size classification
            total_pixels = width * height
            if total_pixels < 500000:  # < 0.5 megapixels
                properties.append('small')
            elif total_pixels < 2000000:  # < 2 megapixels
                properties.append('medium')
            else:
                properties.append('large')

            # Orientation
            aspect_ratio = width / height
            if aspect_ratio > 1.2:
                properties.append('landscape')
            elif aspect_ratio < 0.8:
                properties.append('portrait')
            else:
                properties.append('square')

            # Check for transparency
            if pil_image.mode in ('RGBA', 'LA') or (pil_image.mode == 'P' and 'transparency' in pil_image.info):
                properties.append('transparent')

            return properties

        except Exception as e:
            logging.warning(f"Property extraction failed: {e}")
            return []

    def _build_ai_tagging_prompt(self, filename: str) -> str:
        """Build optimized prompt for AI tagging"""
        return f"""Analyze this design image and extract comprehensive tags.

CRITICAL: Return ONLY valid JSON (no markdown, no code blocks).

Extract and categorize:
1. **text**: All visible text/words (OCR) - be thorough
2. **objects**: Main subjects, objects, characters, animals, shapes
3. **relationships**: How objects interact (e.g., "dinosaur holding umbrella")
4. **style**: Art style (cartoon, realistic, vintage, minimalist, etc.)
5. **colors**: Dominant colors (be specific: "pastel pink", "navy blue")
6. **themes**: Overall mood/concepts (playful, elegant, festive, etc.)

Return this exact JSON structure:
{{
  "text": ["word1", "word2"],
  "objects": ["smiley face", "dinosaur", "umbrella"],
  "relationships": ["dinosaur holding umbrella"],
  "style": ["cartoon", "colorful"],
  "colors": ["green", "yellow", "blue"],
  "themes": ["playful", "happy"]
}}

Context: {filename}

Be specific, descriptive, and thorough."""

    def _parse_ai_vision_response(self, content: str, processing_time: float) -> Dict[str, Any]:
        """Parse OpenAI Vision response into structured tags"""
        try:
            # Clean markdown artifacts if present
            content = content.strip()
            if content.startswith('```'):
                lines = content.split('\n')
                content = '\n'.join(line for line in lines if not line.startswith('```'))

            # Parse JSON
            data = json.loads(content)

            # Flatten all categories into single tag list + preserve categories
            all_tags = []
            categories = {}

            for category in ['text', 'objects', 'relationships', 'style', 'colors', 'themes']:
                category_tags = data.get(category, [])
                if isinstance(category_tags, list):
                    all_tags.extend(category_tags)
                    categories[category] = category_tags

            # Normalize: lowercase, deduplicate, trim
            all_tags = list(set([tag.lower().strip() for tag in all_tags if tag]))

            return {
                'tags': all_tags,
                'metadata': {
                    'model': self.model,
                    'processing_time': round(processing_time, 2),
                    'categories': categories,
                    'total_tags': len(all_tags)
                }
            }

        except json.JSONDecodeError as e:
            logging.error(f"JSON parse failed: {e}")
            logging.debug(f"Response: {content}")
            # Fallback: simple word extraction
            words = [w.strip().lower() for w in content.split() if len(w.strip()) > 2]
            return {
                'tags': words[:20],  # Limit fallback
                'metadata': {
                    'error': 'JSON parse failed - used fallback',
                    'processing_time': processing_time
                }
            }

# Singleton instance
ai_tagging_service = AITaggingService()
