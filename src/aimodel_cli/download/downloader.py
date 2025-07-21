"""Download functionality for CivitAI models."""

import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import requests

from ..api import CivitAIClient
from ..config import get_config
from ..models import ModelInfo, clean_filename


class DownloadError(Exception):
    """Exception raised for download errors."""
    pass


class Downloader:
    """Handle model downloads with HTTP."""
    
    def __init__(self):
        """Initialize downloader."""
        self.config = get_config()
        self.client = CivitAIClient()
    
    
    def download_model(
        self,
        download_url: str,
        save_path: Path,
        model_id: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """Download a model file.
        
        Args:
            download_url: URL to download from
            save_path: Where to save the file
            model_id: Model ID for authentication
            progress_callback: Function to call with progress updates
            
        Returns:
            True if download succeeded
        """
        # Get actual download URL
        direct_url = self.client.get_download_url(download_url, model_id)
        
        if direct_url == "auth_required":
            raise DownloadError(
                "This file requires authentication. Please set your CivitAI API key."
            )
        elif not direct_url:
            raise DownloadError("Could not get download URL")
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # HTTP download
        return self._download_with_http(direct_url, save_path, progress_callback)
    
    
    def _download_with_http(
        self,
        url: str,
        save_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """Download file using HTTP with resume support.
        
        Args:
            url: Download URL
            save_path: Where to save the file
            progress_callback: Function to call with progress updates
            
        Returns:
            True if download succeeded
        """
        headers = {}
        downloaded = 0
        
        # Check for partial download
        if save_path.exists():
            downloaded = save_path.stat().st_size
            headers['Range'] = f'bytes={downloaded}-'
        
        # Configure request session for better performance
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'AI-Model-CLI/1.0.0'
        })
        
        # Add proxy configuration if set
        proxy = self.config.get("proxy", "")
        if proxy:
            session.proxies = {'http': proxy, 'https': proxy}
        
        # Configure SSL verification
        if self.config.get("disable_ssl", False):
            session.verify = False
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        try:
            response = session.get(
                url,
                headers=headers,
                stream=True,
                timeout=self.config.get("timeout", 60)
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            if 'content-range' in response.headers:
                # Partial download - extract total size from range header
                range_info = response.headers['content-range']
                total_size = int(range_info.split('/')[-1])
            elif response.status_code == 206:
                # Partial content but no content-range header
                pass
            elif downloaded > 0:
                # Server doesn't support resume, start fresh
                downloaded = 0
                save_path.unlink(missing_ok=True)
                response.close()
                return self._download_with_http(url, save_path, progress_callback)
            
            mode = 'ab' if downloaded > 0 and response.status_code == 206 else 'wb'
            if mode == 'wb':
                downloaded = 0
                save_path.unlink(missing_ok=True)
            
            with open(save_path, mode) as f:
                start_time = time.time()
                last_update = 0
                chunk_size = 32768  # 32KB chunks for better performance
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        now = time.time()
                        if progress_callback and (now - last_update) > 0.5:
                            elapsed = now - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            
                            if total_size > 0:
                                progress = downloaded / total_size
                                speed_str = self._format_speed(speed)
                                remaining = total_size - downloaded
                                eta_str = self._format_eta(remaining, speed)
                                status_str = f"Downloading... {speed_str}, ETA: {eta_str}"
                                progress_callback(progress, status_str)
                            else:
                                # Unknown total size
                                speed_str = self._format_speed(speed)
                                downloaded_str = self._format_size(downloaded)
                                status_str = f"Downloading... {downloaded_str}, {speed_str}"
                                progress_callback(0.0, status_str)
                            
                            last_update = now
            
            if progress_callback:
                progress_callback(1.0, "Download completed")
            
            return True
            
        except requests.exceptions.RequestException as e:
            raise DownloadError(f"HTTP download failed: {e}")
        except Exception as e:
            raise DownloadError(f"Download failed: {e}")
        finally:
            session.close()
    
    def _format_speed(self, bytes_per_sec: float) -> str:
        """Format download speed for display.
        
        Args:
            bytes_per_sec: Speed in bytes per second
            
        Returns:
            Formatted speed string
        """
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bytes_per_sec < 1024:
                return f"{bytes_per_sec:.1f} {unit}"
            bytes_per_sec /= 1024
        return f"{bytes_per_sec:.1f} TB/s"
    
    def _format_size(self, bytes_count: int) -> str:
        """Format file size for display.
        
        Args:
            bytes_count: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024
        return f"{bytes_count:.1f} PB"
    
    def _format_eta(self, remaining_bytes: int, speed: float) -> str:
        """Format ETA for display.
        
        Args:
            remaining_bytes: Bytes left to download
            speed: Current speed in bytes per second
            
        Returns:
            Formatted ETA string
        """
        if speed <= 0:
            return "∞"
        
        eta_seconds = remaining_bytes / speed
        
        if eta_seconds < 60:
            return f"{eta_seconds:.0f}s"
        elif eta_seconds < 3600:
            return f"{eta_seconds/60:.0f}m"
        else:
            hours = eta_seconds // 3600
            minutes = (eta_seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    


def download_model_by_id(
    model_id: int,
    version_id: Optional[int] = None,
    file_id: Optional[int] = None,
    save_dir: Optional[Path] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, Optional[Path]]:
    """Download a model by ID.
    
    Args:
        model_id: CivitAI model ID
        version_id: Specific version ID (latest if None)
        file_id: Specific file ID (primary if None)
        save_dir: Directory to save to (config default if None)
        progress_callback: Function to call with progress updates
        
    Returns:
        Tuple of (success, saved_file_path)
    """
    client = CivitAIClient()
    config = get_config()
    
    # Get model information
    model_data = client.get_model_by_id(model_id)
    if isinstance(model_data, str):
        raise DownloadError(f"Failed to get model info: {model_data}")
    
    if not model_data.get('items'):
        raise DownloadError("Model not found")
    
    model_item = model_data['items'][0]
    versions = model_item.get('modelVersions', [])
    
    if not versions:
        raise DownloadError("No versions available")
    
    # Select version
    if version_id:
        version = next((v for v in versions if v['id'] == version_id), None)
        if not version:
            raise DownloadError(f"Version {version_id} not found")
    else:
        version = versions[0]  # Latest version
    
    # Select file
    files = version.get('files', [])
    if not files:
        raise DownloadError("No files available")
    
    if file_id:
        file_info = next((f for f in files if f['id'] == file_id), None)
        if not file_info:
            raise DownloadError(f"File {file_id} not found")
    else:
        # Get primary file or first file
        file_info = next((f for f in files if f.get('primary')), files[0])
    
    # Determine save path
    if save_dir is None:
        # Use model-type-specific path
        model_type = model_item.get('type', 'Other')
        save_dir = config.get_model_path(model_type)
    
    filename = clean_filename(file_info['name'])
    save_path = save_dir / filename
    
    # Download
    downloader = Downloader()
    success = downloader.download_model(
        file_info['downloadUrl'],
        save_path,
        model_id,
        progress_callback
    )
    
    if success:
        # Save metadata
        model_info = ModelInfo(save_path)
        sha256 = file_info.get('hashes', {}).get('SHA256')
        if sha256:
            model_info.save_to_json({'sha256': sha256})
        
        model_info.save_model_metadata(model_data, sha256)
        
        # Save preview if configured
        if config.get("save_preview", True):
            model_info.save_preview_image(model_data, sha256)
        
        return True, save_path
    else:
        return False, None