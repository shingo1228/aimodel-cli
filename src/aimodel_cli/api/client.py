"""CivitAI API client implementation."""

import hashlib
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import get_config


class CivitAIClient:
    """Client for interacting with CivitAI API."""
    
    def __init__(self):
        """Initialize CivitAI API client."""
        self.config = get_config()
        self.base_url = "https://civitai.com/api/v1"
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Connection": "keep-alive",
            "Sec-Ch-Ua-Platform": "Windows",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }
        
        if referer:
            headers['Referer'] = f"https://civitai.com/models/{referer}"
        
        api_key = self.config.get("api_key")
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        return headers
    
    def _get_proxies(self) -> Dict[str, str]:
        """Get proxy configuration."""
        proxy = self.config.get("proxy")
        if proxy:
            return {
                'http': proxy,
                'https': proxy,
            }
        return {}
    
    def _make_request(self, url: str, **kwargs) -> Union[Dict[str, Any], str]:
        """Make HTTP request with error handling."""
        headers = self._get_headers(kwargs.pop('referer', None))
        proxies = self._get_proxies()
        timeout = self.config.get("timeout", 60)
        verify_ssl = not self.config.get("disable_ssl", False)
        
        try:
            response = self.session.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=timeout,
                verify=verify_ssl,
                **kwargs
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return "invalid_json"
                
        except requests.exceptions.Timeout:
            return "timeout"
        except requests.exceptions.ConnectionError:
            return "connection_error"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return "not_found"
            elif e.response.status_code == 503:
                return "service_unavailable"
            else:
                return "http_error"
        except Exception:
            return "unknown_error"
    
    def search_models(
        self,
        query: Optional[str] = None,
        content_types: Optional[List[str]] = None,
        sort_by: str = "Most Downloaded",
        period: str = "All Time",
        base_models: Optional[List[str]] = None,
        nsfw: bool = False,
        limit: int = 20,
        page: int = 1
    ) -> Union[Dict[str, Any], str]:
        """Search for models on CivitAI.
        
        Args:
            query: Search query
            content_types: List of content types to filter by
            sort_by: Sort order
            period: Time period for sorting
            base_models: List of base models to filter by
            nsfw: Include NSFW content
            limit: Number of results per page
            page: Page number
            
        Returns:
            API response or error string
        """
        params = {
            'limit': limit,
            'sort': sort_by,
            'period': period.replace(" ", "") if period else None,
            'nsfw': "true" if nsfw else "false"
        }
        
        if content_types:
            params["types"] = content_types
        
        if query:
            if "civitai.com" in query:
                # Extract model ID from URL
                match = re.search(r'models/(\d+)', query)
                if match:
                    params = {'ids': match.group(1)}
            else:
                params["query"] = query
        
        if base_models:
            params["baseModels"] = base_models
        
        # Build query string
        query_parts = []
        for key, value in params.items():
            if isinstance(value, list):
                for item in value:
                    query_parts.append((key, item))
            else:
                query_parts.append((key, value))
        
        query_string = urllib.parse.urlencode(query_parts, doseq=True, quote_via=urllib.parse.quote)
        url = f"{self.base_url}/models?{query_string}"
        
        return self._make_request(url)
    
    def get_model_by_id(self, model_id: int, nsfw: bool = True) -> Union[Dict[str, Any], str]:
        """Get model details by ID.
        
        Args:
            model_id: Model ID
            nsfw: Include NSFW content
            
        Returns:
            API response or error string
        """
        params = {
            'ids': model_id,
            'nsfw': "true" if nsfw else "false"
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"{self.base_url}/models?{query_string}"
        
        return self._make_request(url)
    
    def get_model_version(self, version_id: int) -> Union[Dict[str, Any], str]:
        """Get model version details.
        
        Args:
            version_id: Version ID
            
        Returns:
            API response or error string
        """
        url = f"{self.base_url}/model-versions/{version_id}"
        return self._make_request(url)
    
    def get_model_by_hash(self, sha256: str) -> Union[Dict[str, Any], str]:
        """Get model by SHA256 hash.
        
        Args:
            sha256: SHA256 hash
            
        Returns:
            API response or error string
        """
        url = f"{self.base_url}/model-versions/by-hash/{sha256}"
        return self._make_request(url)
    
    def get_download_url(self, file_url: str, model_id: Optional[int] = None) -> Optional[str]:
        """Get direct download URL for a file.
        
        Args:
            file_url: File download URL from API
            model_id: Model ID for headers
            
        Returns:
            Direct download URL or None if failed
        """
        headers = self._get_headers(model_id)
        proxies = self._get_proxies()
        verify_ssl = not self.config.get("disable_ssl", False)
        
        try:
            response = self.session.get(
                file_url,
                headers=headers,
                proxies=proxies,
                allow_redirects=False,
                verify=verify_ssl
            )
            
            if 300 <= response.status_code <= 308:
                if "login?returnUrl" in response.text and "reason=download-auth" in response.text:
                    return "auth_required"
                
                return response.headers.get("Location")
            
        except Exception:
            pass
        
        return None
    
    def filter_early_access(self, models_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out early access models if configured.
        
        Args:
            models_data: Models data from API
            
        Returns:
            Filtered models data
        """
        if not self.config.get("hide_early_access", True):
            return models_data
        
        current_time = datetime.now(timezone.utc)
        filtered_items = []
        
        for item in models_data.get('items', []):
            versions_to_keep = []
            
            for version in item.get('modelVersions', []):
                if not version.get('files'):
                    continue
                
                early_access_deadline_str = version.get('earlyAccessDeadline')
                if early_access_deadline_str:
                    try:
                        early_access_deadline = datetime.strptime(
                            early_access_deadline_str, 
                            "%Y-%m-%dT%H:%M:%S.%fZ"
                        ).replace(tzinfo=timezone.utc)
                        if current_time <= early_access_deadline:
                            continue
                    except ValueError:
                        # If we can't parse the date, include the version
                        pass
                
                versions_to_keep.append(version)
            
            if versions_to_keep:
                item['modelVersions'] = versions_to_keep
                filtered_items.append(item)
        
        models_data['items'] = filtered_items
        return models_data
    
    def search_by_hash(self, hash_value: str) -> Union[Dict[str, Any], str]:
        """Search for model by SHA256 hash.
        
        Args:
            hash_value: SHA256 hash of the model file
            
        Returns:
            API response or error string
        """
        try:
            url = f"{self.base_url}/model-versions/by-hash/{hash_value}"
            headers = self._get_headers()
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return "Model not found with the provided hash"
            else:
                return f"API error: {response.status_code}"
                
        except Exception as e:
            return f"Request failed: {str(e)}"
    
    @staticmethod
    def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read at a time
            
        Returns:
            SHA256 hash as uppercase hex string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest().upper()