"""Download command implementation."""

from pathlib import Path
from typing import Optional

import click
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskID

from ..api import CivitAIClient
from ..download import download_model_by_id, DownloadError
from ..utils import print_error, print_success, format_model_versions, format_version_files
from ..config import get_config


@click.command()
@click.argument('model_id', type=int)
@click.option('--version', type=int, help='Specific version ID to download')
@click.option('--file', 'file_id', type=int, help='Specific file ID to download')
@click.option('--path', type=click.Path(path_type=Path), 
              help='Directory to save the file (default: configured download path)')
@click.option('--show-versions', is_flag=True, 
              help='Show available versions instead of downloading')
@click.option('--show-files', is_flag=True,
              help='Show available files for latest/specified version')
def download(
    model_id: int,
    version: Optional[int],
    file_id: Optional[int],
    path: Optional[Path],
    show_versions: bool,
    show_files: bool
) -> None:
    """Download an AI model.
    
    Examples:
        aimodel download 123456
        aimodel download 123456 --version 234567
        aimodel download 123456 --file 345678
        aimodel download 123456 --path ./my-models
        aimodel download 123456 --show-versions
    """
    client = CivitAIClient()
    
    # Get model information
    with Progress(
        TextColumn("[progress.description]"),
        transient=True,
    ) as progress:
        progress.add_task(description="Fetching model information...", total=None)
        model_data = client.get_model_by_id(model_id)
    
    if isinstance(model_data, str):
        error_messages = {
            'timeout': 'Request timed out. Please try again.',
            'connection_error': 'Failed to connect to AI model service. Check your internet connection.',
            'not_found': f'Model {model_id} not found.',
            'service_unavailable': 'AI model service is currently unavailable.',
            'invalid_json': 'Received invalid response from AI model service.',
        }
        print_error(error_messages.get(model_data, f'Unknown error: {model_data}'))
        return
    
    if not model_data.get('items'):
        print_error(f"Model {model_id} not found.")
        return
    
    model_item = model_data['items'][0]
    
    # Show versions if requested
    if show_versions:
        format_model_versions(model_data)
        return
    
    # Show files if requested
    if show_files:
        versions = model_item.get('modelVersions', [])
        if not versions:
            print_error("No versions available.")
            return
        
        # Use specified version or latest
        if version:
            version_data = next((v for v in versions if v['id'] == version), None)
            if not version_data:
                print_error(f"Version {version} not found.")
                return
        else:
            version_data = versions[0]
        
        format_version_files(version_data)
        return
    
    # Download the model
    progress_task: Optional[TaskID] = None
    
    def progress_callback(progress_value: float, status: str) -> None:
        nonlocal progress_task
        if progress_task is not None:
            download_progress.update(progress_task, completed=progress_value * 100, description=status)
    
    with Progress(
        TextColumn("[progress.description]"),
        BarColumn(),
        TextColumn("[progress.percentage:>3.0f]%"),
        TimeRemainingColumn(),
    ) as download_progress:
        progress_task = download_progress.add_task("Starting download...", total=100)
        
        try:
            success, saved_path = download_model_by_id(
                model_id=model_id,
                version_id=version,
                file_id=file_id,
                save_dir=path,
                progress_callback=progress_callback
            )
            
            if success and saved_path:
                print_success(f"Downloaded: {saved_path}")
            else:
                print_error("Download failed.")
                
        except DownloadError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Unexpected error: {e}")


@click.command()
@click.argument('url')
@click.option('--path', type=click.Path(path_type=Path),
              help='Directory to save the file (default: configured download path)')
def download_url(url: str, path: Optional[Path]) -> None:
    """Download a model from a URL.
    
    Examples:
        aimodel download-url "https://civitai.com/models/123456"
    """
    import re
    
    # Extract model ID from URL
    match = re.search(r'models/(\d+)', url)
    if not match:
        print_error("Invalid CivitAI URL. Expected format: https://civitai.com/models/123456")
        return
    
    model_id = int(match.group(1))
    
    # Use the download command with extracted ID
    from click.testing import CliRunner
    runner = CliRunner()
    
    cmd_args = [str(model_id)]
    if path:
        cmd_args.extend(['--path', str(path)])
    
    result = runner.invoke(download, cmd_args, standalone_mode=False)
    if result.exception:
        raise result.exception