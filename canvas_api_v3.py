"""
Canvas API v3 Core Client

This module provides the core CanvasAPIClient class and common utilities
for interacting with the GoCanvas API v3. This is the central module that
other canvas_api_*_v3.py files import from.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import requests

# ============================================================================
# Configuration
# ============================================================================

# Global logging configuration
LOG_CONFIG = {
    'level': 'DEBUG',  # Default log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'file': 'canvas_api_v3.log',  # Log file name
}

# API Configuration file path
API_CONFIG_FILE = 'canvas_api_config.json'

# API Base URL
API_BASE_URL = "https://www.gocanvas.com/api/v3"

# Initialize logger (basic setup for config loading)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration Loading
# ============================================================================

def load_api_config(config_file: str = None) -> Dict:
    """
    Load API configuration from JSON file.
    
    Args:
        config_file: Path to config file (default: canvas_api_config.json)
        
    Returns:
        Dictionary with API configuration
    """
    if config_file is None:
        config_file = API_CONFIG_FILE
    
    default_config = {
        'username': None,
        'password': None,
        'bearer_token': None,
        'form_id': None
    }
    
    if not os.path.exists(config_file):
        # Silently create default config file (logger may not be fully configured yet)
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file: {config_file}")
        except Exception as e:
            print(f"Could not create config file: {e}")
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Merge with defaults to ensure all keys exist
        default_config.update(config)
        return default_config
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config file '{config_file}': {e}")
        return default_config
    except Exception as e:
        print(f"Error loading config file '{config_file}': {e}")
        return default_config

# Load API configuration from file
API_CONFIG = load_api_config()

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(log_file=None, log_level='INFO'):
    """Set up logging configuration."""
    if log_file is None:
        log_file = LOG_CONFIG.get('file', 'canvas_api_v3.log')
    
    # Convert string level to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    logging.root.handlers.clear()
    
    # Create handlers
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set formatter on handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.root.setLevel(level)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)
    
    # Set logger level
    logger.setLevel(level)
    
    logger.info(f"Logging initialized. Level: {log_level}, File: {log_file}")

# ============================================================================
# Canvas API Client
# ============================================================================

class CanvasAPIClient:
    """Client for interacting with GoCanvas API v3."""
    
    BASE_URL = API_BASE_URL
    
    def __init__(self, username: str = None, password: str = None, bearer_token: str = None):
        """
        Initialize Canvas API client.
        
        Args:
            username: GoCanvas username for Basic Auth
            password: GoCanvas password for Basic Auth
            bearer_token: OAuth Bearer token (alternative to username/password)
        """
        if bearer_token:
            self.auth_type = 'bearer'
            self.bearer_token = bearer_token
            self.username = None
            self.password = None
        elif username and password:
            self.auth_type = 'basic'
            self.username = username
            self.password = password
            self.bearer_token = None
        else:
            raise ValueError("Either (username and password) or bearer_token must be provided")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        return headers
    
    def _get_auth(self) -> tuple:
        """Get authentication tuple for Basic Auth."""
        if self.auth_type == 'basic':
            return (self.username, self.password)
        return None
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get Authorization header for Bearer token."""
        if self.auth_type == 'bearer':
            return {'Authorization': f'Bearer {self.bearer_token}'}
        return {}
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> requests.Response:
        """
        Make an API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            
        Returns:
            Response object
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        headers.update(self._get_auth_header())
        
        auth = self._get_auth()
        
        logger.debug(f"Making {method} request to {url}")
        if params:
            logger.debug(f"Query parameters: {params}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, auth=auth, headers=headers, params=params, json=data, timeout=30)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, auth=auth, headers=headers, params=params, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, auth=auth, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

# ============================================================================
# Utility Functions
# ============================================================================

def get_date_range(days: int = 7) -> tuple:
    """
    Get start and end dates for the last N days.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.replace('/', '_').replace('\\', '_')
