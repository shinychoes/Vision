"""
Tests for vision_ui.cli module, focusing on summarize-multi functionality.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from vision_ui.cli import cmd_summarize_multi, build_parser


class TestSummarizeMultiCLI:
    """Test the summarize-multi CLI command."""
    
    def create_sample_file(self, content: str) -> Path:
        """Create a temporary sample file for testing."""
        temp_file = Path("temp_test_sample.txt")
        temp_file.write_text(content, encoding='utf-8')
        return temp_file
    
    def cleanup_sample_file(self, file_path: Path):
        """Clean up temporary test file."""
        if file_path.exists():
            file_path.unlink()
    
    def test_summarize_multi_basic(self):
        """Test basic summarize-multi functionality."""
        content = "This is a test sentence. This is another test sentence. " * 10
        temp_file = self.create_sample_file(content)
        
        try:
            # Mock argparse namespace
            args = type('Args', (), {
                'file': str(temp_file),
                'profiles': 'phone,laptop',
                'layers': 'headline,one_screen',
                'persona': None,
                'format': 'stacked'
            })()
            
            # Capture stdout
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                cmd_summarize_multi(args)
            
            output = captured_output.getvalue()
            
            # Verify output contains expected structure
            assert "=== PHONE ===" in output
            assert "=== LAPTOP ===" in output
            assert "--- Headline ---" in output
            assert "--- One Screen ---" in output
            assert len(output) > 0
            
        finally:
            self.cleanup_sample_file(temp_file)
    
    def test_summarize_multi_json_format(self):
        """Test summarize-multi with JSON output format."""
        content = "Test content for JSON output. " * 5
        temp_file = self.create_sample_file(content)
        
        try:
            args = type('Args', (), {
                'file': str(temp_file),
                'profiles': 'phone',
                'layers': 'headline',
                'persona': None,
                'format': 'json'
            })()
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                cmd_summarize_multi(args)
            
            output = captured_output.getvalue()
            
            # Verify valid JSON
            import json
            parsed = json.loads(output)
            assert "phone" in parsed
            assert "headline" in parsed["phone"]
            
        finally:
            self.cleanup_sample_file(temp_file)
    
    def test_summarize_multi_compact_format(self):
        """Test summarize-multi with compact output format."""
        content = "Test content for compact output. " * 3
        temp_file = self.create_sample_file(content)
        
        try:
            args = type('Args', (), {
                'file': str(temp_file),
                'profiles': 'phone,laptop',
                'layers': 'headline',
                'persona': None,
                'format': 'compact'
            })()
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                cmd_summarize_multi(args)
            
            output = captured_output.getvalue()
            
            # Verify compact format
            lines = output.strip().split('\n')
            assert len(lines) == 2
            assert "phone.headline:" in lines[0]
            assert "laptop.headline:" in lines[1]
            
        finally:
            self.cleanup_sample_file(temp_file)
    
    def test_summarize_multi_with_persona(self):
        """Test summarize-multi with persona."""
        content = "The user has a problem with the system. We need to fix the code."
        temp_file = self.create_sample_file(content)
        
        try:
            args = type('Args', (), {
                'file': str(temp_file),
                'profiles': 'phone',
                'layers': 'headline',
                'persona': 'developer',
                'format': 'stacked'
            })()
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                cmd_summarize_multi(args)
            
            output = captured_output.getvalue()
            
            # Should contain persona-related content
            assert "=== PHONE ===" in output
            assert "--- Headline ---" in output
            assert len(output) > 0
            
        finally:
            self.cleanup_sample_file(temp_file)
    
    def test_summarize_multi_invalid_profiles(self):
        """Test summarize-multi with invalid profile names."""
        content = "Test content."
        temp_file = self.create_sample_file(content)
        
        try:
            args = type('Args', (), {
                'file': str(temp_file),
                'profiles': 'invalid_profile',
                'layers': 'headline',
                'persona': None,
                'format': 'stacked'
            })()
            
            captured_output = StringIO()
            with patch('sys.stderr', captured_output):
                with pytest.raises(SystemExit):
                    cmd_summarize_multi(args)
            
            error_output = captured_output.getvalue()
            assert "Error:" in error_output
            
        finally:
            self.cleanup_sample_file(temp_file)
    
    def test_summarize_multi_invalid_persona(self):
        """Test summarize-multi with invalid persona name."""
        content = "Test content."
        temp_file = self.create_sample_file(content)
        
        try:
            args = type('Args', (), {
                'file': str(temp_file),
                'profiles': 'phone',
                'layers': 'headline',
                'persona': 'invalid_persona',
                'format': 'stacked'
            })()
            
            captured_output = StringIO()
            with patch('sys.stderr', captured_output):
                with pytest.raises(SystemExit):
                    cmd_summarize_multi(args)
            
            error_output = captured_output.getvalue()
            assert "Error:" in error_output
            
        finally:
            self.cleanup_sample_file(temp_file)
    
    def test_summarize_multi_stdin_input(self):
        """Test summarize-multi reading from stdin."""
        content = "Test content from stdin. " * 5
        
        args = type('Args', (), {
            'file': '-',  # Read from stdin
            'profiles': 'phone',
            'layers': 'headline',
            'persona': None,
            'format': 'compact'
        })()
        
        # Mock stdin
        with patch('sys.stdin', StringIO(content)):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                cmd_summarize_multi(args)
            
            output = captured_output.getvalue()
            assert "phone.headline:" in output
            assert len(output) > 0


class TestParser:
    """Test argument parser configuration."""
    
    def test_summarize_multi_parser_exists(self):
        """Test that summarize-multi subcommand exists."""
        parser = build_parser()
        
        # Test help for summarize-multi
        with patch('sys.stdout', StringIO()) as mock_stdout:
            try:
                parser.parse_args(['summarize-multi', '--help'])
            except SystemExit:
                pass  # --help causes SystemExit
        
        # Verify the command was processed (help text should contain summarize-multi)
        help_text = mock_stdout.getvalue()
        assert 'summarize-multi' in help_text
    
    def test_summarize_multi_required_args(self):
        """Test that required arguments are enforced."""
        parser = build_parser()
        
        # Missing required --file argument
        with pytest.raises(SystemExit):
            parser.parse_args(['summarize-multi', '--profiles', 'phone'])
        
        # Missing required --profiles argument
        with pytest.raises(SystemExit):
            parser.parse_args(['summarize-multi', '--file', 'test.txt'])
    
    def test_summarize_multi_valid_args(self):
        """Test parsing valid arguments."""
        parser = build_parser()
        
        args = parser.parse_args([
            'summarize-multi',
            '--file', 'test.txt',
            '--profiles', 'phone,laptop',
            '--layers', 'headline,one_screen',
            '--persona', 'developer',
            '--format', 'json'
        ])
        
        assert args.file == 'test.txt'
        assert args.profiles == 'phone,laptop'
        assert args.layers == 'headline,one_screen'
        assert args.persona == 'developer'
        assert args.format == 'json'
    
    def test_summarize_multi_default_args(self):
        """Test parsing with default arguments."""
        parser = build_parser()
        
        args = parser.parse_args([
            'summarize-multi',
            '--file', 'test.txt',
            '--profiles', 'phone'
        ])
        
        assert args.layers == 'headline,one_screen,deep'  # default
        assert args.persona is None  # default
        assert args.format == 'stacked'  # default
