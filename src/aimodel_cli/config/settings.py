"""Configuration management for AI Model CLI."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for AI Model CLI."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Custom configuration directory. If None, uses default.
        """
        if config_dir is None:
            config_dir = Path.home() / ".aimodel-cli"
        
        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"
        self.subfolders_file = config_dir / "subfolders.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize default configuration
        self._defaults = {
            "api_key": "",
            "default_download_path": str(Path.cwd() / "models"),
            "disable_ssl": False,
            "proxy": "",
            "timeout": 60,
            "show_nsfw": False,
            "auto_create_folders": True,
            "save_metadata": True,
            "save_preview": True,
            "overwrite_existing": False,
            "metadata_recursive_default": False,
            # Model type specific paths
            "model_paths": {
                "Checkpoint": "",
                "TextualInversion": "",
                "LORA": "",
                "LoCon": "",
                "DoRA": "",
                "Hypernetwork": "",
                "AestheticGradient": "",
                "Controlnet": "",
                "Poses": "",
                "VAE": "",
                "Upscaler": "",
                "MotionModule": "",
                "Wildcards": "",
                "Workflows": "",
                "Other": ""
            }
        }
        
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            self._save_config(self._defaults)
            return self._defaults.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            merged_config = self._defaults.copy()
            merged_config.update(config)
            return merged_config
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config file: {e}")
            return self._defaults.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Failed to save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
        self._save_config(self._config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = self._defaults.copy()
        self._save_config(self._config)
    
    def load_subfolders(self) -> Dict[str, str]:
        """Load custom subfolder configurations."""
        if not self.subfolders_file.exists():
            return {}
        
        try:
            with open(self.subfolders_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_subfolders(self, subfolders: Dict[str, str]) -> None:
        """Save custom subfolder configurations."""
        try:
            with open(self.subfolders_file, 'w', encoding='utf-8') as f:
                json.dump(subfolders, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Failed to save subfolders file: {e}")
    
    def get_model_path(self, model_type: str) -> Path:
        """Get download path for specific model type.
        
        Args:
            model_type: Type of model (e.g., 'Checkpoint', 'LORA', etc.)
            
        Returns:
            Path object for the model type
        """
        model_paths = self._config.get("model_paths", {})
        specific_path = model_paths.get(model_type, "")
        
        if specific_path:
            return Path(specific_path)
        else:
            # Fall back to default path with mapped folder name
            default_path = Path(self._config.get("default_download_path"))
            folder_name = self._get_default_folder_name(model_type)
            return default_path / folder_name
    
    def set_model_path(self, model_type: str, path: str) -> None:
        """Set download path for specific model type.
        
        Args:
            model_type: Type of model
            path: Path to set (empty string to use default)
        """
        if "model_paths" not in self._config:
            self._config["model_paths"] = {}
        
        self._config["model_paths"][model_type] = path
        self._save_config(self._config)
    
    def get_all_model_paths(self) -> Dict[str, str]:
        """Get all model type paths.
        
        Returns:
            Dictionary of model type -> path mappings
        """
        model_paths = self._config.get("model_paths", {})
        result = {}
        
        for model_type in self._defaults["model_paths"]:
            specific_path = model_paths.get(model_type, "")
            if specific_path:
                result[model_type] = specific_path
            else:
                default_path = Path(self._config.get("default_download_path"))
                folder_name = self._get_default_folder_name(model_type)
                result[model_type] = str(default_path / folder_name)
        
        return result
    
    def _get_default_folder_name(self, model_type: str) -> str:
        """Get default folder name for model type.
        
        Args:
            model_type: Type of model
            
        Returns:
            Default folder name for the model type
        """
        folder_mapping = {
            "Checkpoint": "Stable-diffusion",
            "LORA": "Lora",
            "TextualInversion": "embeddings",
            "Upscaler": "ESRGAN",
            "Controlnet": "ControlNet"
        }
        
        return folder_mapping.get(model_type, model_type)


# Global configuration instance
_config = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


