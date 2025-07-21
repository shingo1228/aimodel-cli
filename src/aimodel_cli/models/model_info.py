"""Model information and metadata handling."""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image
import requests
from bs4 import BeautifulSoup

from ..config import get_config


class ModelInfo:
    """Handle model metadata and information."""
    
    def __init__(self, file_path: Path):
        """Initialize model info handler.
        
        Args:
            file_path: Path to model file
        """
        self.file_path = Path(file_path)
        self.config = get_config()
        self.json_path = self.file_path.with_suffix('.json')
        self.preview_path = self.file_path.with_suffix('.preview.png')
    
    def generate_sha256(self) -> str:
        """Generate SHA256 hash for the model file.
        
        Returns:
            SHA256 hash string
        """
        # Check if hash already exists in JSON
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'sha256' in data and data['sha256']:
                        return data['sha256']
            except (json.JSONDecodeError, IOError):
                pass
        
        # Generate hash
        h = hashlib.sha256()
        with open(self.file_path, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        
        hash_value = h.hexdigest()
        
        # Save to JSON
        self.save_to_json({'sha256': hash_value})
        
        return hash_value
    
    def save_to_json(self, data: Dict[str, Any], overwrite: bool = False) -> None:
        """Save data to model JSON file.
        
        Args:
            data: Data to save
            overwrite: Whether to overwrite existing data
        """
        existing_data = {}
        if self.json_path.exists() and not overwrite:
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Merge data
        existing_data.update(data)
        
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving JSON file: {e}")
    
    def load_from_json(self) -> Dict[str, Any]:
        """Load data from model JSON file.
        
        Returns:
            Model data dictionary
        """
        if not self.json_path.exists():
            return {}
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def get_model_id(self) -> Optional[str]:
        """Get model ID from JSON file.
        
        Returns:
            Model ID or None
        """
        data = self.load_from_json()
        return data.get('modelId')
    
    def save_model_metadata(
        self,
        api_data: Dict[str, Any],
        sha256: Optional[str] = None,
        overwrite: bool = False
    ) -> bool:
        """Save model metadata from API response.
        
        Args:
            api_data: API response data
            sha256: SHA256 hash to match
            overwrite: Whether to overwrite existing data
            
        Returns:
            True if successful, False otherwise
        """
        if not sha256:
            sha256 = self.generate_sha256()
        
        # Find matching model in API data
        for item in api_data.get('items', []):
            for version in item.get('modelVersions', []):
                for file_info in version.get('files', []):
                    file_sha256 = file_info.get('hashes', {}).get('SHA256', '')
                    if file_sha256.upper() == sha256.upper():
                        return self._save_metadata_for_version(item, version, overwrite)
        
        return False
    
    def _save_metadata_for_version(
        self,
        model_item: Dict[str, Any],
        version_info: Dict[str, Any],
        overwrite: bool
    ) -> bool:
        """Save metadata for a specific model version.
        
        Args:
            model_item: Model item from API
            version_info: Version info from API
            overwrite: Whether to overwrite existing data
            
        Returns:
            True if successful
        """
        # Extract metadata
        trained_words = version_info.get('trainedWords', [])
        base_model = version_info.get('baseModel', '')
        description = model_item.get('description', '')
        
        # Clean up trained words
        if isinstance(trained_words, list):
            trained_tags = ','.join(trained_words)
            trained_tags = re.sub(r'<[^>]*:[^>]*>', '', trained_tags)
            trained_tags = re.sub(r', ?', ', ', trained_tags)
            trained_tags = trained_tags.strip(', ')
        else:
            trained_tags = str(trained_words) if trained_words else ''
        
        # Normalize base model
        if base_model.startswith("SD 1"):
            base_model = "SD1"
        elif base_model.startswith("SD 2"):
            base_model = "SD2"
        elif base_model.startswith("SDXL"):
            base_model = "SDXL"
        else:
            base_model = "Other"
        
        # Clean description
        if description:
            description = self._clean_description(description)
        
        # Prepare data to save
        metadata = {}
        
        existing_data = self.load_from_json()
        if overwrite or "activation text" not in existing_data:
            metadata["activation text"] = trained_tags
        
        if overwrite or "sd version" not in existing_data:
            metadata["sd version"] = base_model
        
        if description and (overwrite or "description" not in existing_data):
            metadata["description"] = description
        
        # Add model IDs
        metadata["modelId"] = model_item.get('id')
        metadata["modelVersionId"] = version_info.get('id')
        
        if metadata:
            self.save_to_json(metadata, overwrite)
            return True
        
        return False
    
    def _clean_description(self, description: str) -> str:
        """Clean HTML description text.
        
        Args:
            description: Raw HTML description
            
        Returns:
            Cleaned text
        """
        try:
            soup = BeautifulSoup(description, 'html.parser')
            
            # Replace links with text + URL
            for link in soup.find_all('a', href=True):
                if not self._is_image_url(link['href']):
                    link_text = f"{link.text} {link['href']}"
                    link.replace_with(link_text)
            
            return soup.get_text()
            
        except ImportError:
            # BeautifulSoup not available, return as-is
            return description
    
    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is for an image
        """
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions)
    
    def save_preview_image(
        self,
        api_data: Dict[str, Any],
        sha256: Optional[str] = None,
        overwrite: bool = False
    ) -> Optional[Path]:
        """Save preview image for the model.
        
        Args:
            api_data: API response data
            sha256: SHA256 hash to match
            overwrite: Whether to overwrite existing image
            
        Returns:
            Path to saved image or None
        """
        if not sha256:
            sha256 = self.generate_sha256()
        
        preview_path = self.file_path.with_suffix('.preview.png')
        
        if preview_path.exists() and not overwrite:
            return preview_path
        
        # Find matching model and get first image
        for item in api_data.get('items', []):
            for version in item.get('modelVersions', []):
                for file_info in version.get('files', []):
                    file_sha256 = file_info.get('hashes', {}).get('SHA256', '')
                    if file_sha256.upper() == sha256.upper():
                        # Get first image from this version
                        for image in version.get('images', []):
                            if image.get('type') == 'image':
                                return self._download_image(image['url'], preview_path)
        
        return None
    
    def _download_image(self, url: str, save_path: Path) -> Optional[Path]:
        """Download image from URL.
        
        Args:
            url: Image URL
            save_path: Where to save the image
            
        Returns:
            Path to saved image or None if failed
        """
        try:
            # Get full resolution image
            url_with_width = re.sub(r'/width=\d+', '/width=512', url)
            
            response = requests.get(url_with_width, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return save_path
            
        except Exception as e:
            print(f"Failed to download preview image: {e}")
            return None


def get_model_type_from_path(file_path: Path) -> str:
    """Determine model type from file path.
    
    Args:
        file_path: Path to model file
        
    Returns:
        Model type string
    """
    path_parts = file_path.parts
    
    # Check parent directories for type hints
    for part in reversed(path_parts):
        part_lower = part.lower()
        
        if 'checkpoint' in part_lower or 'ckpt' in part_lower:
            return 'Checkpoint'
        elif 'lora' in part_lower:
            return 'LORA'
        elif 'locon' in part_lower or 'lycoris' in part_lower:
            return 'LoCon'
        elif 'dora' in part_lower:
            return 'DoRA'
        elif 'embedding' in part_lower or 'textual' in part_lower:
            return 'TextualInversion'
        elif 'controlnet' in part_lower:
            return 'Controlnet'
        elif 'vae' in part_lower:
            return 'VAE'
        elif 'upscaler' in part_lower or 'esrgan' in part_lower:
            return 'Upscaler'
    
    # Check file extension
    suffix = file_path.suffix.lower()
    if suffix in ['.ckpt', '.safetensors'] and file_path.stat().st_size > 1024**3:  # > 1GB
        return 'Checkpoint'
    elif suffix in ['.pt', '.safetensors']:
        return 'LORA'  # Default for smaller files
    
    return 'Other'


def clean_filename(filename: str) -> str:
    """Clean filename by removing illegal characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    import platform
    
    if platform.system() == "Windows":
        illegal_chars = r'[\\/:*?"<>|]'
    else:
        illegal_chars = r'[/]'
    
    name, ext = os.path.splitext(filename)
    clean_name = re.sub(illegal_chars, '', name)
    clean_name = re.sub(r'\s+', ' ', clean_name.strip())
    
    return f"{clean_name}{ext}"