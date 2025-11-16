"""
Integration tests for screenshot-aware summarization functionality.
Tests the end-to-end workflow from CLI to OCR to summarization.
"""

import pytest
from unittest.mock import patch, MagicMock
from vision_ui.cli import cmd_summarize_screenshot
from vision_ui.summarize import screenshot_aware_summarize, summarize_screenshot
from vision_ui.profiles import load_profile
import argparse


class TestScreenshotIntegration:
    """Test screenshot-aware summarization integration."""
    
    @patch('vision_ui.summarize.ScreenshotAnalyzer.analyze_screenshot')
    def test_screenshot_aware_summarize_integration(self, mock_analyze):
        """Test end-to-end screenshot-aware summarization."""
        # Mock OCR result
        mock_ocr_result = MagicMock()
        mock_ocr_result.full_text = "This is a screenshot with some text content for testing."
        mock_ocr_result.regions = []
        mock_ocr_result.preprocessing_applied = ['grayscale', 'enhance']
        mock_ocr_result.image_info = {'size': (800, 600)}
        mock_analyze.return_value = mock_ocr_result
        
        # Mock analyzer methods
        with patch('vision_ui.summarize.ScreenshotAnalyzer.extract_ui_regions') as mock_regions, \
             patch('vision_ui.summarize.ScreenshotAnalyzer.estimate_text_density') as mock_density:
            
            mock_regions.return_value = {}
            mock_density.return_value = 0.5
            
            profiles = [load_profile("phone"), load_profile("laptop")]
            result = screenshot_aware_summarize(
                image_path="test.png",
                profiles=profiles,
                layers=["headline", "one_screen"],
                persona="developer"
            )
            
            # Should have summaries for both profiles
            assert "phone" in result
            assert "laptop" in result
            assert "headline" in result["phone"]
            assert "one_screen" in result["phone"]
            assert "headline" in result["laptop"]
            assert "one_screen" in result["laptop"]
            
            # Should have OCR metadata
            assert "_ocr_metadata" in result
            assert result["_ocr_metadata"]["text_density"] == 0.5
            assert len(result["_ocr_metadata"]["preprocessing_applied"]) > 0
    
    @patch('vision_ui.summarize.ScreenshotAnalyzer.analyze_screenshot')
    def test_summarize_screenshot_convenience(self, mock_analyze):
        """Test the convenience function for single profile summarization."""
        # Mock OCR result
        mock_ocr_result = MagicMock()
        mock_ocr_result.full_text = "Simple screenshot text for testing."
        mock_ocr_result.regions = []
        mock_ocr_result.preprocessing_applied = []
        mock_ocr_result.image_info = {'size': (1000, 800)}
        mock_analyze.return_value = mock_ocr_result
        
        with patch('vision_ui.summarize.ScreenshotAnalyzer.extract_ui_regions') as mock_regions, \
             patch('vision_ui.summarize.ScreenshotAnalyzer.estimate_text_density') as mock_density:
            
            mock_regions.return_value = {}
            mock_density.return_value = 0.3
            
            summary = summarize_screenshot(
                image_path="test.png",
                profile_name="laptop",
                layer="headline",
                persona="designer"
            )
            
            assert isinstance(summary, str)
            assert len(summary) > 0
    
    @patch('vision_ui.cli.screenshot_aware_summarize')
    def test_cli_screenshot_command_integration(self, mock_summarize):
        """Test CLI integration for screenshot summarization."""
        # Mock the summarization result
        mock_result = {
            "phone": {
                "headline": "Phone headline from screenshot",
                "one_screen": "Phone one-screen summary from screenshot"
            },
            "laptop": {
                "headline": "Laptop headline from screenshot",
                "one_screen": "Laptop one-screen summary from screenshot"
            }
        }
        mock_summarize.return_value = mock_result
        
        # Create mock arguments
        args = argparse.Namespace(
            image="test.png",
            profiles="phone,laptop",
            layers="headline,one_screen",
            persona="developer",
            format="stacked",
            verbose=False
        )
        
        # Test CLI command
        cmd_summarize_screenshot(args)
        
        # Verify the function was called with correct parameters
        mock_summarize.assert_called_once()
        call_args = mock_summarize.call_args[1]
        
        assert call_args["image_path"] == "test.png"
        assert len(call_args["profiles"]) == 2
        assert call_args["persona"] == "developer"
        assert "headline" in call_args["layers"]
        assert "one_screen" in call_args["layers"]
    
    @patch('vision_ui.cli.screenshot_aware_summarize')
    def test_cli_screenshot_verbose_output(self, mock_summarize):
        """Test CLI verbose output with OCR metadata."""
        # Mock result with OCR metadata
        mock_result = {
            "phone": {"headline": "Test headline"},
            "_ocr_metadata": {
                "text_density": 0.75,
                "regions_found": 5,
                "preprocessing_applied": ["grayscale", "enhance"],
                "image_size": (1200, 900)
            }
        }
        mock_summarize.return_value = mock_result
        
        args = argparse.Namespace(
            image="test.png",
            profiles="phone",
            layers="headline",
            persona=None,
            format="compact",
            verbose=True
        )
        
        # Capture output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        cmd_summarize_screenshot(args)
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        
        # Should contain OCR metadata
        assert "OCR METADATA" in output
        assert "75.00%" in output  # text density
        assert "Regions found: 5" in output
        assert "grayscale" in output
        assert "1200" in output  # image size
    
    @patch('vision_ui.summarize.ScreenshotAnalyzer.analyze_screenshot')
    def test_screenshot_no_text_error_handling(self, mock_analyze):
        """Test error handling when no text is found in screenshot."""
        # Mock empty OCR result
        mock_ocr_result = MagicMock()
        mock_ocr_result.full_text = "   "  # Only whitespace
        mock_analyze.return_value = mock_ocr_result
        
        profiles = [load_profile("phone")]
        
        with pytest.raises(ValueError, match="No text found in screenshot"):
            screenshot_aware_summarize(
                image_path="empty.png",
                profiles=profiles,
                layers=["headline"]
            )
    
    @patch('vision_ui.summarize.ScreenshotAnalyzer.analyze_screenshot')
    def test_screenshot_ocr_failure_handling(self, mock_analyze):
        """Test error handling when OCR analysis fails."""
        # Mock OCR failure
        mock_analyze.side_effect = RuntimeError("Tesseract not found")
        
        profiles = [load_profile("phone")]
        
        with pytest.raises(RuntimeError, match="Failed to analyze screenshot"):
            screenshot_aware_summarize(
                image_path="corrupt.png",
                profiles=profiles,
                layers=["headline"]
            )
