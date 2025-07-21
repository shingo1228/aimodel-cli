"""Info command implementation."""

from pathlib import Path
from typing import Optional

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..api import CivitAIClient
from ..models import ModelInfo
from ..utils import format_model_info, print_error, print_info


@click.command()
@click.argument('target')
@click.option('--local', is_flag=True, help='Target is a local file path')
def info(target: str, local: bool) -> None:
    """Show information about a model.
    
    TARGET can be either:
    - A model ID (e.g., 123456)
    - A local file path (with --local flag)
    - A CivitAI URL (e.g., https://civitai.com/models/123456)
    
    Examples:
        civitai info 123456
        civitai info "https://civitai.com/models/123456"
        civitai info ./model.safetensors --local
    """
    if local:
        # Handle local file
        file_path = Path(target)
        if not file_path.exists():
            print_error(f"File not found: {target}")
            return
        
        model_info = ModelInfo(file_path)
        data = model_info.load_from_json()
        
        if not data:
            print_info(f"No metadata found for: {file_path.name}")
            print_info("Try running: civitai scan to fetch model information")
            return
        
        # Display local info
        print_info(f"File: {file_path.name}")
        print_info(f"Path: {file_path}")
        
        if 'sha256' in data:
            print_info(f"SHA256: {data['sha256']}")
        
        if 'modelId' in data:
            print_info(f"CivitAI Model ID: {data['modelId']}")
        
        if 'activation text' in data:
            print_info(f"Activation Text: {data['activation text']}")
        
        if 'sd version' in data:
            print_info(f"Base Model: {data['sd version']}")
        
        if 'description' in data:
            desc = data['description']
            if len(desc) > 200:
                desc = desc[:200] + "..."
            print_info(f"Description: {desc}")
        
        return
    
    # Handle model ID or URL
    model_id = None
    
    if target.isdigit():
        model_id = int(target)
    elif 'civitai.com' in target:
        import re
        match = re.search(r'models/(\d+)', target)
        if match:
            model_id = int(match.group(1))
        else:
            print_error("Invalid CivitAI URL. Expected format: https://civitai.com/models/123456")
            return
    else:
        print_error("Invalid target. Use model ID, URL, or file path with --local")
        return
    
    # Fetch model info from API
    client = CivitAIClient()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Fetching model information...", total=None)
        result = client.get_model_by_id(model_id)
    
    if isinstance(result, str):
        error_messages = {
            'timeout': 'Request timed out. Please try again.',
            'connection_error': 'Failed to connect to CivitAI. Check your internet connection.',
            'not_found': f'Model {model_id} not found.',
            'service_unavailable': 'CivitAI service is currently unavailable.',
            'invalid_json': 'Received invalid response from CivitAI.',
        }
        print_error(error_messages.get(result, f'Unknown error: {result}'))
        return
    
    # Display model info
    if result.get('items'):
        formatted_info = format_model_info(result)
        print(formatted_info)
    else:
        print_error("No model data received from API")