"""Main CLI entry point."""

import click
from rich.console import Console

from .commands.search import search
from .commands.download import download, download_url
from .commands.config import config
from .commands.info import info
from .commands.metadata import metadata
from .commands.update import update
from .utils import print_error, print_info


@click.group()
@click.version_option()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """AI Model CLI - Download and manage AI models.
    
    This tool provides comprehensive AI model management with advanced features
    for existing model collections and new downloads.
    
    Key Features:
    • Search and download models with advanced filters
    • Check for updates in existing model collections
    • Complete missing metadata using SHA256 hash identification
    • Generate Markdown reports with preview images
    • Smart model-type organization (Checkpoint→Stable-diffusion, LORA→Lora, etc.)
    • Recursive directory processing
    • Personal API key support for restricted content
    
    Examples:
        aimodel search "realistic portrait" --type LORA
        aimodel download 123456
        aimodel metadata complete --model-type LORA --recursive
        aimodel update check --model-type Checkpoint --report updates.md
        aimodel config model-path LORA /custom/lora/path
    
    Get started with interactive setup:
        aimodel setup
    
    For detailed help on any command:
        aimodel COMMAND --help
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    print_info(f"AI Model CLI version {__version__}")


@cli.command()
def setup() -> None:
    """Interactive setup wizard."""
    from .config import get_config
    
    console = Console()
    config_obj = get_config()
    
    console.print("[bold]AI Model CLI Setup Wizard[/bold]")
    console.print()
    
    # API Key setup
    console.print("1. API Key Configuration")
    console.print("   Get your CivitAI API key from: https://civitai.com/user/account")
    
    current_key = config_obj.get('api_key', '')
    if current_key:
        masked_key = f"{'*' * (len(current_key) - 4)}{current_key[-4:]}"
        console.print(f"   Current API key: {masked_key}")
        if not click.confirm("Do you want to update your API key?"):
            api_key = current_key
        else:
            api_key = click.prompt('   Enter your API key', hide_input=True)
    else:
        console.print("   No API key configured.")
        if click.confirm("Do you want to set up your API key now?"):
            api_key = click.prompt('   Enter your API key', hide_input=True)
        else:
            api_key = ''
    
    if api_key:
        config_obj.set('api_key', api_key)
        console.print("   ✓ API key configured")
    
    console.print()
    
    # Download path setup
    console.print("2. Download Path Configuration")
    current_path = config_obj.get('default_download_path')
    console.print(f"   Current download path: {current_path}")
    
    if click.confirm("Do you want to change the download path?"):
        new_path = click.prompt('   Enter new download path', default=current_path)
        config_obj.set('default_download_path', new_path)
        console.print("   ✓ Download path updated")
    
    console.print()
    
    # Download settings
    console.print("3. Download Settings")
    
    show_nsfw = config_obj.get('show_nsfw', False)
    console.print(f"   Show NSFW content: {show_nsfw}")
    if click.confirm("Do you want to change this setting?"):
        show_nsfw = click.confirm("Show NSFW content in search results?")
        config_obj.set('show_nsfw', show_nsfw)
        console.print("   ✓ NSFW setting updated")
    
    console.print()
    console.print("[bold green]Setup completed![/bold green]")
    console.print()
    console.print("You can now use the CLI. Try:")
    console.print("  aimodel search --help")
    console.print("  aimodel download --help")


# Add commands to the main CLI group
cli.add_command(search)
cli.add_command(download)
cli.add_command(download_url)
cli.add_command(config)
cli.add_command(info)
cli.add_command(metadata)
cli.add_command(update)


if __name__ == '__main__':
    cli()