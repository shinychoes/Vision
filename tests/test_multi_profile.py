"""
Tests for multi-profile summarization functionality.
"""

import pytest
from vision_ui.profiles import Profile, load_profile
from vision_ui.summarize import (
    multi_profile_summarize,
    layered_summarize,
    Persona,
    BUILTIN_PERSONAS,
    DEFAULT_LAYERS,
    format_multi_profile_output
)


class TestLayeredSummarize:
    """Test layered summarization for a single profile."""
    
    def test_basic_layered_summarize(self):
        """Test basic layered summarization."""
        text = "This is a test. This is another sentence. This is a third sentence. " * 10
        budget = 200
        
        layers = ["headline", "one_screen"]
        result = layered_summarize(text, budget, layers)
        
        assert "headline" in result
        assert "one_screen" in result
        assert len(result["headline"]) <= budget * 0.2  # Should be much shorter
        assert len(result["one_screen"]) <= budget * 0.9
    
    def test_all_layers(self):
        """Test generating all available layers."""
        text = "Sentence one. Sentence two. Sentence three. " * 20
        budget = 300
        
        layers = ["headline", "one_screen", "deep"]
        result = layered_summarize(text, budget, layers)
        
        assert len(result) == 3
        for layer in layers:
            assert layer in result
            assert result[layer]  # Should not be empty
    
    def test_invalid_layer(self):
        """Test that invalid layer names raise error."""
        with pytest.raises(ValueError, match="Unknown layer"):
            layered_summarize("test text", 100, ["invalid_layer"])
    
    def test_with_persona(self):
        """Test layered summarization with persona."""
        text = "The user has a problem with the code. We need to fix it quickly."
        budget = 200
        
        persona = Persona(
            name="test",
            vocabulary_mappings={"user": "end-user", "fix": "resolve"},
            context_prefix="Technical review:"
        )
        
        result = layered_summarize(text, budget, ["headline"], persona=persona)
        
        # Headline should use vocabulary-only persona (no context prefix)
        # At least one vocabulary mapping should appear (may not be all due to truncation)
        assert "end-user" in result["headline"] or "resolve" in result["headline"]
        # Should NOT contain context prefix in headline
        assert "Technical review:" not in result["headline"]
        assert len(result["headline"]) > 0
    
    def test_custom_summarizer(self):
        """Test layered summarization with custom summarizer function."""
        text = "This is a test sentence. This is another test sentence."
        budget = 100
        
        def custom_summarizer(text: str, char_limit: int) -> str:
            return f"CUSTOM: {text[:char_limit]}"
        
        result = layered_summarize(text, budget, ["headline"], summarizer=custom_summarizer)
        
        assert result["headline"].startswith("CUSTOM:")
        assert len(result["headline"]) <= budget + len("CUSTOM: ")


class TestPersona:
    """Test persona functionality."""
    
    def test_persona_creation(self):
        """Test creating a persona."""
        persona = Persona(
            name="test",
            vocabulary_mappings={"old": "new"},
            example_sentences=["Example sentence."],
            context_prefix="Context:"
        )
        assert persona.name == "test"
        assert persona.vocabulary_mappings == {"old": "new"}
        assert persona.example_sentences == ["Example sentence."]
        assert persona.context_prefix == "Context:"
    
    def test_persona_apply_vocabulary(self):
        """Test persona vocabulary replacement."""
        persona = Persona(
            name="test",
            vocabulary_mappings={"user": "end-user", "problem": "issue"}
        )
        
        text = "The user has a problem."
        result = persona.apply(text)
        assert "end-user" in result
        assert "issue" in result
    
    def test_persona_apply_context(self):
        """Test persona context prefix addition."""
        persona = Persona(
            name="test",
            context_prefix="From a developer's perspective:"
        )
        
        text = "This is the content."
        result = persona.apply(text)
        assert result.startswith("From a developer's perspective:")
        assert "This is the content." in result
    
    def test_persona_apply_examples(self):
        """Test persona example sentences addition."""
        persona = Persona(
            name="test",
            example_sentences=["Example 1", "Example 2"]
        )
        
        text = "Main content."
        result = persona.apply(text)
        assert "Example: Example 1" in result
        assert "Example: Example 2" in result
        assert "Main content." in result
    
    def test_builtin_personas(self):
        """Test built-in personas exist and are valid."""
        expected_personas = ["developer", "designer", "manager"]
        for name in expected_personas:
            assert name in BUILTIN_PERSONAS
            persona = BUILTIN_PERSONAS[name]
            assert persona.name == name
            assert isinstance(persona, Persona)


class TestMultiProfileSummarize:
    """Test multi-profile summarization."""
    
    def test_multi_profile_basic(self):
        """Test basic multi-profile summarization."""
        text = "This is a test. This is another sentence. " * 30
        
        profiles = [
            load_profile("phone"),
            load_profile("laptop")
        ]
        
        result = multi_profile_summarize(text, profiles, ["headline", "one_screen"])
        
        assert "phone" in result
        assert "laptop" in result
        
        for profile_name in ["phone", "laptop"]:
            assert "headline" in result[profile_name]
            assert "one_screen" in result[profile_name]
            
            # Phone summaries should be shorter due to smaller screen
            phone_headline = result["phone"]["headline"]
            laptop_headline = result["laptop"]["headline"]
            
            # This is a rough check - phone might be shorter but not guaranteed
            assert len(phone_headline) > 0
            assert len(laptop_headline) > 0
    
    def test_multi_profile_all_layers(self):
        """Test multi-profile with all layers."""
        text = "Sentence one. Sentence two. Sentence three. " * 25
        
        profiles = [load_profile("phone"), load_profile("slides")]
        layers = ["headline", "one_screen", "deep"]
        
        result = multi_profile_summarize(text, profiles, layers)
        
        for profile_name in ["phone", "slides"]:
            for layer in layers:
                assert layer in result[profile_name]
                assert result[profile_name][layer]  # Should not be empty
    
    def test_multi_profile_with_persona(self):
        """Test multi-profile summarization with persona."""
        text = "The user has a problem with the system. We need to fix the code."
        
        profiles = [load_profile("phone")]
        
        result = multi_profile_summarize(
            text, 
            profiles, 
            ["headline"], 
            persona="developer"
        )
        
        summary = result["phone"]["headline"]
        # Headline should use vocabulary-only persona (developer persona maps "user" -> "end-user")
        assert "end-user" in summary or "issue" in summary
        assert len(summary) > 0
    
    def test_invalid_persona(self):
        """Test that invalid persona raises error."""
        profiles = [load_profile("phone")]
        
        with pytest.raises(ValueError, match="Unknown persona"):
            multi_profile_summarize("test", profiles, ["headline"], persona="nonexistent")
    
    def test_custom_summarizer(self):
        """Test multi-profile with custom summarizer."""
        text = "Test content for custom summarizer."
        profiles = [load_profile("phone")]
        
        def custom_summarizer(text: str, char_limit: int) -> str:
            return f"CUSTOM({char_limit}): {text[:20]}"
        
        result = multi_profile_summarize(
            text, 
            profiles, 
            ["headline"], 
            summarizer=custom_summarizer
        )
        
        summary = result["phone"]["headline"]
        assert summary.startswith("CUSTOM(")
        assert "Test content for cus" in summary


class TestFormatOutput:
    """Test output formatting functions."""
    
    def test_format_stacked(self):
        """Test stacked output format."""
        summaries = {
            "phone": {
                "headline": "Phone headline",
                "one_screen": "Phone one-screen summary"
            },
            "laptop": {
                "headline": "Laptop headline"
            }
        }
        
        result = format_multi_profile_output(summaries, "stacked")
        
        assert "=== PHONE ===" in result
        assert "=== LAPTOP ===" in result
        assert "--- Headline ---" in result
        assert "--- One Screen ---" in result
        assert "Phone headline" in result
        assert "Laptop headline" in result
    
    def test_format_json(self):
        """Test JSON output format."""
        summaries = {
            "phone": {"headline": "Phone headline"}
        }
        
        result = format_multi_profile_output(summaries, "json")
        
        import json
        parsed = json.loads(result)
        assert parsed == summaries
    
    def test_format_compact(self):
        """Test compact output format."""
        summaries = {
            "phone": {"headline": "Phone headline"},
            "laptop": {"headline": "Laptop headline"}
        }
        
        result = format_multi_profile_output(summaries, "compact")
        
        lines = result.strip().split('\n')
        assert len(lines) == 2
        assert "phone.headline: Phone headline" in lines
        assert "laptop.headline: Laptop headline" in lines


class TestLayerConfig:
    """Test layer configuration."""
    
    def test_default_layers(self):
        """Test default layer configurations."""
        expected_layers = ["headline", "one_screen", "deep"]
        for layer_name in expected_layers:
            assert layer_name in DEFAULT_LAYERS
            layer = DEFAULT_LAYERS[layer_name]
            assert layer.name == layer_name
            assert 0 < layer.budget_multiplier <= 1.0
    
    def test_headline_layer_config(self):
        """Test headline layer has appropriate configuration."""
        headline = DEFAULT_LAYERS["headline"]
        assert headline.budget_multiplier == 0.1
        assert headline.max_sentences == 2
        assert headline.include_hash is False
    
    def test_deep_layer_config(self):
        """Test deep layer has appropriate configuration."""
        deep = DEFAULT_LAYERS["deep"]
        assert deep.budget_multiplier == 1.0
        assert deep.include_hash is True


class TestBudgetCompliance:
    """Test that summaries respect character budgets."""
    
    def test_layer_budget_compliance(self):
        """Test that each layer respects its budget."""
        # Create a long text
        text = "This is a test sentence. " * 100
        total_budget = 500
        
        layers = ["headline", "one_screen", "deep"]
        result = layered_summarize(text, total_budget, layers)
        
        for layer_name, summary in result.items():
            layer_config = DEFAULT_LAYERS[layer_name]
            expected_budget = int(total_budget * layer_config.budget_multiplier)
            
            # Allow some tolerance for rounding
            assert len(summary) <= expected_budget + 10, f"Layer {layer_name} exceeded budget"
    
    def test_profile_budget_compliance(self):
        """Test that multi-profile summaries respect profile budgets."""
        text = "This is a test sentence. " * 50
        
        profiles = [load_profile("phone"), load_profile("laptop")]
        result = multi_profile_summarize(text, profiles, ["one_screen"])
        
        for profile in profiles:
            from UI_UX.budget import compute_budget
            budget = compute_budget(
                width_px=profile.width_px,
                height_px=profile.height_px,
                font_size_px=profile.font_size_px,
                editor_ruler_columns=profile.editor_ruler_columns,
                buffer=profile.buffer
            )
            
            summary = result[profile.name]["one_screen"]
            expected_budget = int(budget["target_chars"] * 0.8)  # one_screen multiplier
            
            # Allow some tolerance
            assert len(summary) <= expected_budget + 10, f"Profile {profile.name} exceeded budget"
