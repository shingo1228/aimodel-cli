"""Search command implementation."""

from typing import List, Optional

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..api import CivitAIClient
from ..utils import format_search_results, print_error


@click.command()
@click.argument('query', required=False)
@click.option('--type', 'content_types', multiple=True, 
              type=click.Choice([
                  'Checkpoint', 'TextualInversion', 'LORA', 'LoCon', 'DoRA',
                  'Hypernetwork', 'AestheticGradient', 'Controlnet', 'Poses',
                  'VAE', 'Upscaler', 'MotionModule', 'Wildcards', 'Workflows', 'Other'
              ]),
              help='Filter by content type(s)')
@click.option('--base-model', 'base_models', multiple=True,
              type=click.Choice([
                  'SD 1.4', 'SD 1.5', 'SD 2.0', 'SD 2.1', 'SDXL 1.0', 'SDXL Turbo',
                  'Stable Cascade', 'Pony', 'Flux.1 D', 'Flux.1 S', 'Other'
              ]),
              help='Filter by base model(s)')
@click.option('--sort', 'sort_by', 
              type=click.Choice([
                  'Newest', 'Oldest', 'Most Downloaded', 'Highest Rated',
                  'Most Liked', 'Most Buzz', 'Most Discussed', 'Most Collected', 'Most Images'
              ]),
              default='Most Downloaded',
              help='Sort order')
@click.option('--period',
              type=click.Choice(['All Time', 'Year', 'Month', 'Week', 'Day']),
              default='All Time',
              help='Time period for sorting')
@click.option('--nsfw', is_flag=True, default=False,
              help='Include NSFW content')
@click.option('--limit', type=int, default=20,
              help='Number of results to show')
@click.option('--page', type=int, default=1,
              help='Page number')
def search(
    query: Optional[str],
    content_types: List[str],
    base_models: List[str],
    sort_by: str,
    period: str,
    nsfw: bool,
    limit: int,
    page: int
) -> None:
    """Search for AI models with comprehensive filtering.
    
    Advanced search with multiple content types, base models, and sorting options.
    Results show model information, download counts, and availability status.
    
    Content Types Available:
    Checkpoint, TextualInversion, LORA, LoCon, DoRA, Hypernetwork, 
    AestheticGradient, Controlnet, Poses, VAE, Upscaler, MotionModule, 
    Wildcards, Workflows, Other
    
    Base Models Available:
    SD 1.4, SD 1.5, SD 2.0, SD 2.1, SDXL 1.0, SDXL Turbo,
    Stable Cascade, Pony, Flux.1 D, Flux.1 S, Other
    
    Examples:
        # Search with multiple filters
        aimodel search "realistic portrait" --type LORA --type Checkpoint --base-model "SD 1.5"
        
        # Recent popular models
        aimodel search --sort "Most Downloaded" --period Week --limit 10
        
        # Include NSFW content
        aimodel search "artistic style" --nsfw --type LORA
    """
    client = CivitAIClient()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Searching...", total=None)
        
        result = client.search_models(
            query=query,
            content_types=list(content_types) if content_types else None,
            base_models=list(base_models) if base_models else None,
            sort_by=sort_by,
            period=period,
            nsfw=nsfw,
            limit=limit,
            page=page
        )
    
    if isinstance(result, str):
        error_messages = {
            'timeout': 'Request timed out. Please try again.',
            'connection_error': 'Failed to connect to AI model service. Check your internet connection.',
            'not_found': 'No results found.',
            'service_unavailable': 'AI model service is currently unavailable.',
            'invalid_json': 'Received invalid response from AI model service.',
        }
        print_error(error_messages.get(result, f'Unknown error: {result}'))
        return
    
    # Filter early access models
    result = client.filter_early_access(result)
    
    format_search_results(result)