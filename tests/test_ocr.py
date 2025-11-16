"""
Tests for vision_ui.ocr module, focusing on screenshot-aware summarization.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from vision_ui.ocr import (
    ImageProcessor, OCRExtractor, ScreenshotAnalyzer,
    ImageRegion, OCRResult, extract_text_from_image,
    analyze_screenshot_for_summarization
)


class TestImageProcessor:
    """Test image preprocessing functionality."""
    
    @pytest.mark.skip("PIL ImageEnhance mocking is complex - tested via integration")
    def test_preprocess_for_ocr_basic(self):
        """Test basic image preprocessing."""
        pass
    
    @patch('vision_ui.ocr.os.path.exists')
    @patch('vision_ui.ocr.Image.open')
    def test_preprocess_for_ocr_no_enhance(self, mock_image_open, mock_exists):
        """Test preprocessing without enhancement."""
        mock_exists.return_value = True
        
        mock_image = MagicMock()
        mock_image.mode = "L"  # Already grayscale
        mock_image.size = (1200, 900)
        mock_image_open.return_value = mock_image
        
        processor = ImageProcessor()
        processed_image, applied_steps = processor.preprocess_for_ocr("test.png", enhance=False)
        
        # Should only convert to grayscale if needed
        assert len(applied_steps) == 0 or "grayscale" in applied_steps
    
    @pytest.mark.skip("PIL ImageEnhance mocking is complex - tested via integration")
    def test_preprocess_for_ocr_small_image_resize(self):
        """Test that small images are resized for better OCR."""
        pass


class TestOCRExtractor:
    """Test OCR text extraction functionality."""
    
    def test_extractor_initialization(self):
        """Test OCR extractor initialization."""
        extractor = OCRExtractor()
        assert extractor is not None
    
    def test_extractor_with_custom_path(self):
        """Test OCR extractor with custom tesseract path."""
        custom_path = "/usr/bin/tesseract"
        extractor = OCRExtractor(tesseract_path=custom_path)
        assert extractor is not None
    
    @patch('vision_ui.ocr.os.path.exists')
    @patch('vision_ui.ocr.pytesseract.image_to_string')
    @patch('vision_ui.ocr.pytesseract.image_to_data')
    @patch('vision_ui.ocr.Image.open')
    @patch('vision_ui.ocr.ImageProcessor.preprocess_for_ocr')
    def test_extract_text_success(self, mock_preprocess, mock_image_open, mock_image_to_data, mock_image_to_string, mock_exists):
        """Test successful OCR text extraction."""
        mock_exists.return_value = True
        
        # Mock preprocessing to avoid PIL complexity
        mock_image = MagicMock()
        mock_image.mode = "RGB"
        mock_image.size = (1000, 800)
        mock_preprocess.return_value = (mock_image, [])
        mock_image_open.return_value = mock_image
        
        # Mock OCR results
        mock_image_to_string.return_value = "Extracted text content"
        mock_image_to_data.return_value = {
            'text': ['Extracted', 'text', 'content', ''],
            'conf': [95, 88, 92, 0],
            'left': [10, 100, 200, 0],
            'top': [10, 10, 10, 0],
            'width': [80, 50, 70, 0],
            'height': [20, 20, 20, 0]
        }
        
        extractor = OCRExtractor()
        result = extractor.extract_text("test.png")
        
        assert isinstance(result, OCRResult)
        assert result.full_text == "Extracted text content"
        assert len(result.regions) == 3  # Non-empty text regions
        assert result.image_info['size'] == (1000, 800)
        assert result.preprocessing_applied == []  # No preprocessing by default
    
    @patch('vision_ui.ocr.os.path.exists')
    @patch('vision_ui.ocr.pytesseract.image_to_string')
    @patch('vision_ui.ocr.pytesseract.image_to_data')
    @patch('vision_ui.ocr.Image.open')
    def test_extract_text_with_preprocessing(self, mock_image_open, mock_image_to_data, mock_image_to_string, mock_exists):
        """Test OCR extraction with preprocessing enabled."""
        mock_exists.return_value = True
        
        # Mock image processor
        mock_image = MagicMock()
        mock_image.mode = "RGB"
        mock_image.size = (500, 400)
        mock_image_open.return_value = mock_image
        
        with patch('vision_ui.ocr.ImageProcessor.preprocess_for_ocr') as mock_preprocess:
            mock_preprocess.return_value = (mock_image, ['grayscale', 'enhance'])
            
            # Mock OCR results
            mock_image_to_string.return_value = "Processed text"
            mock_image_to_data.return_value = {
                'text': ['Processed', 'text', ''],
                'conf': [90, 85, 0],
                'left': [0, 50, 0],
                'top': [0, 0, 0],
                'width': [40, 30, 0],
                'height': [15, 15, 0]
            }
            
            extractor = OCRExtractor()
            result = extractor.extract_text("test.png", preprocess=True)
            
            assert result.full_text == "Processed text"
            assert 'grayscale' in result.preprocessing_applied
            assert 'enhance' in result.preprocessing_applied
    
    def test_extract_text_file_not_found(self):
        """Test OCR extraction with non-existent file."""
        extractor = OCRExtractor()
        
        with pytest.raises(FileNotFoundError, match="Image file not found"):
            extractor.extract_text("nonexistent.png")
    
    def test_parse_ocr_data_empty(self):
        """Test parsing empty OCR data."""
        extractor = OCRExtractor()
        empty_data = {
            'text': [], 'conf': [], 'left': [], 'top': [], 'width': [], 'height': []
        }
        
        regions = extractor._parse_ocr_data(empty_data)
        assert regions == []
    
    def test_parse_ocr_data_filters_low_confidence(self):
        """Test that low confidence OCR results are filtered out."""
        extractor = OCRExtractor()
        data = {
            'text': ['High confidence', 'Low confidence', ''],
            'conf': [95, 25, 0],  # 25 is below threshold
            'left': [0, 50, 0],
            'top': [0, 0, 0],
            'width': [100, 80, 0],
            'height': [20, 20, 0]
        }
        
        regions = extractor._parse_ocr_data(data)
        assert len(regions) == 1  # Only high confidence region
        assert regions[0].text == "High confidence"
        assert regions[0].confidence == 0.95
    
    def test_classify_region_code(self):
        """Test region classification for code content."""
        extractor = OCRExtractor()
        
        # Code patterns
        assert extractor._classify_region("def function():", 0, 0) == "code"
        assert extractor._classify_region("if (condition) {", 0, 0) == "code"
        assert extractor._classify_region("import numpy as np", 0, 0) == "code"
    
    def test_classify_region_ui_element(self):
        """Test region classification for UI elements."""
        extractor = OCRExtractor()
        
        assert extractor._classify_region("Click", 0, 0) == "ui_element"
        assert extractor._classify_region("OK", 0, 0) == "ui_element"
        assert extractor._classify_region("Submit", 0, 0) == "ui_element"
    
    def test_classify_region_numeric(self):
        """Test region classification for numeric content."""
        extractor = OCRExtractor()
        
        assert extractor._classify_region("123.45", 0, 0) == "numeric"
        assert extractor._classify_region("95%", 0, 0) == "numeric"
    
    def test_classify_region_url_path(self):
        """Test region classification for URLs and paths."""
        extractor = OCRExtractor()
        
        assert extractor._classify_region("https://example.com", 0, 0) == "url_path"
        assert extractor._classify_region("C:\\Users\\file.txt", 0, 0) == "url_path"
        assert extractor._classify_region("/usr/local/bin", 0, 0) == "url_path"
    
    def test_classify_region_default_text(self):
        """Test default region classification as text."""
        extractor = OCRExtractor()
        
        assert extractor._classify_region("Regular text content", 0, 0) == "text"


class TestScreenshotAnalyzer:
    """Test screenshot analysis functionality."""
    
    @patch('vision_ui.ocr.OCRExtractor.extract_text')
    def test_analyze_screenshot_success(self, mock_extract):
        """Test successful screenshot analysis."""
        # Mock OCR result
        mock_ocr_result = OCRResult(
            full_text="Screenshot content",
            regions=[ImageRegion(0, 0, 100, 20, "Screenshot", 0.95)],
            image_info={'size': (800, 600)},
            preprocessing_applied=['grayscale']
        )
        mock_extract.return_value = mock_ocr_result
        
        analyzer = ScreenshotAnalyzer()
        result = analyzer.analyze_screenshot("test.png")
        
        assert result.full_text == "Screenshot content"
        assert len(result.regions) == 1
        assert result.preprocessing_applied == ['grayscale']
    
    def test_extract_ui_regions_empty(self):
        """Test extracting UI regions from empty result."""
        analyzer = ScreenshotAnalyzer()
        empty_result = OCRResult(
            full_text="",
            regions=[],
            image_info={'size': (100, 100)},
            preprocessing_applied=[]
        )
        
        regions_by_type = analyzer.extract_ui_regions(empty_result)
        assert regions_by_type == {}
    
    def test_extract_ui_regions_grouped(self):
        """Test grouping regions by type."""
        analyzer = ScreenshotAnalyzer()
        result = OCRResult(
            full_text="Mixed content",
            regions=[
                ImageRegion(0, 0, 50, 20, "Click", 0.9, "ui_element"),
                ImageRegion(60, 0, 100, 20, "def func()", 0.85, "code"),
                ImageRegion(0, 30, 80, 20, "OK", 0.95, "ui_element")
            ],
            image_info={'size': (200, 100)},
            preprocessing_applied=[]
        )
        
        regions_by_type = analyzer.extract_ui_regions(result)
        
        assert len(regions_by_type["ui_element"]) == 2
        assert len(regions_by_type["code"]) == 1
        assert regions_by_type["ui_element"][0].text == "Click"
        assert regions_by_type["code"][0].text == "def func()"
    
    def test_estimate_text_density_empty(self):
        """Test text density estimation with no regions."""
        analyzer = ScreenshotAnalyzer()
        empty_result = OCRResult(
            full_text="",
            regions=[],
            image_info={'size': (1000, 800)},
            preprocessing_applied=[]
        )
        
        density = analyzer.estimate_text_density(empty_result)
        assert density == 0.0
    
    def test_estimate_text_density_calculated(self):
        """Test text density calculation."""
        analyzer = ScreenshotAnalyzer()
        result = OCRResult(
            full_text="Content",
            regions=[
                ImageRegion(0, 0, 200, 20, "Text", 0.9),  # 4000 pixels
                ImageRegion(0, 30, 300, 30, "More text", 0.8)  # 9000 pixels
            ],
            image_info={'size': (1000, 800)},  # 800,000 total pixels
            preprocessing_applied=[]
        )
        
        density = analyzer.estimate_text_density(result)
        expected_density = (4000 + 9000) / 800000
        assert abs(density - expected_density) < 0.001


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('vision_ui.ocr.OCRExtractor.extract_text')
    def test_extract_text_from_image(self, mock_extract):
        """Test extract_text_from_image convenience function."""
        mock_result = OCRResult(
            full_text="Convenience test",
            regions=[],
            image_info={'size': (100, 100)},
            preprocessing_applied=[]
        )
        mock_extract.return_value = mock_result
        
        text = extract_text_from_image("test.png")
        assert text == "Convenience test"
    
    @patch('vision_ui.ocr.ScreenshotAnalyzer.analyze_screenshot')
    def test_analyze_screenshot_for_summarization(self, mock_analyze):
        """Test analyze_screenshot_for_summarization convenience function."""
        mock_result = OCRResult(
            full_text="Screenshot analysis",
            regions=[],
            image_info={'size': (200, 150)},
            preprocessing_applied=['enhance']
        )
        mock_analyze.return_value = mock_result
        
        result = analyze_screenshot_for_summarization("test.png")
        assert result.full_text == "Screenshot analysis"
        assert result.preprocessing_applied == ['enhance']


class TestImageRegion:
    """Test ImageRegion dataclass."""
    
    def test_image_region_creation(self):
        """Test creating an ImageRegion."""
        region = ImageRegion(
            x=10, y=20, width=100, height=30,
            text="Test region", confidence=0.95, region_type="text"
        )
        
        assert region.x == 10
        assert region.y == 20
        assert region.width == 100
        assert region.height == 30
        assert region.text == "Test region"
        assert region.confidence == 0.95
        assert region.region_type == "text"
    
    def test_image_region_default_type(self):
        """Test ImageRegion with default region type."""
        region = ImageRegion(
            x=0, y=0, width=50, height=20,
            text="Default", confidence=0.8
        )
        
        assert region.region_type == "text"


class TestOCRResult:
    """Test OCRResult dataclass."""
    
    def test_ocr_result_creation(self):
        """Test creating an OCRResult."""
        regions = [ImageRegion(0, 0, 100, 20, "Test", 0.9)]
        image_info = {"size": (800, 600), "format": ".png"}
        preprocessing = ["grayscale", "enhance"]
        
        result = OCRResult(
            full_text="Test result",
            regions=regions,
            image_info=image_info,
            preprocessing_applied=preprocessing
        )
        
        assert result.full_text == "Test result"
        assert len(result.regions) == 1
        assert result.image_info == image_info
        assert result.preprocessing_applied == preprocessing
