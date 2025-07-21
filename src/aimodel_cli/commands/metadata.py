"""Metadata and preview completion command implementation."""

import click
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress, TaskID, TextColumn, BarColumn, TimeRemainingColumn

from ..api import CivitAIClient
from ..config import get_config
from ..models import ModelInfo
from ..utils import print_success, print_error, print_warning, print_info


@click.group()
def metadata() -> None:
    """Manage model metadata and previews."""
    pass


@metadata.command('complete')
@click.argument('path', type=click.Path(exists=True, path_type=Path), required=False)
@click.option('--model-type', '-t', help='Process files in specific model type path (Checkpoint, LORA, TextualInversion, etc.)')
@click.option('--recursive/--no-recursive', '-r', default=None, help='Process files recursively in subdirectories (overrides config default)')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing metadata and preview files')
@click.option('--metadata-only', is_flag=True, help='Only download metadata, skip preview images')
@click.option('--preview-only', is_flag=True, help='Only download preview images, skip metadata')
def complete_metadata(
    path: Optional[Path], 
    model_type: Optional[str],
    recursive: Optional[bool], 
    force: bool, 
    metadata_only: bool, 
    preview_only: bool
) -> None:
    """Complete missing metadata and preview files using SHA256 hash identification.
    
    This command analyzes existing model files using SHA256 hash identification
    to fetch metadata from CivitAI, including descriptions, tags, and preview images.
    
    Either specify PATH or use --model-type option:
    
    PATH: File or directory path to process
    
    --model-type: Process files in the configured download path for a specific model type
                 (Checkpoint, LORA, TextualInversion, Upscaler, Controlnet, etc.)
    
    Hash-based Identification:
    • Calculates SHA256 hash of each model file
    • Matches against CivitAI database for accurate identification
    • Downloads model name, description, tags, and preview images
    • Creates .json metadata files and .preview.png images
    
    The recursive behavior is determined by:
    1. Command line flags --recursive/-r or --no-recursive (highest priority)
    2. Config setting metadata_recursive_default (if no flags specified)
    
    Examples:
        aimodel metadata complete --model-type LORA --recursive
        aimodel metadata complete /path/to/models --force --recursive
        aimodel metadata complete --model-type Checkpoint --preview-only
    """
    if metadata_only and preview_only:
        print_error("Cannot specify both --metadata-only and --preview-only")
        return
    
    if path is None and model_type is None:
        print_error("Must specify either PATH or --model-type option")
        return
    
    if path is not None and model_type is not None:
        print_error("Cannot specify both PATH and --model-type option")
        return
    
    # Determine recursive setting
    config = get_config()
    if recursive is not None:
        # Use command line flag
        use_recursive = recursive
    else:
        # Use config default
        use_recursive = config.get("metadata_recursive_default", False)
    
    client = CivitAIClient()
    console = Console()
    
    # Determine target path
    if model_type:
        # Validate model type
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
        print_info(f"Processing {model_type} models in: {target_path}")
        
        if not target_path.exists():
            print_warning(f"Directory does not exist: {target_path}")
            print_info("No models to process")
            return
    else:
        target_path = path
    
    # Collect model files
    model_files = []
    if target_path.is_file():
        if _is_model_file(target_path):
            model_files.append(target_path)
        else:
            print_error(f"File {target_path} is not a supported model file")
            return
    else:
        model_files = _find_model_files(target_path, use_recursive)
    
    if not model_files:
        print_warning("No model files found")
        return
    
    print_info(f"Found {len(model_files)} model files")
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Processing models...", total=len(model_files))
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for model_file in model_files:
            progress.update(task, description=f"Processing {model_file.name}")
            
            try:
                result = _process_single_file(
                    model_file, client, force, metadata_only, preview_only
                )
                
                if result == "success":
                    success_count += 1
                elif result == "skipped":
                    skipped_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print_error(f"Error processing {model_file.name}: {e}")
                error_count += 1
            
            progress.advance(task)
    
    # Summary
    console.print()
    if success_count > 0:
        print_success(f"Successfully processed {success_count} files")
    if skipped_count > 0:
        print_info(f"Skipped {skipped_count} files (already complete)")
    if error_count > 0:
        print_error(f"Failed to process {error_count} files")


@metadata.command('hash')
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
def calculate_hash(file_path: Path) -> None:
    """Calculate SHA256 hash of a model file with caching.
    
    This command calculates the SHA256 hash and automatically saves it to the
    model's metadata file. Subsequent calls will use the cached value for instant results.
    
    FILE_PATH: Path to the model file
    """
    if not _is_model_file(file_path):
        print_error(f"File {file_path} is not a supported model file")
        return
    
    try:
        model_info = ModelInfo(file_path)
        
        # Check if hash is already cached
        existing_data = model_info.load_from_json()
        if 'sha256' in existing_data and existing_data['sha256']:
            print_info("Using cached SHA256 hash...")
            hash_value = existing_data['sha256']
        else:
            print_info("Calculating SHA256 hash...")
            hash_value = model_info.generate_sha256()
        
        print_info(f"SHA256: {hash_value}")
        
    except Exception as e:
        print_error(f"Failed to calculate hash: {e}")


def _process_single_file(
    model_file: Path,
    client: CivitAIClient,
    force: bool,
    metadata_only: bool,
    preview_only: bool
) -> str:
    """Process a single model file.
    
    Returns:
        "success", "skipped", or "error"
    """
    model_info = ModelInfo(model_file)
    
    # Check if files already exist
    json_exists = model_info.json_path.exists()
    preview_exists = model_info.preview_path.exists()
    
    if not force:
        if metadata_only and json_exists:
            return "skipped"
        if preview_only and preview_exists:
            return "skipped"
        if not metadata_only and not preview_only and json_exists and preview_exists:
            return "skipped"
    
    # Calculate hash (uses cached value if available)
    try:
        file_hash = model_info.generate_sha256()
    except Exception as e:
        print_error(f"Failed to calculate hash for {model_file.name}: {e}")
        return "error"
    
    # Search by hash
    hash_result = client.search_by_hash(file_hash)
    if isinstance(hash_result, str):
        print_warning(f"Could not find model info for {model_file.name}: {hash_result}")
        return "error"
    
    # Extract model data for metadata saving
    model_data = _convert_version_to_model_data(hash_result)
    
    success = True
    
    # Save metadata
    if not metadata_only or not preview_only:
        if force or not json_exists:
            try:
                model_info.save_model_metadata(model_data, file_hash)
            except Exception as e:
                print_error(f"Failed to save metadata for {model_file.name}: {e}")
                success = False
    
    # Save preview
    if not metadata_only:
        if force or not preview_exists:
            try:
                model_info.save_preview_image(model_data, file_hash)
            except Exception as e:
                print_warning(f"Failed to save preview for {model_file.name}: {e}")
                # Preview failure is not critical
    
    return "success" if success else "error"


def _convert_version_to_model_data(version_data: dict) -> dict:
    """Convert API version response to model data format.
    
    Args:
        version_data: Version data from hash search
        
    Returns:
        Model data in expected format
    """
    # The hash search returns version data, we need to construct model data format
    model_data = {
        "items": [{
            "id": version_data.get("modelId"),
            "name": version_data.get("model", {}).get("name", "Unknown"),
            "type": version_data.get("model", {}).get("type", "Unknown"),
            "nsfw": version_data.get("model", {}).get("nsfw", False),
            "description": version_data.get("model", {}).get("description", ""),
            "modelVersions": [version_data]
        }]
    }
    
    return model_data


def _is_model_file(file_path: Path) -> bool:
    """Check if file is a supported model file."""
    supported_extensions = {'.safetensors', '.pt', '.pth', '.ckpt', '.bin'}
    return file_path.suffix.lower() in supported_extensions


def _find_model_files(directory: Path, recursive: bool) -> List[Path]:
    """Find all model files in directory."""
    model_files = []
    
    pattern = "**/*" if recursive else "*"
    
    for file_path in directory.glob(pattern):
        if file_path.is_file() and _is_model_file(file_path):
            model_files.append(file_path)
    
    return sorted(model_files)


# Add commands to the group
metadata.add_command(complete_metadata)
metadata.add_command(calculate_hash)