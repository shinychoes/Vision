"""
Command-line utilities for `vision-ui`.

The CLI is intentionally small: it wraps functions in `UI_UX.budget` to compute a one-screen
budget and perform a naive summary. `profile` and `report` commands are stubs for Phase 1.
"""
import argparse
import json
import sys
from typing import Optional

from UI_UX.budget import compute_budget, naive_summarize, pretty_budget
from .profiles import parse_profiles_from_cli
from .summarize import multi_profile_summarize, format_multi_profile_output, screenshot_aware_summarize
from .triage import display_triage_board, format_triage_output


def _read_text_from_file_or_stdin(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def cmd_budget(args: argparse.Namespace) -> None:
    if args.profile is not None:
        # Placeholder: profile-based lookup to be implemented later.
        raise NotImplementedError("Profile-based budgets are not implemented yet.")

    budget = compute_budget(
        width_px=args.width,
        height_px=args.height,
        font_size_px=args.font,
        editor_ruler_columns=args.ruler,
        buffer=args.buffer,
    )

    if args.json:
        print(json.dumps(budget, indent=2))
    else:
        # pretty_budget expects int-like values for presentation; coerce where safe
        # Only include the keys used by pretty_budget and ensure they are ints
        view = {k: int(budget[k]) for k in ("columns", "lines", "effective_columns", "char_budget", "target_chars") if k in budget}
        print(pretty_budget(view))


def cmd_summarize(args: argparse.Namespace) -> None:
    text = _read_text_from_file_or_stdin(args.file)

    if args.profile is not None:
        # Placeholder: profile-based lookup to be implemented later.
        raise NotImplementedError("Profile-based summarization is not implemented yet.")

    budget = compute_budget(
        width_px=args.width,
        height_px=args.height,
        font_size_px=args.font,
        editor_ruler_columns=args.ruler,
        buffer=args.buffer,
    )
    target_chars = int(budget["target_chars"])  # ensure integer for summarization
    summary = naive_summarize(text, target_chars)
    print(summary)


def cmd_profile(args: argparse.Namespace) -> None:
    # Skeleton only. You can later wire this to JSON/YAML profiles.
    raise NotImplementedError("Profile management commands are not implemented yet.")


def cmd_triage_compare(args: argparse.Namespace) -> None:
    """Handle triage comparison command with rich formatting."""
    # Parse profiles from CLI
    try:
        profiles = parse_profiles_from_cli(args.profiles)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Read input text
    try:
        text = _read_text_from_file_or_stdin(args.text)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Parse layers
    layers = [layer.strip() for layer in args.layers.split(',') if layer.strip()]
    
    # Generate summaries
    try:
        summaries = multi_profile_summarize(
            text=text,
            profiles=profiles,
            layers=layers,
            persona=args.persona
        )
    except Exception as e:
        print(f"Error generating summaries: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Display triage board
    display_triage_board(
        summaries=summaries,
        profiles=profiles,
        show_profile_info=args.show_profile_info,
        show_metadata=False
    )


def cmd_summarize_multi(args: argparse.Namespace) -> None:
    """Handle multi-profile summarization command."""
    text = _read_text_from_file_or_stdin(args.file)
    
    # Parse profiles from CLI
    try:
        profiles = parse_profiles_from_cli(args.profiles)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Parse layers
    layers = [layer.strip() for layer in args.layers.split(',') if layer.strip()]
    
    # Generate summaries
    try:
        summaries = multi_profile_summarize(
            text=text,
            profiles=profiles,
            layers=layers,
            persona=args.persona
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Format output
    formatted_output = format_multi_profile_output(summaries, args.format)
    print(formatted_output)


def cmd_summarize_screenshot(args: argparse.Namespace) -> None:
    """Handle screenshot-aware summarization command."""
    # Parse profiles from CLI
    try:
        profiles = parse_profiles_from_cli(args.profiles)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Parse layers
    layers = [layer.strip() for layer in args.layers.split(',') if layer.strip()]
    
    # Generate summaries from screenshot
    try:
        summaries = screenshot_aware_summarize(
            image_path=args.image,
            profiles=profiles,
            layers=layers,
            persona=args.persona
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract OCR metadata for display
    ocr_metadata = summaries.pop('_ocr_metadata', {})
    
    # Choose output format
    if args.format == "triage":
        # Display triage board format
        display_triage_board(
            summaries=summaries,
            profiles=profiles,
            show_profile_info=args.show_profile_info,
            show_metadata=args.verbose,
            ocr_metadata=ocr_metadata
        )
    else:
        # Use existing formatted output
        formatted_output = format_multi_profile_output(summaries, args.format)
        print(formatted_output)
        
        # Show OCR metadata if requested
        if args.verbose:
            print("\n=== OCR METADATA ===")
            print(f"Text density: {ocr_metadata.get('text_density', 'N/A'):.2%}")
            print(f"Regions found: {ocr_metadata.get('regions_found', 'N/A')}")
            print(f"Preprocessing applied: {', '.join(ocr_metadata.get('preprocessing_applied', []))}")
            print(f"Image size: {ocr_metadata.get('image_size', 'N/A')}")


def cmd_report(args: argparse.Namespace) -> None:
    # Skeleton only. You can later generate HTML/CSV/JSON multi-profile reports here.
    raise NotImplementedError("Report generation is not implemented yet.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vision-ui",
        description="Screen-aware text and token budgeting utilities.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # budget
    p_budget = sub.add_parser(
        "budget",
        help="Compute a one-screen budget for a given window size.",
    )
    p_budget.add_argument("--width", type=int, required=True, help="Window width in pixels.")
    p_budget.add_argument("--height", type=int, required=True, help="Window height in pixels.")
    p_budget.add_argument("--font", type=int, default=14, help="Font size in pixels (default: 14).")
    p_budget.add_argument(
        "--ruler",
        type=int,
        default=80,
        help="Editor ruler columns (default: 80).",
    )
    p_budget.add_argument(
        "--buffer",
        type=float,
        default=0.9,
        help="Fraction of char budget to target (default: 0.9).",
    )
    p_budget.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Optional profile name or JSON path (not implemented yet).",
    )
    p_budget.add_argument(
        "--json",
        action="store_true",
        help="Output full budget as JSON instead of a one-line summary.",
    )
    p_budget.set_defaults(func=cmd_budget)

    # summarize
    p_sum = sub.add_parser(
        "summarize",
        help="Produce a one-screen summary for a text file or stdin.",
    )
    p_sum.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to input text file, or '-' to read from stdin.",
    )
    p_sum.add_argument("--width", type=int, required=True, help="Window width in pixels.")
    p_sum.add_argument("--height", type=int, required=True, help="Window height in pixels.")
    p_sum.add_argument("--font", type=int, default=14, help="Font size in pixels (default: 14).")
    p_sum.add_argument(
        "--ruler",
        type=int,
        default=80,
        help="Editor ruler columns (default: 80).",
    )
    p_sum.add_argument(
        "--buffer",
        type=float,
        default=0.9,
        help="Fraction of char budget to target (default: 0.9).",
    )
    p_sum.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Optional profile name or JSON path (not implemented yet).",
    )
    p_sum.set_defaults(func=cmd_summarize)

    # summarize-multi
    p_sum_multi = sub.add_parser(
        "summarize-multi",
        help="Generate multi-profile, multi-layer summaries for a text file or stdin.",
    )
    p_sum_multi.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to input text file, or '-' to read from stdin.",
    )
    p_sum_multi.add_argument(
        "--profiles",
        type=str,
        required=True,
        help="Comma-separated profile names (e.g., 'phone,laptop,slides').",
    )
    p_sum_multi.add_argument(
        "--layers",
        type=str,
        default="headline,one_screen,deep",
        help="Comma-separated layer names (default: 'headline,one_screen,deep').",
    )
    p_sum_multi.add_argument(
        "--persona",
        type=str,
        default=None,
        help="Optional persona name (developer, designer, manager).",
    )
    p_sum_multi.add_argument(
        "--format",
        type=str,
        default="stacked",
        choices=["stacked", "json", "compact"],
        help="Output format (default: stacked).",
    )
    p_sum_multi.set_defaults(func=cmd_summarize_multi)

    # triage-compare
    p_triage = sub.add_parser(
        "triage-compare",
        help="Display multi-profile summaries in rich triage board format.",
    )
    p_triage.add_argument(
        "--text",
        type=str,
        required=True,
        help="Text file path or '-' for stdin to summarize.",
    )
    p_triage.add_argument(
        "--profiles",
        type=str,
        required=True,
        help="Comma-separated profile names (e.g., 'phone,laptop,slides').",
    )
    p_triage.add_argument(
        "--layers",
        type=str,
        default="headline,one_screen,deep",
        help="Comma-separated layer names (default: 'headline,one_screen,deep').",
    )
    p_triage.add_argument(
        "--persona",
        type=str,
        default=None,
        help="Optional persona name (developer, designer, manager).",
    )
    p_triage.add_argument(
        "--show-profile-info",
        action="store_true",
        help="Display detailed profile information.",
    )
    p_triage.set_defaults(func=cmd_triage_compare)

    # summarize-screenshot
    p_sum_screenshot = sub.add_parser(
        "summarize-screenshot",
        help="Generate multi-profile summaries from a screenshot using OCR.",
    )
    p_sum_screenshot.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the screenshot image file.",
    )
    p_sum_screenshot.add_argument(
        "--profiles",
        type=str,
        required=True,
        help="Comma-separated profile names (e.g., 'phone,laptop,slides').",
    )
    p_sum_screenshot.add_argument(
        "--layers",
        type=str,
        default="headline,one_screen",
        help="Comma-separated layer names (default: 'headline,one_screen').",
    )
    p_sum_screenshot.add_argument(
        "--persona",
        type=str,
        default=None,
        help="Optional persona name (developer, designer, manager).",
    )
    p_sum_screenshot.add_argument(
        "--format",
        type=str,
        default="stacked",
        choices=["stacked", "json", "compact", "triage"],
        help="Output format (default: stacked).",
    )
    p_sum_screenshot.add_argument(
        "--verbose",
        action="store_true",
        help="Show OCR metadata and processing information.",
    )
    p_sum_screenshot.add_argument(
        "--show-profile-info",
        action="store_true",
        help="Display detailed profile information (only with triage format).",
    )
    p_sum_screenshot.set_defaults(func=cmd_summarize_screenshot)

    # profile (stub)
    p_profile = sub.add_parser(
        "profile",
        help="Manage screen profiles (stub: to be implemented).",
    )
    p_profile.set_defaults(func=cmd_profile)

    # report (stub)
    p_report = sub.add_parser(
        "report",
        help="Generate multi-profile reports (stub: to be implemented).",
    )
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.error("No command specified.")
    func(args)


if __name__ == "__main__":
    main()
