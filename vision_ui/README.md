# Vision UI - Multi-Profile Summarization

Vision UI provides screen-aware text summarization with multi-device support and persona adaptation. Built on top of the `UI_UX` budget computation system.

## Features

- **Multi-device profiles**: Generate summaries optimized for different screen sizes (phone, laptop, slides, tweet)
- **Layered summaries**: Create headline, one-screen, and deep summaries with different detail levels
- **Persona adaptation**: Transform content for different audiences (developer, designer, manager)
- **Budget compliance**: Automatically respect character limits based on screen dimensions
- **CLI integration**: Command-line interface for programmatic and human use

## Quick Start

### Installation

```bash
# From the repository root
pip install -e .
```

### Basic Usage

```bash
# Generate multi-profile summaries
vision-ui summarize-multi --file README.md --profiles phone,laptop

# With persona and specific layers
vision-ui summarize-multi --file doc.txt --profiles slides --layers headline --persona developer

# JSON output for programmatic use
vision-ui summarize-multi --file report.txt --profiles phone,laptop,slides --format json
```

### Python API

```python
from vision_ui.profiles import load_profile, parse_profiles_from_cli
from vision_ui.summarize import multi_profile_summarize, format_multi_profile_output

# Load profiles
profiles = parse_profiles_from_cli("phone,laptop")

# Generate summaries
text = "Your document content here..."
summaries = multi_profile_summarize(text, profiles, ["headline", "one_screen"])

# Format output
output = format_multi_profile_output(summaries, "stacked")
print(output)
```

## Device Profiles

Built-in profiles are optimized for common device types:

| Profile | Dimensions | Font Size | Use Case |
|---------|------------|-----------|----------|
| `laptop` | 1920×1080 | 14px | Standard desktop viewing |
| `phone` | 375×667 | 12px | Mobile devices |
| `slides` | 1024×768 | 18px | Presentations |
| `tweet` | 280×400 | 14px | Social media posts |

### Custom Profiles

Create custom profiles as JSON files:

```json
{
  "name": "tablet",
  "width_px": 768,
  "height_px": 1024,
  "font_size_px": 14,
  "editor_ruler_columns": 60,
  "buffer": 0.9
}
```

Save to `vision_ui/profiles/tablet.json` and use with `--profiles tablet`.

## Summary Layers

- **headline** (10% of budget): Very short, 1-2 sentences
- **one_screen** (80% of budget): Fits on one screen of the target device
- **deep** (100% of budget): Full summary with content hash for reference

## Personas

Personas adapt content for different audiences:

### Developer
- Vocabulary: "user" → "end-user", "problem" → "issue", "fix" → "resolve"
- Focus: Technical implementation details, API design patterns
- Context: "As a software developer reviewing this content:"

### Designer  
- Vocabulary: "functionality" → "user experience", "code" → "interface"
- Focus: Visual hierarchy, user interaction patterns
- Context: "From a UX/UI design perspective:"

### Manager
- Vocabulary: "technical" → "strategic", "implementation" → "execution"  
- Focus: Business impact, resource allocation, timelines
- Context: "From a project management viewpoint:"

## Output Formats

### Stacked (default)
Human-readable with clear section headers:

```
=== PHONE ===
--- Headline ---
Brief summary here...

--- One Screen ---
Longer summary that fits on phone screen...

=== LAPTOP ===
--- Headline ---
Summary optimized for laptop...
```

### JSON
Programmatic consumption:

```json
{
  "phone": {
    "headline": "Brief summary...",
    "one_screen": "Longer summary..."
  },
  "laptop": {
    "headline": "Laptop summary...",
    "one_screen": "Laptop one-screen summary..."
  }
}
```

### Compact
Single-line format for logs:

```
phone.headline: Brief summary...
phone.one_screen: Longer summary...
laptop.headline: Laptop summary...
```

## CLI Reference

### summarize-multi

Generate multi-profile, multi-layer summaries.

```bash
vision-ui summarize-multi [OPTIONS]

Required:
  --file FILE           Input text file or '-' for stdin
  --profiles PROFILES   Comma-separated profile names

Optional:
  --layers LAYERS       Comma-separated layers (default: headline,one_screen,deep)
  --persona PERSONA     Persona name (developer, designer, manager)
  --format FORMAT       Output format: stacked, json, compact (default: stacked)
```

### Examples

```bash
# Basic multi-profile summary
vision-ui summarize-multi --file README.md --profiles phone,laptop

# Headline only with developer persona
vision-ui summarize-multi --file spec.md --profiles phone --layers headline --persona developer

# All profiles and layers, JSON output
vision-ui summarize-multi --file report.txt --profiles phone,laptop,slides --format json

# Read from stdin
cat document.txt | vision-ui summarize-multi --file - --profiles laptop --format compact
```

## Budget Compliance

The system automatically calculates character budgets based on:

- Screen dimensions (width × height in pixels)
- Font size and line height
- Editor ruler columns (text wrapping)
- Buffer factor (default 90% of available space)

Summaries are guaranteed to stay within calculated budgets for each profile and layer.

## Error Handling

Common errors and solutions:

- **Profile not found**: Check profile name spelling or create custom JSON profile
- **Invalid persona**: Available personas: developer, designer, manager  
- **File not found**: Use absolute paths or ensure file exists in current directory
- **Budget exceeded**: Should not happen - system enforces budget constraints

## Development

### Running Tests

```bash
# From repository root
pytest tests/ -v
```

### Project Structure

```
vision_ui/
├── profiles.py          # Profile management
├── summarize.py         # Multi-profile summarization
├── cli.py              # Command-line interface
├── tests/              # Unit tests
└── README.md           # This file
```

## Phase 2 & Future Plans

- **Screenshot-aware summarization**: OCR integration and layout-aware budgets
- **Triage board UI**: Web interface for multi-profile review
- **Advanced personas**: Configurable persona files and budget-aware adaptation
- **Image slotting**: Automatic image placement within summaries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See LICENSE file for details.
