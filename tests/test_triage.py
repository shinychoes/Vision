"""
Tests for vision_ui.triage module, focusing on rich formatting and triage board functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
from rich.console import Console

from vision_ui.triage import (
    TriageBoard, format_triage_output, display_triage_board
)
from vision_ui.profiles import Profile


class TestTriageBoard:
    """Test triage board functionality."""
    
    def test_triage_board_initialization(self):
        """Test triage board initialization."""
        board = TriageBoard()
        assert board.console is not None
        
        # Test with custom console
        custom_console = Console(width=80)
        board_custom = TriageBoard(console=custom_console)
        assert board_custom.console == custom_console
    
    def test_display_comparison_basic(self):
        """Test basic comparison display."""
        # Create test summaries
        summaries = {
            "phone": {
                "headline": "Mobile headline summary",
                "one_screen": "Mobile one-screen summary with more content"
            },
            "laptop": {
                "headline": "Laptop headline summary that is longer",
                "one_screen": "Laptop one-screen summary with even more detailed content"
            }
        }
        
        # Create test profiles
        profiles = [
            Profile("phone", 375, 667, font_size_px=14),
            Profile("laptop", 1920, 1080, font_size_px=16)
        ]
        
        # Capture output
        string_io = StringIO()
        console = Console(file=string_io, width=120)
        board = TriageBoard(console)
        
        board.display_comparison(summaries, profiles)
        
        output = string_io.getvalue()
        
        # Should contain title and profile names
        assert "MULTI-PROFILE TRIAGE BOARD" in output
        assert "PHONE" in output
        assert "LAPTOP" in output
        assert "Mobile headline summary" in output
        assert "Laptop headline summary" in output
    
    def test_display_comparison_with_ocr_metadata(self):
        """Test comparison display with OCR metadata."""
        summaries = {
            "phone": {"headline": "Test summary"}
        }
        
        profiles = [Profile("phone", 375, 667)]
        
        ocr_metadata = {
            "text_density": 0.75,
            "regions_found": 5,
            "preprocessing_applied": ["grayscale", "enhance"],
            "image_size": (1200, 900)
        }
        
        string_io = StringIO()
        console = Console(file=string_io)
        board = TriageBoard(console)
        
        board.display_comparison(summaries, profiles, show_metadata=True, ocr_metadata=ocr_metadata)
        
        output = string_io.getvalue()
        
        assert "OCR Processing Metadata" in output
        assert "75.0%" in output
        assert "5" in output
        assert "grayscale" in output
        assert "1200 × 900" in output
    
    def test_display_profile_info(self):
        """Test profile information display."""
        profiles = [
            Profile("phone", 375, 667, font_size_px=14, editor_ruler_columns=40, buffer=0.8),
            Profile("laptop", 1920, 1080, font_size_px=16, editor_ruler_columns=80, buffer=0.9),
            Profile("slides", 1024, 768, font_size_px=18, editor_ruler_columns=60, buffer=0.85)
        ]
        
        string_io = StringIO()
        console = Console(file=string_io)
        board = TriageBoard(console)
        
        board.display_profile_info(profiles)
        
        output = string_io.getvalue()
        
        assert "Device Profile Information" in output
        assert "PHONE" in output
        assert "LAPTOP" in output
        assert "SLIDES" in output
        assert "375×667" in output
        assert "1920×1080" in output
        assert "1024×768" in output


class TestTriageFormatting:
    """Test triage formatting functions."""
    
    def test_format_triage_output_basic(self):
        """Test basic triage output formatting."""
        summaries = {
            "phone": {"headline": "Mobile summary"},
            "laptop": {"headline": "Laptop summary"}
        }
        
        profiles = [
            Profile("phone", 375, 667),
            Profile("laptop", 1920, 1080)
        ]
        
        output = format_triage_output(summaries, profiles)
        
        assert isinstance(output, str)
        assert "MULTI-PROFILE TRIAGE BOARD" in output
        assert "Mobile summary" in output
        assert "Laptop summary" in output
    
    def test_format_triage_output_with_profile_info(self):
        """Test triage output with profile information."""
        summaries = {"phone": {"headline": "Test"}}
        profiles = [Profile("phone", 375, 667)]
        
        output = format_triage_output(
            summaries, profiles, 
            show_profile_info=True
        )
        
        assert "Device Profile Information" in output
        assert "PHONE" in output
    
    def test_format_triage_output_with_metadata(self):
        """Test triage output with OCR metadata."""
        summaries = {"phone": {"headline": "Test"}}
        profiles = [Profile("phone", 375, 667)]
        
        ocr_metadata = {
            "text_density": 0.5,
            "regions_found": 3,
            "preprocessing_applied": ["grayscale"],
            "image_size": (800, 600)
        }
        
        output = format_triage_output(
            summaries, profiles,
            show_metadata=True,
            ocr_metadata=ocr_metadata
        )
        
        assert "OCR Processing Metadata" in output
        assert "50.0%" in output
    
    @patch('vision_ui.triage.TriageBoard.display_comparison')
    @patch('vision_ui.triage.TriageBoard.display_profile_info')
    def test_display_triage_board_function(self, mock_profile_info, mock_comparison):
        """Test display_triage_board convenience function."""
        summaries = {"phone": {"headline": "Test"}}
        profiles = [Profile("phone", 375, 667)]
        
        display_triage_board(summaries, profiles)
        
        # Should call display_comparison but not profile_info
        mock_comparison.assert_called_once()
        mock_profile_info.assert_not_called()
    
    @patch('vision_ui.triage.TriageBoard.display_comparison')
    @patch('vision_ui.triage.TriageBoard.display_profile_info')
    def test_display_triage_board_with_options(self, mock_profile_info, mock_comparison):
        """Test display_triage_board with all options."""
        summaries = {"phone": {"headline": "Test"}}
        profiles = [Profile("phone", 375, 667)]
        ocr_metadata = {"text_density": 0.5}
        
        display_triage_board(
            summaries, profiles,
            show_profile_info=True,
            show_metadata=True,
            ocr_metadata=ocr_metadata
        )
        
        # Should call both functions when profile info is requested
        mock_comparison.assert_called_once()
        mock_profile_info.assert_called_once()


class TestTriageIntegration:
    """Test triage board integration with other modules."""
    
    @patch('vision_ui.summarize.multi_profile_summarize')
    def test_integration_with_multi_profile_summarize(self, mock_summarize):
        """Test integration with multi-profile summarization."""
        # Mock the summarization result
        mock_summaries = {
            "phone": {"headline": "Phone headline"},
            "laptop": {"headline": "Laptop headline"}
        }
        mock_summarize.return_value = mock_summaries
        
        profiles = [Profile("phone", 375, 667), Profile("laptop", 1920, 1080)]
        
        output = format_triage_output(mock_summaries, profiles)
        
        assert "Phone headline" in output
        assert "Laptop headline" in output
        assert "MULTI-PROFILE TRIAGE BOARD" in output
    
    def test_empty_summaries_handling(self):
        """Test handling of empty summaries."""
        summaries = {}
        profiles = [Profile("phone", 375, 667)]
        
        output = format_triage_output(summaries, profiles)
        
        # Should still show the title even with no summaries
        assert "MULTI-PROFILE TRIAGE BOARD" in output
    
    def test_missing_layers_handling(self):
        """Test handling when profiles have different layers."""
        summaries = {
            "phone": {"headline": "Phone headline"},
            "laptop": {"one_screen": "Laptop one-screen"}  # Different layer
        }
        
        profiles = [
            Profile("phone", 375, 667),
            Profile("laptop", 1920, 1080)
        ]
        
        output = format_triage_output(summaries, profiles)
        
        # Should handle missing layers gracefully
        assert "Phone headline" in output
        assert "Laptop one-screen" in output
        assert "N/A" in output  # For missing layers


class TestTriageErrorHandling:
    """Test error handling in triage functionality."""
    
    def test_invalid_profile_handling(self):
        """Test handling of invalid profile data."""
        summaries = {"invalid": {"headline": "Test"}}
        profiles = []  # Empty profiles list
        
        # Should not crash, just show empty results
        output = format_triage_output(summaries, profiles)
        assert isinstance(output, str)
    
    def test_malformed_metadata_handling(self):
        """Test handling of malformed OCR metadata."""
        summaries = {"phone": {"headline": "Test"}}
        profiles = [Profile("phone", 375, 667)]
        
        # Malformed metadata
        bad_metadata = {
            "text_density": None,
            "regions_found": "invalid",
            "preprocessing_applied": None,
            "image_size": "invalid"
        }
        
        # Should handle gracefully without crashing
        output = format_triage_output(
            summaries, profiles,
            show_metadata=True,
            ocr_metadata=bad_metadata
        )
        
        assert isinstance(output, str)
        assert "OCR Processing Metadata" in output
