"""
vision_ui.ocr

OCR and image-aware text extraction for screenshot summarization.
Supports image preprocessing, text extraction, and region-based analysis.
"""

import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError as e:
    raise ImportError(f"OCR dependencies not installed. Install with: pip install pytesseract pillow\nError: {e}")


@dataclass
class ImageRegion:
    """Represents a region within an image with extracted text."""
    x: int
    y: int
    width: int
    height: int
    text: str
    confidence: float
    region_type: str = "text"  # text, code, ui_element, etc.


@dataclass
class OCRResult:
    """Complete OCR extraction result."""
    full_text: str
    regions: List[ImageRegion]
    image_info: Dict[str, Any]
    preprocessing_applied: List[str]


class ImageProcessor:
    """Handles image preprocessing for better OCR accuracy."""
    
    @staticmethod
    def preprocess_for_ocr(image_path: str, enhance: bool = True) -> Tuple[Image.Image, List[str]]:
        """
        Apply preprocessing steps to improve OCR accuracy.
        
        Args:
            image_path: Path to the input image
            enhance: Whether to apply enhancement filters
            
        Returns:
            Tuple of (processed_image, applied_steps)
        """
        image = Image.open(image_path)
        applied_steps = []
        
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
            applied_steps.append('grayscale')
        
        # Resize if too small (OCR struggles with tiny text)
        width, height = image.size
        if width < 1000 or height < 800:
            scale = max(1000/width, 800/height)
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            applied_steps.append(f'rescale_{scale:.2f}x')
        
        if enhance:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            applied_steps.append('contrast_enhance')
            
            # Apply slight sharpening
            image = image.filter(ImageFilter.SHARPEN)
            applied_steps.append('sharpen')
            
            # Binarization for better text detection
            threshold = 128
            image = image.point(lambda p: 255 if p > threshold else 0)
            applied_steps.append('binarize')
        
        return image, applied_steps


class OCRExtractor:
    """Extracts text from images using Tesseract OCR."""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR extractor.
        
        Args:
            tesseract_path: Optional path to tesseract executable
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_text(self, image_path: str, preprocess: bool = True) -> OCRResult:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to apply preprocessing
            
        Returns:
            OCRResult with extracted text and metadata
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Preprocess image
        preprocessing_steps = []
        if preprocess:
            processor = ImageProcessor()
            image, preprocessing_steps = processor.preprocess_for_ocr(image_path)
        else:
            image = Image.open(image_path)
        
        # Get image info
        image_info = {
            'size': image.size,
            'mode': image.mode,
            'format': Path(image_path).suffix.lower()
        }
        
        # Extract full text
        try:
            full_text = pytesseract.image_to_string(image, lang='eng')
            full_text = full_text.strip()
        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {e}")
        
        # Extract text with bounding box data
        try:
            data = pytesseract.image_to_data(image, lang='eng', output_type=pytesseract.Output.DICT)
            regions = self._parse_ocr_data(data)
        except Exception:
            # Fallback to empty regions if detailed extraction fails
            regions = []
        
        return OCRResult(
            full_text=full_text,
            regions=regions,
            image_info=image_info,
            preprocessing_applied=preprocessing_steps
        )
    
    def _parse_ocr_data(self, data: Dict[str, List]) -> List[ImageRegion]:
        """
        Parse Tesseract OCR data into structured regions.
        
        Args:
            data: Raw OCR data from pytesseract
            
        Returns:
            List of ImageRegion objects
        """
        regions = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text and int(data['conf'][i]) > 30:  # Filter low-confidence results
                region = ImageRegion(
                    x=data['left'][i],
                    y=data['top'][i],
                    width=data['width'][i],
                    height=data['height'][i],
                    text=text,
                    confidence=float(data['conf'][i]) / 100.0,
                    region_type=self._classify_region(text, data['left'][i], data['top'][i])
                )
                regions.append(region)
        
        return regions
    
    def _classify_region(self, text: str, x: int, y: int) -> str:
        """
        Classify text region based on content and position.
        
        Args:
            text: Extracted text
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Region type classification
        """
        # Code patterns
        if re.search(r'[{}();]', text) or re.search(r'\b(def|class|import|if|for|while)\b', text):
            return 'code'
        
        # UI elements (buttons, labels)
        if re.search(r'^(Click|OK|Cancel|Submit|Save|Delete|Edit)$', text, re.IGNORECASE):
            return 'ui_element'
        
        # Numbers and measurements
        if re.match(r'^[\d,.%]+$', text):
            return 'numeric'
        
        # URLs and file paths
        if re.search(r'https?://|\.com|\.org|/|\\', text):
            return 'url_path'
        
        # Default to text
        return 'text'


class ScreenshotAnalyzer:
    """Analyzes screenshots for layout-aware summarization."""
    
    def __init__(self, ocr_extractor: Optional[OCRExtractor] = None):
        """
        Initialize screenshot analyzer.
        
        Args:
            ocr_extractor: Optional OCR extractor instance
        """
        self.ocr_extractor = ocr_extractor or OCRExtractor()
    
    def analyze_screenshot(self, image_path: str) -> OCRResult:
        """
        Analyze a screenshot and extract structured text.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            OCRResult with extracted text and layout information
        """
        return self.ocr_extractor.extract_text(image_path, preprocess=True)
    
    def extract_ui_regions(self, ocr_result: OCRResult) -> Dict[str, List[ImageRegion]]:
        """
        Group regions by type for layout-aware processing.
        
        Args:
            ocr_result: OCR extraction result
            
        Returns:
            Dictionary mapping region types to lists of regions
        """
        regions_by_type = {}
        for region in ocr_result.regions:
            if region.region_type not in regions_by_type:
                regions_by_type[region.region_type] = []
            regions_by_type[region.region_type].append(region)
        
        return regions_by_type
    
    def estimate_text_density(self, ocr_result: OCRResult) -> float:
        """
        Estimate text density for budget adjustment.
        
        Args:
            ocr_result: OCR extraction result
            
        Returns:
            Text density ratio (0.0 to 1.0)
        """
        if not ocr_result.regions:
            return 0.0
        
        # Calculate total text area vs image area
        total_text_area = sum(r.width * r.height for r in ocr_result.regions)
        image_area = ocr_result.image_info['size'][0] * ocr_result.image_info['size'][1]
        
        return min(total_text_area / image_area, 1.0) if image_area > 0 else 0.0


def extract_text_from_image(image_path: str, preprocess: bool = True) -> str:
    """
    Convenience function to extract text from an image.
    
    Args:
        image_path: Path to the image file
        preprocess: Whether to apply preprocessing
        
    Returns:
        Extracted text as string
    """
    extractor = OCRExtractor()
    result = extractor.extract_text(image_path, preprocess=preprocess)
    return result.full_text


def analyze_screenshot_for_summarization(image_path: str) -> OCRResult:
    """
    Convenience function to analyze a screenshot for summarization.
    
    Args:
        image_path: Path to the screenshot image
        
    Returns:
        Complete OCR analysis result
    """
    analyzer = ScreenshotAnalyzer()
    return analyzer.analyze_screenshot(image_path)
