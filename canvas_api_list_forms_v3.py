"""
List All Forms from GoCanvas API v3

This script retrieves and lists all forms from the GoCanvas API v3.
It uses the existing canvas_api_config.json for authentication.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Union

# Import CanvasAPIClient from canvas_api_v3
try:
    from canvas_api_v3 import CanvasAPIClient, load_api_config, setup_logging, API_CONFIG_FILE, LOG_CONFIG
except ImportError as e:
    print(f"Error importing from canvas_api_v3: {e}")
    print("Make sure canvas_api_v3.py is in the same directory.")
    sys.exit(1)

# Initialize logger
logger = logging.getLogger(__name__)


def get_forms(client: CanvasAPIClient, status: str = None, page: int = 1, per_page: int = 100,
              all_pages: bool = False) -> Union[List[Dict], Dict]:
    """
    Retrieve all forms from GoCanvas API.
    
    Args:
        client: Canvas API client instance
        status: Status filter (optional, e.g., 'new', 'pending', 'published', 'archived', or 'testing')
        page: Page number for pagination (ignored if all_pages=True)
        per_page: Number of results per page (max 100, ignored if all_pages=True)
        all_pages: If True, automatically paginate and return all forms as a list.
                  If False, return a single page result (dict or list depending on API response)
        
    Returns:
        If all_pages=True: List of all forms
        If all_pages=False: Dictionary containing forms and pagination info (or list if API returns list)
    """
    def _fetch_page(page_num: int, per_page_size: int) -> Union[Dict, List]:
        """Helper method to fetch a single page of forms."""
        endpoint = "forms"
        params = {
            'page': page_num,
            'per_page': min(per_page_size, 100)  # API limit is 100
        }
        
        if status:
            params['status'] = status
        
        response = client._make_request('GET', endpoint, params=params)
        return response.json()
    
    # If all_pages is False, return single page result
    if not all_pages:
        return _fetch_page(page, per_page)
    
    # Otherwise, paginate through all pages
    all_forms = []
    current_page = 1
    per_page_size = 100
    
    logger.info(f"Retrieving all forms" + (f" with status: {status}" if status else ""))
    
    while True:
        logger.debug(f"Fetching forms page {current_page}...")
        result = _fetch_page(current_page, per_page_size)
        
        # Handle different response formats
        if isinstance(result, list):
            forms = result
            has_more = len(forms) == per_page_size
        elif isinstance(result, dict):
            forms = result.get('forms', result.get('data', []))
            # Check for pagination info
            if 'pagination' in result:
                pagination = result['pagination']
                has_more = pagination.get('current_page', current_page) < pagination.get('total_pages', 1)
            elif 'meta' in result:
                meta = result['meta']
                has_more = meta.get('current_page', current_page) < meta.get('total_pages', 1)
            else:
                # If no pagination info, assume more pages if we got a full page
                has_more = len(forms) == per_page_size
        else:
            forms = []
            has_more = False
        
        all_forms.extend(forms)
        logger.info(f"Retrieved {len(forms)} forms from page {current_page} (total: {len(all_forms)})")
        
        if not has_more or len(forms) == 0:
            break
        
        current_page += 1
    
    logger.info(f"Total forms retrieved: {len(all_forms)}")
    return all_forms


def main(username: str = None, password: str = None, bearer_token: str = None,
         status: str = None, output_file: str = None, output_to_screen: bool = False,
         log_file: str = None, log_level: str = None, config_file: str = None):
    """
    List all forms from GoCanvas API.
    
    Args:
        username: GoCanvas username for Basic Auth
        password: GoCanvas password for Basic Auth
        bearer_token: OAuth Bearer token (alternative to username/password)
        status: Status filter (optional, e.g., 'new', 'pending', 'published', 'archived', or 'testing')
        output_file: Path for output file (default: canvas_forms_TIMESTAMP.json, ignored if output_to_screen=True)
        output_to_screen: If True, output to console instead of file
        log_file: Path for log file
        log_level: Logging level
        config_file: Path to API config file
    """
    # Load config if provided
    if config_file:
        config = load_api_config(config_file)
    else:
        config = load_api_config()
    
    # Use provided credentials or fall back to config
    username = username or config.get('username')
    password = password or config.get('password')
    bearer_token = bearer_token or config.get('bearer_token')
    
    # Set up logging
    if log_level is None:
        log_level = LOG_CONFIG.get('level', 'INFO')
    if log_file is None:
        log_file = LOG_CONFIG.get('file', 'list_forms.log')
    setup_logging(log_file, log_level)
    
    # Initialize API client
    try:
        client = CanvasAPIClient(username=username, password=password, bearer_token=bearer_token)
        logger.info("Canvas API client initialized")
    except ValueError as e:
        logger.error(f"Failed to initialize API client: {e}")
        print(f"Error: {e}")
        return
    
    # Retrieve forms list
    try:
        logger.info("Retrieving all forms" + (f" with status: {status}" if status else ""))
        forms_list = get_forms(client, status=status, all_pages=True)
        
        if not forms_list:
            logger.warning("No forms found")
            if output_to_screen:
                print("No forms found")
            return
        
        logger.info(f"Found {len(forms_list)} forms")
        
        # Format output as JSON string
        output_json = json.dumps(forms_list, indent=3, ensure_ascii=False)
        
        if output_to_screen:
            # Output to console
            print(output_json)
            logger.info(f"Output {len(forms_list)} forms to console")
        else:
            # Save to file
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'canvas_forms_{timestamp}.json'
            
            # Write to working directory if output_file is a relative path (not absolute)
            if not os.path.isabs(output_file):
                # Create working directory if it doesn't exist
                working_dir = 'working'
                if not os.path.exists(working_dir):
                    os.makedirs(working_dir)
                output_file = os.path.join(working_dir, output_file)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            
            logger.info(f"Saved {len(forms_list)} forms to {output_file}")
            print(f"Saved {len(forms_list)} forms to {output_file}")
        
        # Print summary
        logger.info("\nSummary:")
        logger.info(f"  Total forms found: {len(forms_list)}")
        if status:
            logger.info(f"  Status filter: {status}")
        if not output_to_screen:
            logger.info(f"  Output file: {output_file}")
        
        # Print form IDs and names for quick reference
        logger.info("\nForms:")
        for form in forms_list:
            form_id = form.get('id', 'N/A')
            form_name = form.get('name', 'Unknown')
            form_status = form.get('status', 'N/A')
            logger.info(f"  ID: {form_id}, Name: {form_name}, Status: {form_status}")
        
    except Exception as e:
        logger.error(f"Error retrieving forms: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='List all forms from GoCanvas API v3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using config file (canvas_api_config.json)
  python list_forms.py
  
  # Using Basic Auth (username/password)
  python list_forms.py -u user@example.com -p password
  
  # Using Bearer token
  python list_forms.py --bearer-token YOUR_TOKEN
  
  # Output to screen/console
  python list_forms.py --output-to-screen
  
  # Filter by status
  python list_forms.py --status published
  
  # Custom output file
  python list_forms.py -o my_forms.json
  
  # Custom config file
  python list_forms.py --config-file my_config.json
        """
    )
    
    # Authentication options (mutually exclusive)
    # Only require if no default credentials are configured
    default_config = load_api_config()
    has_default_auth = (default_config.get('username') and default_config.get('password')) or default_config.get('bearer_token')
    auth_group = parser.add_mutually_exclusive_group(required=not has_default_auth)
    auth_group.add_argument(
        '-u', '--username',
        dest='username',
        default=None,
        help='GoCanvas username for Basic Auth (default: from config file)'
    )
    auth_group.add_argument(
        '--bearer-token',
        dest='bearer_token',
        default=None,
        help='OAuth Bearer token for authentication (default: from config file)'
    )
    
    parser.add_argument(
        '-p', '--password',
        dest='password',
        default=None,
        help='GoCanvas password (required if using username, default: from config file)'
    )
    
    parser.add_argument(
        '--status',
        dest='status',
        choices=['new', 'pending', 'published', 'archived', 'testing'],
        default=None,
        help='Filter forms by status'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        default=None,
        help='Path for output file (default: canvas_forms_TIMESTAMP.json, ignored if --output-to-screen is used)'
    )
    
    parser.add_argument(
        '--output-to-screen',
        dest='output_to_screen',
        action='store_true',
        help='Output results to console/screen instead of file'
    )
    
    parser.add_argument(
        '--log-file',
        dest='log_file',
        default=None,
        help='Path for log file (default: list_forms.log)'
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
    
    # Validate authentication
    if args.username and not args.password:
        parser.error("Password is required when using username authentication")
    
    # Ensure we have some form of authentication
    config = load_api_config(args.config_file) if args.config_file else default_config
    username = args.username if args.username else config.get('username')
    password = args.password if args.password else config.get('password')
    bearer_token = args.bearer_token if args.bearer_token else config.get('bearer_token')
    
    if not bearer_token and not (username and password):
        parser.error("Authentication required: provide --bearer-token or -u/-p, or configure in config file")
    
    main(
        username=username,
        password=password,
        bearer_token=bearer_token,
        status=args.status,
        output_file=args.output_file,
        output_to_screen=args.output_to_screen,
        log_file=args.log_file,
        log_level=args.log_level,
        config_file=args.config_file
    )
