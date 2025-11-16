"""
vision_ui.triage

Rich formatting and triage board functionality for multi-profile summarization.
Provides side-by-side comparison, colored output, and enhanced display options.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.align import Align

from .summarize import DEFAULT_LAYERS
from .profiles import Profile


class TriageBoard:
    """Enhanced triage board display for multi-profile summaries."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize triage board with optional custom console."""
        self.console = console or Console()
    
    def display_comparison(
        self, 
        summaries: Dict[str, Dict[str, str]], 
        profiles: List[Profile],
        show_metadata: bool = False,
        ocr_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Display summaries in side-by-side comparison format.
        
        Args:
            summaries: Multi-profile summary results
            profiles: List of profile objects used
            show_metadata: Whether to display OCR metadata
            ocr_metadata: Optional OCR processing metadata
        """
        # Remove metadata from summaries for display
        display_summaries = {k: v for k, v in summaries.items() if not k.startswith('_')}
        
        # Create main title
        title = "🎯 MULTI-PROFILE TRIAGE BOARD"
        self.console.print(Align.center(Text(title, style="bold blue")))
        self.console.print()
        
        # Display OCR metadata if available
        if show_metadata and ocr_metadata:
            self._display_ocr_metadata(ocr_metadata)
        
        # Get all layers present in summaries
        all_layers = set()
        for profile_summaries in display_summaries.values():
            all_layers.update(profile_summaries.keys())
        
        # Sort layers by default order
        sorted_layers = sorted(all_layers, key=lambda x: self._get_layer_order(x))
        
        # Display each layer as a comparison table
        for layer in sorted_layers:
            self._display_layer_comparison(display_summaries, profiles, layer)
            self.console.print()
    
    def _display_layer_comparison(
        self, 
        summaries: Dict[str, Dict[str, str]], 
        profiles: List[Profile], 
        layer: str
    ) -> None:
        """Display comparison for a specific layer."""
        layer_config = DEFAULT_LAYERS.get(layer)
        if not layer_config:
            return
        
        # Create table for this layer
        table = Table(
            title=f"📱 {layer_config.name.title().replace('_', ' ')} Layer",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        # Add columns
        table.add_column("Profile", style="bold", width=12)
        table.add_column("Device", style="dim", width=15)
        table.add_column("Screen", style="dim", width=12)
        table.add_column("Summary", style="white", width=50)
        table.add_column("Length", justify="right", style="dim", width=8)
        
        # Add rows for each profile
        for profile in profiles:
            profile_name = profile.name
            profile_summary = summaries.get(profile_name, {})
            summary = profile_summary.get(layer, "N/A")
            
            # Truncate very long summaries for display
            if len(summary) > 200:
                display_summary = summary[:197] + "..."
            else:
                display_summary = summary
            
            # Color code based on summary length
            length_style = self._get_length_style(len(summary))
            
            table.add_row(
                profile_name.upper(),
                self._get_device_type(profile),
                f"{profile.width_px}×{profile.height_px}",
                display_summary,
                f"[{length_style}]{len(summary)}[/{length_style}]"
            )
        
        self.console.print(table)
    
    def _display_ocr_metadata(self, metadata: Dict[str, Any]) -> None:
        """Display OCR processing metadata."""
        metadata_table = Table(
            title="🔍 OCR Processing Metadata",
            box=box.ROUNDED,
            show_header=False
        )
        
        metadata_table.add_column("Property", style="bold cyan")
        metadata_table.add_column("Value", style="white")
        
        # Format metadata values
        text_density = metadata.get('text_density', 0)
        regions_found = metadata.get('regions_found', 0)
        preprocessing = metadata.get('preprocessing_applied', [])
        image_size = metadata.get('image_size', (0, 0))
        
        metadata_table.add_row(
            "Text Density",
            f"{text_density:.1%}" if text_density else "N/A"
        )
        metadata_table.add_row(
            "Regions Found", 
            str(regions_found)
        )
        metadata_table.add_row(
            "Preprocessing",
            ", ".join(preprocessing) if preprocessing else "None"
        )
        metadata_table.add_row(
            "Image Size",
            f"{image_size[0]} × {image_size[1]}" if image_size != (0, 0) else "Unknown"
        )
        
        self.console.print(metadata_table)
        self.console.print()
    
    def display_profile_info(self, profiles: List[Profile]) -> None:
        """Display detailed profile information."""
        table = Table(
            title="📊 Device Profile Information",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Profile", style="bold", width=10)
        table.add_column("Resolution", style="white", width=12)
        table.add_column("Font Size", style="white", width=10)
        table.add_column("Columns", style="white", width=8)
        table.add_column("Buffer", style="white", width=8)
        table.add_column("Budget", style="green", width=12)
        
        for profile in profiles:
            # Calculate budget for this profile
            from UI_UX.budget import compute_budget
            budget = compute_budget(
                width_px=profile.width_px,
                height_px=profile.height_px,
                font_size_px=profile.font_size_px,
                editor_ruler_columns=profile.editor_ruler_columns,
                buffer=profile.buffer
            )
            
            table.add_row(
                profile.name.upper(),
                f"{profile.width_px}×{profile.height_px}",
                f"{profile.font_size_px}px",
                str(profile.editor_ruler_columns),
                f"{profile.buffer:.1%}",
                f"{budget['target_chars']:,} chars"
            )
        
        self.console.print(table)
        self.console.print()
    
    def _get_layer_order(self, layer_name: str) -> int:
        """Get display order for layers."""
        order = ["headline", "one_screen", "deep"]
        try:
            return order.index(layer_name)
        except ValueError:
            return 999
    
    def _get_device_type(self, profile: Profile) -> str:
        """Get human-readable device type from profile."""
        name = profile.name.lower()
        if name == "phone":
            return "📱 Mobile"
        elif name == "laptop":
            return "💻 Laptop"
        elif name == "slides":
            return "📽️ Presentation"
        elif name == "tweet":
            return "🐦 Social"
        else:
            return "🖥️ Display"
    
    def _get_length_style(self, length: int) -> str:
        """Get color style based on summary length."""
        if length < 50:
            return "green"  # Very concise
        elif length < 150:
            return "yellow"  # Moderate
        elif length < 300:
            return "orange"  # Long
        else:
            return "red"  # Very long


def format_triage_output(
    summaries: Dict[str, Dict[str, str]], 
    profiles: List[Profile],
    show_profile_info: bool = False,
    show_metadata: bool = False,
    ocr_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format summaries for triage board display.
    
    Args:
        summaries: Multi-profile summary results
        profiles: List of profile objects used
        show_profile_info: Whether to show profile information
        show_metadata: Whether to show OCR metadata
        ocr_metadata: Optional OCR processing metadata
        
    Returns:
        Formatted string for console output
    """
    board = TriageBoard()
    
    # Capture console output
    from io import StringIO
    string_io = StringIO()
    
    # Create console with string output
    console = Console(file=string_io, width=120)
    board.console = console
    
    # Display profile info if requested
    if show_profile_info:
        board.display_profile_info(profiles)
    
    # Display comparison
    board.display_comparison(summaries, profiles, show_metadata, ocr_metadata)
    
    return string_io.getvalue()


def display_triage_board(
    summaries: Dict[str, Dict[str, str]], 
    profiles: List[Profile],
    show_profile_info: bool = False,
    show_metadata: bool = False,
    ocr_metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Display triage board directly to console.
    
    Args:
        summaries: Multi-profile summary results
        profiles: List of profile objects used
        show_profile_info: Whether to show profile information
        show_metadata: Whether to show OCR metadata
        ocr_metadata: Optional OCR processing metadata
    """
    board = TriageBoard()
    
    # Display profile info if requested
    if show_profile_info:
        board.display_profile_info(profiles)
    
    # Display comparison
    board.display_comparison(summaries, profiles, show_metadata, ocr_metadata)
