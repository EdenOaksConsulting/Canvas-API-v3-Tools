"""
Canvas API v3 Client and Submission Retrieval Tool

This module provides a client for interacting with the GoCanvas API v3,
including retrieving submissions and forms, and transforming submissions
from v3 format to v2 format.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import requests

# Import transform function from canvas_transform_v3_to_v2.py
try:
    from canvas_transform_v3_to_v2 import transform_v3_to_v2
except ImportError:
    transform_v3_to_v2 = None

# ============================================================================
# Configuration
# ============================================================================

# Global logging configuration
LOG_CONFIG = {
    'level': 'INFO',  # Default log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
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
    
    def get_submissions(self, start_date: str = None, end_date: str = None, 
                       form_id: int = None, page: int = 1, per_page: int = 100) -> Dict:
        """
        Retrieve submissions from GoCanvas API.
        
        Args:
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            form_id: Filter by form ID (optional)
            page: Page number for pagination
            per_page: Number of results per page (max 100)
            
        Returns:
            Dictionary containing submissions and pagination info
        """
        endpoint = "submissions"
        params = {
            'page': page,
            'per_page': min(per_page, 100)  # API limit is 100
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if form_id:
            params['form_id'] = form_id
        
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def get_all_submissions(self, start_date: str = None, end_date: str = None, 
                           form_id: int = None) -> List[Dict]:
        """
        Retrieve all submissions with automatic pagination.
        
        Args:
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            form_id: Filter by form ID (optional)
            
        Returns:
            List of all submissions
        """
        all_submissions = []
        page = 1
        per_page = 100
        
        logger.info(f"Retrieving submissions from {start_date or 'beginning'} to {end_date or 'now'}")
        if form_id:
            logger.info(f"Filtering by form_id: {form_id}")
        
        while True:
            logger.debug(f"Fetching page {page}...")
            result = self.get_submissions(
                start_date=start_date,
                end_date=end_date,
                form_id=form_id,
                page=page,
                per_page=per_page
            )
            
            # Handle different response formats
            if isinstance(result, list):
                submissions = result
                has_more = len(submissions) == per_page
            elif isinstance(result, dict):
                submissions = result.get('submissions', result.get('data', []))
                # Check for pagination info
                if 'pagination' in result:
                    pagination = result['pagination']
                    has_more = pagination.get('current_page', page) < pagination.get('total_pages', 1)
                elif 'meta' in result:
                    meta = result['meta']
                    has_more = meta.get('current_page', page) < meta.get('total_pages', 1)
                else:
                    # If no pagination info, assume more pages if we got a full page
                    has_more = len(submissions) == per_page
            else:
                submissions = []
                has_more = False
            
            all_submissions.extend(submissions)
            logger.info(f"Retrieved {len(submissions)} submissions from page {page} (total: {len(all_submissions)})")
            
            if not has_more or len(submissions) == 0:
                break
            
            page += 1
        
        logger.info(f"Total submissions retrieved: {len(all_submissions)}")
        return all_submissions
    
    def get_submission_by_id(self, submission_id: int) -> Dict:
        """
        Retrieve a single submission by ID.
        
        Args:
            submission_id: The unique submission ID
            
        Returns:
            Dictionary containing the full submission data
        """
        endpoint = f"submissions/{submission_id}"
        response = self._make_request('GET', endpoint)
        return response.json()
    
    def get_form_by_id(self, form_id: int) -> Dict:
        """
        Retrieve a form by ID (nested structure with sections, sheets, entries).
        
        Args:
            form_id: The unique form ID
            
        Returns:
            Dictionary containing the full nested form data
        """
        endpoint = f"forms/{form_id}"
        response = self._make_request('GET', endpoint)
        return response.json()

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

# ============================================================================
# Main Application Logic
# ============================================================================

def retrieve_form(client: CanvasAPIClient, form_id: int, output_dir: str) -> Optional[Dict]:
    """
    Retrieve a form from the API and save it to a file.
    
    Args:
        client: Canvas API client instance
        form_id: Form ID to retrieve
        output_dir: Output directory path
        
    Returns:
        Form data dictionary if successful, None otherwise
    """
    try:
        logger.info(f"Retrieving form ID {form_id}...")
        form_data = client.get_form_by_id(form_id)
        
        # Create filename using form ID and name
        form_name = form_data.get('name', 'Unknown')
        filename = f"form_{form_id}_{sanitize_filename(form_name)}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(form_data, f, indent=3, ensure_ascii=False)
        
        logger.info(f"Saved form {form_id} ({form_name}) to {filepath}")
        return form_data
        
    except Exception as e:
        logger.error(f"Error retrieving form {form_id}: {e}")
        return None

def process_submission(client: CanvasAPIClient, submission_summary: Dict, 
                      output_dir: str, form_data: Optional[Dict] = None) -> tuple:
    """
    Process a single submission: retrieve, save, and optionally transform.
    
    Args:
        client: Canvas API client instance
        submission_summary: Submission summary from list endpoint
        output_dir: Output directory path
        form_data: Optional form data for transformation
        
    Returns:
        Tuple of (success: bool, transformed: bool)
    """
    submission_id = submission_summary.get('id')
    if not submission_id:
        logger.warning(f"Submission has no ID, skipping")
        return False, False
    
    try:
        # Retrieve full submission
        full_submission = client.get_submission_by_id(submission_id)
        
        # Create filename
        submission_number = submission_summary.get('submission_number', '')
        if submission_number:
            filename = f"submission_{submission_id}_{submission_number}.json"
        else:
            filename = f"submission_{submission_id}.json"
        
        filepath = os.path.join(output_dir, filename)
        
        # Save v3 submission
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_submission, f, indent=3, ensure_ascii=False)
        
        logger.debug(f"Saved submission {submission_id} to {filepath}")
        
        # Transform to v2 format if form_data is available
        transformed = False
        if form_data and transform_v3_to_v2:
            try:
                logger.info(f"Transforming submission {submission_id} to v2 format...")
                v2_data = transform_v3_to_v2(full_submission, form_data)
                
                # Create v2 filename
                if submission_number:
                    v2_filename = f"submission_{submission_id}_{submission_number}_v2.json"
                else:
                    v2_filename = f"submission_{submission_id}_v2.json"
                
                v2_filepath = os.path.join(output_dir, v2_filename)
                
                # Save v2 file
                with open(v2_filepath, 'w', encoding='utf-8') as f:
                    json.dump(v2_data, f, indent=3, ensure_ascii=False)
                
                logger.info(f"Saved transformed submission {submission_id} to {v2_filepath}")
                transformed = True
                
            except Exception as e:
                logger.error(f"Error transforming submission {submission_id}: {e}")
        
        return True, transformed
        
    except Exception as e:
        logger.error(f"Error processing submission {submission_id}: {e}")
        return False, False

def main(username: str = None, password: str = None, bearer_token: str = None,
         days: int = 7, form_id: int = None, output_file: str = None,
         log_file: str = None, log_level: str = None):
    """
    Retrieve submissions from GoCanvas API for the last N days.
    
    Args:
        username: GoCanvas username for Basic Auth
        password: GoCanvas password for Basic Auth
        bearer_token: OAuth Bearer token (alternative to username/password)
        days: Number of days to look back (default: 7)
        form_id: Optional form ID to filter submissions
        output_file: Path for output directory (each submission saved to unique file)
        log_file: Path for log file
        log_level: Logging level
    """
    # Set up logging
    if log_level is None:
        log_level = LOG_CONFIG.get('level', 'INFO')
    if log_file is None:
        log_file = LOG_CONFIG.get('file', 'canvas_api_v3.log')
    setup_logging(log_file, log_level)
    
    # Set default output directory
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f'canvas_submissions_{timestamp}'
    else:
        # If output_file is provided, use it as directory name
        output_dir = output_file.replace('.json', '') if output_file.endswith('.json') else output_file
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    # Get date range
    start_date, end_date = get_date_range(days)
    logger.info(f"Retrieving submissions from last {days} days")
    logger.info(f"Date range: {start_date} to {end_date}")
    logger.info(f"Output directory: {output_dir}")
    
    # Initialize API client
    try:
        client = CanvasAPIClient(username=username, password=password, bearer_token=bearer_token)
        logger.info("Canvas API client initialized")
    except ValueError as e:
        logger.error(f"Failed to initialize API client: {e}")
        return
    
    # Retrieve submission list
    try:
        submission_list = client.get_all_submissions(
            start_date=start_date,
            end_date=end_date,
            form_id=form_id
        )
        
        if not submission_list:
            logger.warning("No submissions found for the specified date range")
            return
        
        logger.info(f"Found {len(submission_list)} submissions. Retrieving full details for each...")
        
        # Retrieve form from API_CONFIG (needed for transformation)
        config_form_id = API_CONFIG.get('form_id')
        form_data = None
        
        if config_form_id:
            form_data = retrieve_form(client, config_form_id, output_dir)
            if not form_data and transform_v3_to_v2:
                logger.warning("Form retrieval failed. Transformation will be skipped.")
        else:
            logger.warning("No form_id specified in API_CONFIG. Form retrieval and transformation will be skipped.")
        
        # Process each submission
        successful = 0
        failed = 0
        transformed = 0
        transform_failed = 0
        
        for idx, submission_summary in enumerate(submission_list, 1):
            logger.info(f"Processing submission {idx}/{len(submission_list)}: ID {submission_summary.get('id')}")
            success, was_transformed = process_submission(client, submission_summary, output_dir, form_data)
            
            if success:
                successful += 1
                if was_transformed:
                    transformed += 1
                elif form_data and transform_v3_to_v2:
                    transform_failed += 1
            else:
                failed += 1
        
        logger.info("Retrieval complete!")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Log file: {log_file}")
        
        # Print summary
        logger.info(f"\nSummary:")
        logger.info(f"  Total submissions found: {len(submission_list)}")
        logger.info(f"  Submissions successfully retrieved: {successful}")
        logger.info(f"  Submissions failed: {failed}")
        if form_data and transform_v3_to_v2:
            logger.info(f"  Submissions transformed to v2: {transformed}")
            if transform_failed > 0:
                logger.info(f"  Transformations failed: {transform_failed}")
        if config_form_id:
            logger.info(f"  Form retrieved: {config_form_id}")
        logger.info(f"  Date range: {start_date} to {end_date}")
        if form_id:
            logger.info(f"  Form ID filter: {form_id}")
        
    except Exception as e:
        logger.error(f"Error retrieving submissions: {e}", exc_info=True)
        raise

# ============================================================================
# Command Line Interface
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Retrieve submissions from GoCanvas API for the last N days',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using Basic Auth (username/password)
  python canvas_api_v3.py -u user@example.com -p password
  
  # Using Bearer token
  python canvas_api_v3.py --bearer-token YOUR_TOKEN
  
  # Retrieve last 14 days
  python canvas_api_v3.py -u user@example.com -p password --days 14
  
  # Filter by form ID
  python canvas_api_v3.py -u user@example.com -p password --form-id 12345
  
  # Custom output directory
  python canvas_api_v3.py -u user@example.com -p password -o my_submissions
        """
    )
    
    # Authentication options (mutually exclusive)
    # Only require if no default credentials are configured
    has_default_auth = (API_CONFIG.get('username') and API_CONFIG.get('password')) or API_CONFIG.get('bearer_token')
    auth_group = parser.add_mutually_exclusive_group(required=not has_default_auth)
    auth_group.add_argument(
        '-u', '--username',
        dest='username',
        default=API_CONFIG.get('username'),
        help='GoCanvas username for Basic Auth (default: from API_CONFIG)'
    )
    auth_group.add_argument(
        '--bearer-token',
        dest='bearer_token',
        default=API_CONFIG.get('bearer_token'),
        help='OAuth Bearer token for authentication (default: from API_CONFIG)'
    )
    
    parser.add_argument(
        '-p', '--password',
        dest='password',
        default=API_CONFIG.get('password'),
        help='GoCanvas password (required if using username, default: from API_CONFIG)'
    )
    
    parser.add_argument(
        '-d', '--days',
        dest='days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    
    parser.add_argument(
        '--form-id',
        dest='form_id',
        type=int,
        default=API_CONFIG.get('form_id'),
        help='Filter submissions by form ID (optional)'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        default=None,
        help='Path for output directory (default: canvas_submissions_TIMESTAMP). Each submission is saved to a unique file.'
    )
    
    parser.add_argument(
        '--log-file',
        dest='log_file',
        default=None,
        help='Path for log file (default: canvas_api_v3.log)'
    )
    
    parser.add_argument(
        '--log-level',
        dest='log_level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=None,
        help='Logging level (default: from LOG_CONFIG or INFO)'
    )
    
    parser.add_argument(
        '--config-file',
        dest='config_file',
        default=None,
        help=f'Path to API config file (default: {API_CONFIG_FILE})'
    )
    
    args = parser.parse_args()
    
    # Reload config if custom config file specified
    if args.config_file:
        config = load_api_config(args.config_file)
    else:
        config = API_CONFIG
    
    # Determine authentication - use command line args if provided, otherwise use defaults
    username = args.username if args.username else config.get('username')
    password = args.password if args.password else config.get('password')
    bearer_token = args.bearer_token if args.bearer_token else config.get('bearer_token')
    
    # Validate authentication
    if username and not password:
        parser.error("Password is required when using username authentication")
    
    # Ensure we have some form of authentication
    if not bearer_token and not (username and password):
        parser.error("Authentication required: provide --bearer-token or -u/-p, or configure API_CONFIG")
    
    main(
        username=username,
        password=password,
        bearer_token=bearer_token,
        days=args.days,
        form_id=args.form_id,
        output_file=args.output_file,
        log_file=args.log_file,
        log_level=args.log_level
    )

