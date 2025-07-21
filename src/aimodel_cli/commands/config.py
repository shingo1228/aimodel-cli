"""Configuration command implementation."""

import click
from rich.console import Console
from rich.table import Table

from ..config import get_config
from ..utils import print_success, print_error, print_info


@click.group()
def config() -> None:
    """Manage configuration settings."""
    pass


@config.command('list')
def list_config() -> None:
    """List all configuration settings."""
    config_obj = get_config()
    settings = config_obj.get_all()
    
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", width=25)
    table.add_column("Value", style="green", width=50)
    
    for key, value in sorted(settings.items()):
        # Hide sensitive values
        if 'key' in key.lower() or 'secret' in key.lower():
            if value:
                display_value = f"{'*' * (len(str(value)) - 4)}{str(value)[-4:]}"
            else:
                display_value = "(not set)"
        else:
            display_value = str(value)
        
        table.add_row(key, display_value)
    
    console.print(table)


@config.command('get')
@click.argument('key')
def get_config_value(key: str) -> None:
    """Get a specific configuration value."""
    config_obj = get_config()
    value = config_obj.get(key)
    
    if value is None:
        print_error(f"Configuration key '{key}' not found.")
        return
    
    # Hide sensitive values
    if 'key' in key.lower() or 'secret' in key.lower():
        if value:
            display_value = f"{'*' * (len(str(value)) - 4)}{str(value)[-4:]}"
        else:
            display_value = "(not set)"
    else:
        display_value = str(value)
    
    print_info(f"{key}: {display_value}")


@config.command('set')
@click.argument('key')
@click.argument('value')
def set_config_value(key: str, value: str) -> None:
    """Set a configuration value."""
    config_obj = get_config()
    
    # Convert string values to appropriate types
    if value.lower() in ('true', 'false'):
        value = value.lower() == 'true'
    elif value.isdigit():
        value = int(value)
    elif value.replace('.', '').isdigit():
        value = float(value)
    
    config_obj.set(key, value)
    print_success(f"Set {key} = {value}")


@config.command('reset')
@click.confirmation_option(prompt='Are you sure you want to reset all configuration to defaults?')
def reset_config() -> None:
    """Reset configuration to defaults."""
    config_obj = get_config()
    config_obj.reset()
    print_success("Configuration reset to defaults.")


@config.command('path')
def show_config_path() -> None:
    """Show configuration file path."""
    config_obj = get_config()
    print_info(f"Configuration directory: {config_obj.config_dir}")
    print_info(f"Configuration file: {config_obj.config_file}")


@config.command('api-key')
@click.argument('api_key', required=False)
@click.option('--show', is_flag=True, help='Show current API key (masked)')
def set_api_key(api_key: str, show: bool) -> None:
    """Set or show API key.
    
    Get your CivitAI API key from: https://civitai.com/user/account
    """
    config_obj = get_config()
    
    if show:
        current_key = config_obj.get('api_key', '')
        if current_key:
            masked_key = f"{'*' * (len(current_key) - 4)}{current_key[-4:]}"
            print_info(f"Current API key: {masked_key}")
        else:
            print_info("No API key configured.")
        return
    
    if api_key is None:
        api_key = click.prompt('Enter your API key', hide_input=True)
    
    config_obj.set('api_key', api_key)
    print_success("API key configured successfully.")


@config.command('download-path')
@click.argument('path', type=click.Path(exists=False), required=False)
def set_download_path(path: str) -> None:
    """Set default download path."""
    config_obj = get_config()
    
    if path is None:
        current_path = config_obj.get('default_download_path')
        print_info(f"Current download path: {current_path}")
        return
    
    config_obj.set('default_download_path', path)
    print_success(f"Download path set to: {path}")


@config.command('model-paths')
def list_model_paths() -> None:
    """List model-type-specific download paths."""
    config_obj = get_config()
    model_paths = config_obj.get_all_model_paths()
    
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Model Type", style="cyan", width=20)
    table.add_column("Download Path", style="green", width=60)
    
    for model_type, path in sorted(model_paths.items()):
        table.add_row(model_type, path)
    
    console.print(table)


@config.command('model-path')
@click.argument('model_type')
@click.argument('path', type=click.Path(exists=False), required=False)
def set_model_path(model_type: str, path: str) -> None:
    """Set download path for specific model type with smart organization.
    
    MODEL_TYPE: Type of model (Checkpoint, LORA, TextualInversion, etc.)
    PATH: Directory path (empty string to use default structure)
    
    Default Model Type Mapping:
    • Checkpoint → Stable-diffusion/
    • LORA → Lora/
    • LoCon → Lora/ (combined with LORA)
    • DoRA → Lora/ (combined with LORA)
    • TextualInversion → embeddings/
    • Upscaler → ESRGAN/
    • Controlnet → ControlNet/
    • VAE → VAE/
    • Other types use their original names
    
    Available model types:
    Checkpoint, TextualInversion, LORA, LoCon, DoRA, Hypernetwork,
    AestheticGradient, Controlnet, Poses, VAE, Upscaler, MotionModule,
    Wildcards, Workflows, Other
    
    Examples:
        # Set custom LORA path
        aimodel config model-path LORA /custom/lora/models
        
        # Reset to default structure
        aimodel config model-path Checkpoint ""
        
        # View current path
        aimodel config model-path LORA
    """
    config_obj = get_config()
    
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
    
    if path is None:
        current_path = config_obj.get_model_path(model_type)
        print_info(f"Current path for {model_type}: {current_path}")
        return
    
    config_obj.set_model_path(model_type, path)
    if path:
        print_success(f"Set {model_type} download path to: {path}")
    else:
        print_success(f"Reset {model_type} to use default path structure")


@config.command('metadata-recursive')
@click.argument('enable', type=click.Choice(['true', 'false']), required=False)
def set_metadata_recursive(enable: str) -> None:
    """Set default recursive behavior for metadata commands.
    
    ENABLE: 'true' to enable recursive by default, 'false' to disable
    """
    config_obj = get_config()
    
    if enable is None:
        current_setting = config_obj.get('metadata_recursive_default', False)
        print_info(f"Current metadata recursive default: {current_setting}")
        return
    
    enable_bool = enable.lower() == 'true'
    config_obj.set('metadata_recursive_default', enable_bool)
    
    if enable_bool:
        print_success("Enabled recursive processing by default for metadata commands")
        print_info("Use --no-recursive flag to override for specific commands")
    else:
        print_success("Disabled recursive processing by default for metadata commands")
        print_info("Use --recursive/-r flag to override for specific commands")


# Add all configuration commands to the group
config.add_command(list_config)
config.add_command(get_config_value)
config.add_command(set_config_value)
config.add_command(reset_config)
config.add_command(show_config_path)
config.add_command(set_api_key)
config.add_command(set_download_path)
config.add_command(list_model_paths)
config.add_command(set_model_path)
config.add_command(set_metadata_recursive)