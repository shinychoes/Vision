"""
vision_ui.summarize

Multi-profile, multi-layer summarization building on UI_UX.budget.
Supports layered summaries (headline, one_screen, deep) across device profiles.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from .profiles import Profile, load_profile, parse_profiles_from_cli
from UI_UX.budget import compute_budget, naive_summarize
from .ocr import OCRExtractor, ScreenshotAnalyzer, OCRResult


@dataclass
class LayerConfig:
    """Configuration for a summary layer."""
    name: str
    budget_multiplier: float  # Fraction of target_chars to use
    max_sentences: Optional[int] = None
    include_hash: bool = False  # For deep layer - include content hash


# Default layer configurations
DEFAULT_LAYERS: Dict[str, LayerConfig] = {
    "headline": LayerConfig(
        name="headline",
        budget_multiplier=0.1,  # 10% of budget
        max_sentences=2
    ),
    "one_screen": LayerConfig(
        name="one_screen", 
        budget_multiplier=0.8,  # 80% of budget
        max_sentences=None
    ),
    "deep": LayerConfig(
        name="deep",
        budget_multiplier=1.0,  # Full budget
        include_hash=True
    )
}


@dataclass
class Persona:
    """Persona adapter for text transformation before summarization."""
    name: str
    vocabulary_mappings: Optional[Dict[str, str]] = None
    example_sentences: Optional[List[str]] = None
    context_prefix: Optional[str] = None
    
    examples_location: str = "append"  # one of: 'prepend', 'append', 'none'

    def examples_text(self) -> str:
        """Return the persona example lines as a single text block."""
        if not self.example_sentences:
            return ""
        return "\n".join(f"Example: {example}" for example in self.example_sentences)

    def context_text(self) -> str:
        return self.context_prefix or ""

    def apply(self, text: str, include_examples: bool = True, include_context: bool = True) -> str:
        """Apply persona transformations to text."""
        transformed = text
        
        # Apply vocabulary mappings first (before adding other content)
        if self.vocabulary_mappings:
            for old_word, new_word in self.vocabulary_mappings.items():
                transformed = transformed.replace(old_word, new_word)
        
        # Add context prefix if specified
        if include_context and self.context_prefix:
            transformed = f"{self.context_prefix}\n\n{transformed}"

        # Add example sentences if specified
        if include_examples and self.example_sentences and self.examples_location == "prepend":
            examples = self.examples_text()
            transformed = f"{examples}\n\n{transformed}"

        if include_examples and self.example_sentences and self.examples_location == "append":
            examples = self.examples_text()
            transformed = f"{transformed}\n\n{examples}"
        
        return transformed


# Built-in personas
BUILTIN_PERSONAS: Dict[str, Persona] = {
    "developer": Persona(
        name="developer",
        vocabulary_mappings={"user": "end-user", "problem": "issue", "fix": "resolve"},
        example_sentences=["Focus on technical implementation details.", "Consider API design patterns."],
        context_prefix="As a software developer reviewing this content:"
    ),
    "designer": Persona(
        name="designer", 
        vocabulary_mappings={"functionality": "user experience", "code": "interface"},
        example_sentences=["Consider visual hierarchy and layout.", "Focus on user interaction patterns."],
        context_prefix="From a UX/UI design perspective:"
    ),
    "manager": Persona(
        name="manager",
        vocabulary_mappings={"technical": "strategic", "implementation": "execution"},
        example_sentences=["Consider business impact and timeline.", "Focus on resource allocation."],
        context_prefix="From a project management viewpoint:"
    )
}


def _calculate_persona_overhead(persona: Persona) -> int:
    """Calculate the character overhead added by persona transformation."""
    overhead = 0
    
    # Context prefix overhead
    if persona.context_prefix:
        overhead += len(persona.context_prefix) + 2  # +2 for newlines
    
    # Example sentences overhead
    if persona.example_sentences:
        for example in persona.example_sentences:
            overhead += len(f"Example: {example}") + 1  # +1 for newline
    
    # Add separators if both exist
    if persona.context_prefix and persona.example_sentences:
        overhead += 2  # Extra newlines between sections
    
    return overhead


def layered_summarize(
    text: str,
    char_budget: int,
    layers: List[str],
    persona: Optional[Persona] = None,
    summarizer: Optional[Callable[[str, int], str]] = None
) -> Dict[str, str]:
    """
    Generate layered summaries for a single character budget.
    
    Args:
        text: Input text to summarize
        char_budget: Available character budget
        layers: List of layer names to generate
        persona: Optional persona adapter
        summarizer: Optional custom summarizer function
        
    Returns:
        Dictionary mapping layer names to summaries
    """
    if summarizer is None:
        summarizer = naive_summarize
    
    results = {}
    
    for layer_name in layers:
        if layer_name not in DEFAULT_LAYERS:
            raise ValueError(f"Unknown layer: {layer_name}")
        
        layer_config = DEFAULT_LAYERS[layer_name]
        layer_budget = int(char_budget * layer_config.budget_multiplier)
        
        # Calculate persona overhead if persona is specified
        persona_overhead = 0
        if persona:
            persona_overhead = _calculate_persona_overhead(persona)
        
        # Calculate hash overhead for deep layer
        hash_overhead = 15 if layer_config.include_hash else 0  # "[hash:xxxxxxxx] "
        
        # Adjust budget for overheads
        effective_budget = layer_budget
        if persona and layer_name == "headline":
            # Headline layer always uses vocabulary-only persona for conciseness
            if persona.vocabulary_mappings:
                transformed_text = text
                for old_word, new_word in persona.vocabulary_mappings.items():
                    transformed_text = transformed_text.replace(old_word, new_word)
                summary = summarizer(transformed_text, effective_budget - hash_overhead)
            else:
                summary = summarizer(text, effective_budget - hash_overhead)
        elif persona and persona.examples_location == "append":
            # Append persona examples after generating the summary; do not make examples consume
            # the text budget so headlines remain concise and one_screen/detailed layers can include
            # persona material as an addendum.
            effective_budget = layer_budget - hash_overhead
            summary = summarizer(text, effective_budget)
            # Append examples/context as a postfix if present
            examples = persona.examples_text()
            context = persona.context_text()
            postfix_items = []
            if context:
                postfix_items.append(context)
            if examples:
                postfix_items.append(examples)
            if postfix_items:
                summary = summary.strip() + "\n\n" + "\n\n".join(postfix_items)
        elif persona and layer_budget > persona_overhead + hash_overhead + 20:  # Keep at least 20 chars for content
            # Other layers use full persona if budget permits
            effective_budget = layer_budget - persona_overhead - hash_overhead
            # Apply persona transformation for summarization (includes examples/context)
            persona_text = persona.apply(text)
            summary = summarizer(persona_text, effective_budget)
        else:
            # No persona or insufficient budget - summarize original text
            summary = summarizer(text, effective_budget - hash_overhead)
        
        # Add hash for deep layer if requested
        if layer_config.include_hash:
            import hashlib
            content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            summary = f"[hash:{content_hash}] {summary}"
        
        results[layer_name] = summary
    
    return results


def multi_profile_summarize(
    text: str,
    profiles: List[Profile],
    layers: List[str] = ['headline', 'one_screen', 'deep'],
    persona: Optional[str] = None,
    summarizer: Optional[Callable[[str, int], str]] = None
) -> Dict[str, Dict[str, str]]:
    """
    Generate multi-profile, multi-layer summaries.
    
    Args:
        text: Input text to summarize
        profiles: List of Profile objects
        layers: List of layer names to generate for each profile
        persona: Optional persona name from BUILTIN_PERSONAS
        summarizer: Optional custom summarizer function
        
    Returns:
        Nested dictionary: {profile_name: {layer_name: summary}}
    """
    if summarizer is None:
        summarizer = naive_summarize
    
    persona_obj = None
    if persona:
        if persona not in BUILTIN_PERSONAS:
            raise ValueError(f"Unknown persona: {persona}. Available: {list(BUILTIN_PERSONAS.keys())}")
        persona_obj = BUILTIN_PERSONAS[persona]
    
    results = {}
    
    for profile in profiles:
        # Compute budget for this profile
        budget = compute_budget(
            width_px=profile.width_px,
            height_px=profile.height_px,
            font_size_px=profile.font_size_px,
            editor_ruler_columns=profile.editor_ruler_columns,
            buffer=profile.buffer
        )
        
        target_chars = budget["target_chars"]
        
        # Generate layered summaries for this profile
        profile_summaries = layered_summarize(
            text=text,
            char_budget=target_chars,
            layers=layers,
            persona=persona_obj,
            summarizer=summarizer
        )
        
        results[profile.name] = profile_summaries
    
    return results


def format_multi_profile_output(
    summaries: Dict[str, Dict[str, str]],
    format_type: str = "stacked"
) -> str:
    """
    Format multi-profile summaries for display.
    
    Args:
        summaries: Output from multi_profile_summarize
        format_type: "stacked", "json", or "compact"
        
    Returns:
        Formatted string
    """
    if format_type == "json":
        import json
        return json.dumps(summaries, indent=2)
    
    elif format_type == "compact":
        lines = []
        for profile_name, profile_summaries in summaries.items():
            for layer_name, summary in profile_summaries.items():
                lines.append(f"{profile_name}.{layer_name}: {summary}")
        return "\n".join(lines)
    
    else:  # stacked (default)
        lines = []
        for profile_name, profile_summaries in summaries.items():
            lines.append(f"=== {profile_name.upper()} ===")
            for layer_name, summary in profile_summaries.items():
                lines.append(f"--- {layer_name.title().replace('_', ' ')} ---")
                lines.append(summary.strip())
                lines.append("")  # Empty line between layers
            lines.append("")  # Empty line between profiles
        return "\n".join(lines).strip()


def screenshot_aware_summarize(
    image_path: str,
    profiles: List[Profile],
    layers: List[str] = ['headline', 'one_screen'],
    persona: Optional[str] = None,
    summarizer: Optional[Callable[[str, int], str]] = None,
    ocr_analyzer: Optional[ScreenshotAnalyzer] = None
) -> Dict[str, Dict[str, str]]:
    """
    Generate multi-profile summaries from a screenshot using OCR.
    
    Args:
        image_path: Path to the screenshot image file
        profiles: List of Profile objects for target devices
        layers: List of layer names to generate
        persona: Optional persona name from BUILTIN_PERSONAS
        summarizer: Optional custom summarizer function
        ocr_analyzer: Optional ScreenshotAnalyzer instance
        
    Returns:
        Nested dictionary: {profile_name: {layer_name: summary}}
    """
    # Initialize OCR analyzer
    if ocr_analyzer is None:
        ocr_analyzer = ScreenshotAnalyzer()
    
    # Extract text from screenshot
    try:
        ocr_result = ocr_analyzer.analyze_screenshot(image_path)
    except Exception as e:
        raise RuntimeError(f"Failed to analyze screenshot: {e}")
    
    if not ocr_result.full_text.strip():
        raise ValueError("No text found in screenshot")
    
    # Extract structured regions for layout-aware processing
    regions_by_type = ocr_analyzer.extract_ui_regions(ocr_result)
    
    # Estimate text density for budget adjustment
    text_density = ocr_analyzer.estimate_text_density(ocr_result)
    
    # Adjust profiles based on screenshot content
    adjusted_profiles = _adjust_profiles_for_screenshot(profiles, ocr_result, text_density)
    
    # Generate summaries using extracted text
    summaries = multi_profile_summarize(
        text=ocr_result.full_text,
        profiles=adjusted_profiles,
        layers=layers,
        persona=persona,
        summarizer=summarizer
    )
    
    # Add OCR metadata to summaries
    summaries['_ocr_metadata'] = {
        'text_density': text_density,
        'regions_found': len(ocr_result.regions),
        'preprocessing_applied': ocr_result.preprocessing_applied,
        'image_size': ocr_result.image_info['size']
    }
    
    return summaries


def _adjust_profiles_for_screenshot(
    profiles: List[Profile], 
    ocr_result: OCRResult, 
    text_density: float
) -> List[Profile]:
    """
    Adjust profile budgets based on screenshot content characteristics.
    
    Args:
        profiles: Original list of Profile objects
        ocr_result: OCR extraction result
        text_density: Estimated text density (0.0 to 1.0)
        
    Returns:
        List of adjusted Profile objects
    """
    adjusted_profiles = []
    
    for profile in profiles:
        # Create a copy of the profile
        adjusted_profile = Profile(
            name=profile.name,
            width_px=profile.width_px,
            height_px=profile.height_px,
            font_size_px=profile.font_size_px,
            editor_ruler_columns=profile.editor_ruler_columns,
            buffer=profile.buffer,
            image_regions=profile.image_regions
        )
        
        # Adjust buffer based on text density
        # Higher text density = more conservative budget
        if text_density > 0.7:
            adjusted_profile.buffer = max(0.7, profile.buffer - 0.1)  # Reduce buffer for dense content
        elif text_density < 0.3:
            adjusted_profile.buffer = min(0.95, profile.buffer + 0.05)  # Increase buffer for sparse content
        
        adjusted_profiles.append(adjusted_profile)
    
    return adjusted_profiles


def extract_text_from_screenshot(image_path: str, preprocess: bool = True) -> str:
    """
    Convenience function to extract text from a screenshot.
    
    Args:
        image_path: Path to the screenshot image file
        preprocess: Whether to apply image preprocessing
        
    Returns:
        Extracted text as string
    """
    analyzer = ScreenshotAnalyzer()
    ocr_result = analyzer.analyze_screenshot(image_path)
    return ocr_result.full_text


def summarize_screenshot(
    image_path: str,
    profile_name: str = "laptop",
    layer: str = "one_screen",
    persona: Optional[str] = None
) -> str:
    """
    Convenience function to summarize a screenshot for a single profile and layer.
    
    Args:
        image_path: Path to the screenshot image file
        profile_name: Name of the target profile
        layer: Name of the summary layer
        persona: Optional persona name
        
    Returns:
        Generated summary as string
    """
    profile = load_profile(profile_name)
    summaries = screenshot_aware_summarize(
        image_path=image_path,
        profiles=[profile],
        layers=[layer],
        persona=persona
    )
    
    return summaries[profile.name][layer]
