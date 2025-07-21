"""Model update checking command implementation."""

import json
import click
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn

from ..api import CivitAIClient
from ..config import get_config
from ..models import ModelInfo
from ..utils import print_success, print_error, print_warning, print_info, safe_str, generate_update_report


@click.group()
def update() -> None:
    """Check for model updates and manage versions."""
    pass


@update.command('check')
@click.argument('path', type=click.Path(exists=True, path_type=Path), required=False)
@click.option('--model-type', '-t', help='Check specific model type path (Checkpoint, LORA, TextualInversion, etc.)')
@click.option('--recursive/--no-recursive', '-r', default=None, help='Process files recursively (overrides config default)')
@click.option('--download', '-d', is_flag=True, help='Automatically download available updates')
@click.option('--show-all', is_flag=True, help='Show all models, including those without updates')
@click.option('--report', type=click.Path(path_type=Path), help='Generate Markdown report file')
@click.option('--report-include-current', is_flag=True, help='Include up-to-date models in report')
def check_updates(
    path: Optional[Path],
    model_type: Optional[str],
    recursive: Optional[bool],
    download: bool,
    show_all: bool,
    report: Optional[Path],
    report_include_current: bool
) -> None:
    """Check for available model updates with comprehensive report generation.
    
    This command scans existing model files for available updates on CivitAI
    and can generate comprehensive Markdown reports with preview images.
    
    Either specify PATH or use --model-type option:
    
    PATH: File or directory path to check
    
    --model-type: Check models in the configured download path for a specific model type
                 (Checkpoint, LORA, TextualInversion, etc.)
    
    Report Generation Features:
    • Comprehensive Markdown reports with model previews and CivitAI links
    • Preview images automatically resized for readability
    • Direct links to CivitAI model pages and specific versions
    • Technical details including file sizes, formats, download counts
    • Summary statistics (total checked, updates available, up-to-date models)
    
    Examples:
        # Check LORA models and generate report with previews
        aimodel update check --model-type LORA --report lora-updates.md
        
        # Check specific directory recursively with auto-download
        aimodel update check /path/to/models --recursive --download
        
        # Generate comprehensive report including up-to-date models
        aimodel update check --model-type Checkpoint --report full-report.md --report-include-current
    """
    if path is None and model_type is None:
        print_error("Must specify either PATH or --model-type option")
        return
    
    if path is not None and model_type is not None:
        print_error("Cannot specify both PATH and --model-type option")
        return
    
    # Determine recursive setting
    config = get_config()
    if recursive is not None:
        use_recursive = recursive
    else:
        use_recursive = config.get("metadata_recursive_default", False)
    
    client = CivitAIClient()
    console = Console()
    
    # Determine target path
    if model_type:
        valid_types = [
            "Checkpoint", "TextualInversion", "LORA", "LoCon", "DoRA",
            "Hypernetwork", "AestheticGradient", "Controlnet", "Poses",
            "VAE", "Upscaler", "MotionModule", "Wildcards", "Workflows", "Other"
        ]
        
        if model_type not in valid_types:
            print_error(f"Invalid model type: {model_type}")
            print_info(f"Valid types: {', '.join(valid_types)}")
            return
        
        target_path = config.get_model_path(model_type)
        print_info(f"Checking {model_type} models in: {target_path}")
        
        if not target_path.exists():
            print_warning(f"Directory does not exist: {target_path}")
            return
    else:
        target_path = path
    
    # Find model files with metadata
    model_files = _find_models_with_metadata(target_path, use_recursive)
    
    if not model_files:
        print_warning("No models with metadata found")
        print_info("Use 'aimodel metadata complete' to generate metadata for existing models")
        return
    
    print_info(f"Found {len(model_files)} models with metadata")
    
    # Check for updates
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Checking for updates...", total=len(model_files))
        
        updates_available = []
        up_to_date = []
        errors = []
        
        for model_file in model_files:
            progress.update(task, description=f"Checking {model_file.name}")
            
            try:
                update_info = _check_model_update(model_file, client)
                
                if update_info["has_update"]:
                    updates_available.append(update_info)
                elif show_all:
                    up_to_date.append(update_info)
                    
            except Exception as e:
                errors.append({"file": model_file, "error": str(e)})
            
            progress.advance(task)
    
    # Display results
    _display_update_results(updates_available, up_to_date, errors, show_all, console)
    
    # Generate report if requested
    if report:
        try:
            generate_update_report(
                updates_available,
                up_to_date,
                errors,
                report,
                include_up_to_date=report_include_current or show_all
            )
            print_success(f"Report generated: {report}")
        except Exception as e:
            print_error(f"Failed to generate report: {e}")
    
    # Auto-download if requested
    if download and updates_available:
        _download_updates(updates_available, client, console)


@update.command('download')
@click.argument('model_file', type=click.Path(exists=True, path_type=Path))
@click.option('--version', help='Specific version to download (default: latest)')
def download_update(model_file: Path, version: Optional[str]) -> None:
    """Download an update for a specific model file."""
    if not _is_model_file(model_file):
        print_error(f"File {model_file} is not a supported model file")
        return
    
    client = CivitAIClient()
    
    try:
        update_info = _check_model_update(model_file, client)
        
        if not update_info["has_update"]:
            print_info(f"No updates available for {model_file.name}")
            return
        
        # Download the update
        if version:
            # Find specific version
            target_version = None
            for v in update_info["available_versions"]:
                if str(v["id"]) == version or v["name"] == version:
                    target_version = v
                    break
            
            if not target_version:
                print_error(f"Version '{version}' not found")
                return
        else:
            target_version = update_info["latest_version"]
        
        print_info(f"Downloading {safe_str(update_info['model_name'])} v{safe_str(target_version['name'])}...")
        
        # Use existing download functionality
        from ..download import download_model_by_id
        
        success, downloaded_path = download_model_by_id(
            update_info["model_id"],
            target_version["id"],
            save_dir=model_file.parent
        )
        
        if success:
            print_success(f"Downloaded update: {downloaded_path}")
        else:
            print_error("Failed to download update")
            
    except Exception as e:
        print_error(f"Failed to check/download update: {e}")


def _find_models_with_metadata(directory: Path, recursive: bool) -> List[Path]:
    """Find all model files that have associated metadata."""
    model_files = []
    
    pattern = "**/*" if recursive else "*"
    
    for file_path in directory.glob(pattern):
        if file_path.is_file() and _is_model_file(file_path):
            # Check if metadata file exists
            json_path = file_path.with_suffix('.json')
            if json_path.exists():
                model_files.append(file_path)
    
    return sorted(model_files)


def _is_model_file(file_path: Path) -> bool:
    """Check if file is a supported model file."""
    supported_extensions = {'.safetensors', '.pt', '.pth', '.ckpt', '.bin'}
    return file_path.suffix.lower() in supported_extensions


def _check_model_update(model_file: Path, client: CivitAIClient) -> Dict[str, Any]:
    """Check if a model has updates available."""
    json_path = model_file.with_suffix('.json')
    
    if not json_path.exists():
        raise Exception(f"No metadata file found for {model_file.name}")
    
    # Load current metadata
    with open(json_path, 'r', encoding='utf-8') as f:
        current_metadata = json.load(f)
    
    model_id = current_metadata.get('modelId')
    current_version_id = current_metadata.get('modelVersionId')
    
    if not model_id:
        raise Exception(f"No model ID found in metadata for {model_file.name}")
    
    # Get latest model information from API
    model_data = client.get_model_by_id(model_id)
    if isinstance(model_data, str):
        raise Exception(f"Failed to get model info: {model_data}")
    
    if not model_data.get('items'):
        raise Exception("Model not found on CivitAI")
    
    model_item = model_data['items'][0]
    versions = model_item.get('modelVersions', [])
    
    if not versions:
        raise Exception("No versions available")
    
    # Find current version and check for newer ones
    current_version = None
    newer_versions = []
    
    for version in versions:
        if version['id'] == current_version_id:
            current_version = version
        elif current_version_id is None or _is_version_newer(version, current_version_id, versions):
            newer_versions.append(version)
    
    has_update = len(newer_versions) > 0
    latest_version = versions[0] if versions else None
    
    return {
        "file_path": model_file,
        "model_id": model_id,
        "model_name": model_item.get('name', 'Unknown'),
        "current_version": current_version,
        "current_version_id": current_version_id,
        "latest_version": latest_version,
        "available_versions": versions,
        "newer_versions": newer_versions,
        "has_update": has_update
    }


def _is_version_newer(version: Dict[str, Any], current_version_id: int, all_versions: List[Dict[str, Any]]) -> bool:
    """Check if a version is newer than the current version."""
    if current_version_id is None:
        return True
    
    # Find current version index
    current_index = None
    version_index = None
    
    for i, v in enumerate(all_versions):
        if v['id'] == current_version_id:
            current_index = i
        if v['id'] == version['id']:
            version_index = i
    
    # Versions are typically ordered newest first
    if current_index is not None and version_index is not None:
        return version_index < current_index
    
    # Fallback to publish date comparison
    current_date = None
    version_date = None
    
    for v in all_versions:
        if v['id'] == current_version_id:
            current_date = v.get('publishedAt')
        if v['id'] == version['id']:
            version_date = v.get('publishedAt')
    
    if current_date and version_date:
        try:
            current_dt = datetime.fromisoformat(current_date.replace('Z', '+00:00'))
            version_dt = datetime.fromisoformat(version_date.replace('Z', '+00:00'))
            return version_dt > current_dt
        except:
            pass
    
    return False


def _display_update_results(
    updates_available: List[Dict[str, Any]],
    up_to_date: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
    show_all: bool,
    console: Console
) -> None:
    """Display update check results."""
    console.print()
    
    if updates_available:
        console.print("[bold green]Models with updates available:[/bold green]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan", width=30)
        table.add_column("Current", style="yellow", width=15)
        table.add_column("Latest", style="green", width=15)
        table.add_column("Published", style="blue", width=12)
        
        for update in updates_available:
            current_name = "Unknown"
            if update["current_version"]:
                current_name = update["current_version"].get("name", "Unknown")
            
            latest_name = update["latest_version"].get("name", "Unknown")
            
            published = update["latest_version"].get("publishedAt", "")
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    published = dt.strftime("%Y-%m-%d")
                except:
                    published = published.split('T')[0]
            
            model_name = update["model_name"]
            if len(model_name) > 27:
                model_name = model_name[:24] + "..."
            
            table.add_row(
                safe_str(model_name), 
                safe_str(current_name), 
                safe_str(latest_name), 
                safe_str(published)
            )
        
        console.print(table)
        console.print()
    
    if show_all and up_to_date:
        console.print("[bold blue]Models up to date:[/bold blue]")
        
        for model in up_to_date:
            model_name = model["model_name"]
            current_name = "Unknown"
            if model["current_version"]:
                current_name = model["current_version"].get("name", "Unknown")
            console.print(f"  {safe_str(model_name)} (v{safe_str(current_name)})")
        
        console.print()
    
    if errors:
        console.print("[bold red]Errors encountered:[/bold red]")
        for error in errors:
            console.print(f"  {safe_str(error['file'].name)}: {safe_str(error['error'])}")
        console.print()
    
    # Summary
    total_checked = len(updates_available) + len(up_to_date) + len(errors)
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"  Total models checked: {total_checked}")
    console.print(f"  Updates available: {len(updates_available)}")
    console.print(f"  Up to date: {len(up_to_date)}")
    console.print(f"  Errors: {len(errors)}")


def _download_updates(
    updates_available: List[Dict[str, Any]],
    client: CivitAIClient,
    console: Console
) -> None:
    """Download available updates."""
    console.print()
    console.print("[bold]Downloading updates...[/bold]")
    
    from ..download import download_model_by_id
    
    success_count = 0
    error_count = 0
    
    for update in updates_available:
        model_name = update["model_name"]
        latest_version = update["latest_version"]
        model_file = update["file_path"]
        
        try:
            console.print(f"Downloading {safe_str(model_name)} v{safe_str(latest_version['name'])}...")
            
            success, downloaded_path = download_model_by_id(
                update["model_id"],
                latest_version["id"],
                save_dir=model_file.parent
            )
            
            if success:
                success_count += 1
                print_success(f"Downloaded: {downloaded_path}")
            else:
                error_count += 1
                print_error(f"Failed to download {safe_str(model_name)}")
                
        except Exception as e:
            error_count += 1
            print_error(f"Error downloading {safe_str(model_name)}: {safe_str(str(e))}")
    
    console.print()
    console.print(f"[bold]Download Summary:[/bold]")
    console.print(f"  Successfully downloaded: {success_count}")
    console.print(f"  Failed: {error_count}")


# Add commands to the group
update.add_command(check_updates)
update.add_command(download_update)