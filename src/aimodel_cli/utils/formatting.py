"""Utility functions for formatting output."""

import sys
from typing import Any, Dict, List
from rich.console import Console
from rich.table import Table
from rich.text import Text

def safe_str(text: str) -> str:
    """Safely encode string for console output."""
    if sys.platform == "win32":
        # Replace problematic characters for Windows console
        return text.encode('ascii', 'replace').decode('ascii')
    return text


def format_model_info(model_data: Dict[str, Any]) -> str:
    """Format model information for display.
    
    Args:
        model_data: Model data from API
        
    Returns:
        Formatted string
    """
    if not model_data.get('items'):
        return "No model data available"
    
    model = model_data['items'][0]
    versions = model.get('modelVersions', [])
    
    lines = []
    lines.append(f"Name: {safe_str(model.get('name', 'Unknown'))}")
    lines.append(f"ID: {model.get('id', 'Unknown')}")
    lines.append(f"Type: {safe_str(model.get('type', 'Unknown'))}")
    lines.append(f"NSFW: {'Yes' if model.get('nsfw') else 'No'}")
    
    if model.get('description'):
        desc = safe_str(model['description'][:200])
        if len(model['description']) > 200:
            desc += "..."
        lines.append(f"Description: {desc}")
    
    if versions:
        lines.append(f"\nVersions ({len(versions)}):")
        for i, version in enumerate(versions[:5]):  # Show first 5 versions
            version_name = safe_str(version.get('name', f'Version {i+1}'))
            base_model = safe_str(version.get('baseModel', 'Unknown'))
            files_count = len(version.get('files', []))
            lines.append(f"  - {version_name} (Base: {base_model}, Files: {files_count})")
        
        if len(versions) > 5:
            lines.append(f"  ... and {len(versions) - 5} more versions")
    
    return "\n".join(lines)


def format_search_results(models_data: Dict[str, Any]) -> None:
    """Format and display search results in a table.
    
    Args:
        models_data: Search results from API
    """
    console = Console()
    
    if not models_data.get('items'):
        console.print("No models found.")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Name", style="green", width=35)
    table.add_column("Type", style="yellow", width=12)
    table.add_column("Base Model", style="blue", width=15)
    table.add_column("Files", style="red", width=5)
    table.add_column("NSFW", style="red", width=5)
    
    for model in models_data['items']:
        model_id = str(model.get('id', ''))
        name = safe_str(model.get('name', 'Unknown'))
        model_type = safe_str(model.get('type', 'Unknown'))
        nsfw = "Yes" if model.get('nsfw') else "No"
        
        # Get info from latest version
        versions = model.get('modelVersions', [])
        if versions:
            latest_version = versions[0]
            base_model = safe_str(latest_version.get('baseModel', 'Unknown'))
            files_count = len(latest_version.get('files', []))
        else:
            base_model = 'Unknown'
            files_count = 0
        
        # Truncate name if too long
        if len(name) > 32:
            name = name[:29] + "..."
        
        table.add_row(
            model_id,
            name,
            model_type,
            base_model,
            str(files_count),
            nsfw
        )
    
    console.print(table)
    
    # Show pagination info
    metadata = models_data.get('metadata', {})
    if 'currentPage' in metadata or 'totalPages' in metadata:
        current_page = metadata.get('currentPage', 1)
        total_pages = metadata.get('totalPages', '?')
        console.print(f"\nPage {current_page} of {total_pages}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def format_model_versions(model_data: Dict[str, Any]) -> None:
    """Format and display model versions.
    
    Args:
        model_data: Model data from API
    """
    console = Console()
    
    if not model_data.get('items'):
        console.print("No model data available.")
        return
    
    model = model_data['items'][0]
    versions = model.get('modelVersions', [])
    
    if not versions:
        console.print("No versions available.")
        return
    
    console.print(f"[bold]Versions for {model.get('name', 'Unknown')}[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Name", style="green", width=25)
    table.add_column("Base Model", style="blue", width=15)
    table.add_column("Published", style="yellow", width=12)
    table.add_column("Files", style="red", width=6)
    
    for version in versions:
        version_id = str(version.get('id', ''))
        name = version.get('name', 'Unknown')
        base_model = version.get('baseModel', 'Unknown')
        published = version.get('publishedAt', '')
        if published:
            published = published.split('T')[0]  # Just the date part
        files_count = len(version.get('files', []))
        
        # Truncate name if too long
        if len(name) > 23:
            name = name[:20] + "..."
        
        table.add_row(
            version_id,
            name,
            base_model,
            published,
            str(files_count)
        )
    
    console.print(table)


def format_version_files(version_data: Dict[str, Any]) -> None:
    """Format and display files in a version.
    
    Args:
        version_data: Version data from API
    """
    console = Console()
    
    files = version_data.get('files', [])
    if not files:
        console.print("No files available.")
        return
    
    version_name = version_data.get('name', 'Unknown')
    console.print(f"[bold]Files in version: {version_name}[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Name", style="green", width=35)
    table.add_column("Size", style="blue", width=10)
    table.add_column("Format", style="yellow", width=12)
    table.add_column("Primary", style="red", width=8)
    
    for file_info in files:
        file_id = str(file_info.get('id', ''))
        name = file_info.get('name', 'Unknown')
        size_kb = file_info.get('sizeKB', 0)
        size_str = format_file_size(size_kb * 1024) if size_kb else 'Unknown'
        
        metadata = file_info.get('metadata', {})
        format_info = metadata.get('format', 'Unknown')
        
        is_primary = "Yes" if file_info.get('primary') else "No"
        
        # Truncate name if too long
        if len(name) > 33:
            name = name[:30] + "..."
        
        table.add_row(
            file_id,
            name,
            size_str,
            format_info,
            is_primary
        )
    
    console.print(table)


def print_error(message: str) -> None:
    """Print error message in red.
    
    Args:
        message: Error message
    """
    console = Console()
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print success message in green.
    
    Args:
        message: Success message
    """
    console = Console()
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_warning(message: str) -> None:
    """Print warning message in yellow.
    
    Args:
        message: Warning message
    """
    console = Console()
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print info message in blue.
    
    Args:
        message: Info message
    """
    console = Console()
    console.print(f"[bold blue]Info:[/bold blue] {message}")