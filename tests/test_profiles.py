"""
Tests for vision_ui.profiles module.
"""

import pytest
import json
import tempfile
from pathlib import Path

from vision_ui.profiles import (
    Profile,
    load_profile,
    list_profiles,
    save_profile,
    parse_profiles_from_cli,
    DEFAULT_PROFILES,
    get_profile_dir
)


class TestProfile:
    """Test Profile dataclass and basic operations."""
    
    def test_profile_creation(self):
        """Test creating a profile."""
        profile = Profile(
            name="test",
            width_px=800,
            height_px=600,
            font_size_px=12,
            editor_ruler_columns=70,
            buffer=0.85
        )
        assert profile.name == "test"
        assert profile.width_px == 800
        assert profile.height_px == 600
        assert profile.font_size_px == 12
        assert profile.editor_ruler_columns == 70
        assert profile.buffer == 0.85
    
    def test_profile_defaults(self):
        """Test profile default values."""
        profile = Profile(
            name="test",
            width_px=800,
            height_px=600
        )
        assert profile.font_size_px == 14
        assert profile.editor_ruler_columns == 80
        assert profile.buffer == 0.9
    
    def test_profile_to_dict(self):
        """Test converting profile to dictionary."""
        profile = Profile(
            name="test",
            width_px=800,
            height_px=600,
            font_size_px=12,
            editor_ruler_columns=70,
            buffer=0.85
        )
        expected = {
            "name": "test",
            "width_px": 800,
            "height_px": 600,
            "font_size_px": 12,
            "editor_ruler_columns": 70,
            "buffer": 0.85
        }
        assert profile.to_dict() == expected
    
    def test_profile_from_dict(self):
        """Test creating profile from dictionary."""
        data = {
            "name": "test",
            "width_px": 800,
            "height_px": 600,
            "font_size_px": 12,
            "editor_ruler_columns": 70,
            "buffer": 0.85
        }
        profile = Profile.from_dict(data)
        assert profile.name == "test"
        assert profile.width_px == 800
        assert profile.height_px == 600


class TestDefaultProfiles:
    """Test built-in default profiles."""
    
    def test_default_profiles_exist(self):
        """Test that all expected default profiles exist."""
        expected_names = ["laptop", "phone", "slides", "tweet"]
        for name in expected_names:
            assert name in DEFAULT_PROFILES
            assert isinstance(DEFAULT_PROFILES[name], Profile)
    
    def test_laptop_profile(self):
        """Test laptop profile has sensible defaults."""
        laptop = DEFAULT_PROFILES["laptop"]
        assert laptop.name == "laptop"
        assert laptop.width_px == 1920
        assert laptop.height_px == 1080
        assert laptop.font_size_px == 14
        assert laptop.editor_ruler_columns == 80
        assert laptop.buffer == 0.9
    
    def test_phone_profile(self):
        """Test phone profile has mobile-appropriate settings."""
        phone = DEFAULT_PROFILES["phone"]
        assert phone.name == "phone"
        assert phone.width_px == 375  # iPhone-like
        assert phone.height_px == 667
        assert phone.font_size_px == 12  # Smaller font for mobile
        assert phone.editor_ruler_columns == 40  # Narrower columns
        assert phone.buffer == 0.85


class TestLoadProfile:
    """Test profile loading functionality."""
    
    def test_load_builtin_profile(self):
        """Test loading built-in profiles by name."""
        laptop = load_profile("laptop")
        assert laptop.name == "laptop"
        assert laptop.width_px == 1920
        
        phone = load_profile("phone")
        assert phone.name == "phone"
        assert phone.width_px == 375
    
    def test_load_profile_from_file(self):
        """Test loading profile from JSON file."""
        profile_data = {
            "name": "custom",
            "width_px": 1024,
            "height_px": 768,
            "font_size_px": 16,
            "editor_ruler_columns": 90,
            "buffer": 0.95
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f)
            temp_path = f.name
        
        try:
            profile = load_profile(temp_path)
            assert profile.name == "custom"
            assert profile.width_px == 1024
            assert profile.height_px == 768
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_profile(self):
        """Test loading non-existent profile raises error."""
        with pytest.raises(ValueError, match="Profile not found"):
            load_profile("nonexistent")
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON file raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid profile file"):
                load_profile(temp_path)
        finally:
            Path(temp_path).unlink()


class TestListProfiles:
    """Test profile listing functionality."""
    
    def test_list_default_profiles(self):
        """Test listing includes all default profiles."""
        profiles = list_profiles()
        expected = ["laptop", "phone", "slides", "tweet"]
        for name in expected:
            assert name in profiles
    
    def test_list_profiles_sorted(self):
        """Test that profile list is sorted."""
        profiles = list_profiles()
        assert profiles == sorted(profiles)


class TestSaveProfile:
    """Test profile saving functionality."""
    
    def test_save_profile(self):
        """Test saving a profile to file."""
        profile = Profile(
            name="test_save",
            width_px=800,
            height_px=600
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profile_dir = Path(temp_dir)
            
            # Temporarily override profile directory
            original_get_profile_dir = get_profile_dir
            import vision_ui.profiles
            vision_ui.profiles.get_profile_dir = lambda: temp_profile_dir
            
            try:
                saved_path = save_profile(profile)
                assert saved_path.exists()
                
                # Verify content
                with open(saved_path, 'r') as f:
                    data = json.load(f)
                assert data["name"] == "test_save"
                assert data["width_px"] == 800
                
            finally:
                vision_ui.profiles.get_profile_dir = original_get_profile_dir
    
    def test_save_profile_custom_filename(self):
        """Test saving profile with custom filename."""
        profile = Profile(
            name="test",
            width_px=800,
            height_px=600
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profile_dir = Path(temp_dir)
            
            # Temporarily override profile directory
            import vision_ui.profiles
            original_get_profile_dir = vision_ui.profiles.get_profile_dir
            vision_ui.profiles.get_profile_dir = lambda: temp_profile_dir
            
            try:
                saved_path = save_profile(profile, "custom_name.json")
                assert saved_path.name == "custom_name.json"
                
            finally:
                vision_ui.profiles.get_profile_dir = original_get_profile_dir


class TestParseProfilesFromCli:
    """Test CLI profile parsing."""
    
    def test_parse_single_profile(self):
        """Test parsing single profile name."""
        profiles = parse_profiles_from_cli("laptop")
        assert len(profiles) == 1
        assert profiles[0].name == "laptop"
    
    def test_parse_multiple_profiles(self):
        """Test parsing multiple profile names."""
        profiles = parse_profiles_from_cli("laptop,phone,slides")
        names = [p.name for p in profiles]
        assert names == ["laptop", "phone", "slides"]
    
    def test_parse_profiles_with_spaces(self):
        """Test parsing profiles with extra spaces."""
        profiles = parse_profiles_from_cli(" laptop , phone , slides ")
        names = [p.name for p in profiles]
        assert names == ["laptop", "phone", "slides"]
    
    def test_parse_empty_string(self):
        """Test parsing empty string returns empty list."""
        profiles = parse_profiles_from_cli("")
        assert profiles == []
    
    def test_parse_invalid_profile(self):
        """Test parsing invalid profile name raises error."""
        with pytest.raises(ValueError, match="Failed to load profile 'nonexistent'"):
            parse_profiles_from_cli("laptop,nonexistent")
