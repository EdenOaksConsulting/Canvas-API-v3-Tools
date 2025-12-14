"""
Get Form by ID from GoCanvas API v3

This script retrieves a specific form by ID from the GoCanvas API v3.
It uses the existing canvas_api_config.json for authentication.
"""

import argparse
import json
import logging
import os
import sys
from typing import Optional, Dict

# Import CanvasAPIClient from canvas_api_v3
try:
    from canvas_api_v3 import CanvasAPIClient, load_api_config, setup_logging, API_CONFIG_FILE, LOG_CONFIG, sanitize_filename
except ImportError as e:
    print(f"Error importing from canvas_api_v3: {e}")
    print("Make sure canvas_api_v3.py is in the same directory.")
    sys.exit(1)

# Initialize logger
logger = logging.getLogger(__name__)


def get_form_by_id(client: CanvasAPIClient, form_id: int, status: str = 'published', version: int = None) -> Dict:
    """
    Retrieve a form by ID (nested structure with sections, sheets, entries).
    
    Args:
        client: Canvas API client instance
        form_id: The unique form ID
        status: Status filter (default: 'published', e.g., 'new', 'pending', 'published', 'archived', or 'testing')
        version: Optional version number to retrieve
        
    Returns:
        Dictionary containing the full nested form data
    """
    endpoint = f"forms/{form_id}"
    params = {'status': status}
    
    if version is not None:
        params['version'] = version
    
    response = client._make_request('GET', endpoint, params=params if params else None)
    return response.json()


def retrieve_form(client: CanvasAPIClient, form_id: int, output_dir: str, status: str = 'published', version: int = None) -> Optional[Dict]:
    """
    Retrieve a form from the API and save it to a file.
    
    Args:
        client: Canvas API client instance
        form_id: Form ID to retrieve
        output_dir: Output directory path
        status: Status filter (default: 'published')
        version: Optional version number to retrieve
        
    Returns:
        Form data dictionary if successful, None otherwise
    """
    try:
        logger.info(f"Retrieving form ID {form_id}...")
        form_data = get_form_by_id(client, form_id, status=status, version=version)
        
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


def main(username: str = None, password: str = None, bearer_token: str = None,
         form_id: int = None, status: str = 'published', version: int = None,
         output_file: str = None, output_to_screen: bool = False,
         log_file: str = None, log_level: str = None, config_file: str = None):
    """
    Get a form by ID from GoCanvas API.
    
    Args:
        username: GoCanvas username for Basic Auth
        password: GoCanvas password for Basic Auth
        bearer_token: OAuth Bearer token (alternative to username/password)
        form_id: Form ID to retrieve
        status: Status filter (default: 'published')
        version: Optional version number to retrieve
        output_file: Path for output file (default: form_{form_id}_{name}.json, ignored if output_to_screen=True)
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
    form_id = form_id or config.get('form_id')
    
    if not form_id:
        print("Error: form_id is required. Provide --form-id or set in config file.")
        return
    
    # Set up logging
    if log_level is None:
        log_level = LOG_CONFIG.get('level', 'INFO')
    if log_file is None:
        log_file = LOG_CONFIG.get('file', 'canvas_api_get_forms_v3.log')
    setup_logging(log_file, log_level)
    
    # Initialize API client
    try:
        client = CanvasAPIClient(username=username, password=password, bearer_token=bearer_token)
        logger.info("Canvas API client initialized")
    except ValueError as e:
        logger.error(f"Failed to initialize API client: {e}")
        print(f"Error: {e}")
        return
    
    # Retrieve form
    try:
        logger.info(f"Retrieving form ID {form_id}...")
        form_data = get_form_by_id(client, form_id, status=status, version=version)
        
        if not form_data:
            logger.warning("No form found")
            if output_to_screen:
                print("No form found")
            return
        
        # Format output as JSON string
        output_json = json.dumps(form_data, indent=3, ensure_ascii=False)
        
        if output_to_screen:
            # Output to console
            print(output_json)
            logger.info(f"Output form {form_id} to console")
        else:
            # Save to file
            if output_file is None:
                form_name = form_data.get('name', 'Unknown')
                output_file = f"form_{form_id}_{sanitize_filename(form_name)}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            
            logger.info(f"Saved form {form_id} to {output_file}")
            print(f"Saved form {form_id} to {output_file}")
        
        # Print summary
        logger.info("\nSummary:")
        logger.info(f"  Form ID: {form_id}")
        logger.info(f"  Form Name: {form_data.get('name', 'Unknown')}")
        logger.info(f"  Status: {status}")
        if version:
            logger.info(f"  Version: {version}")
        if not output_to_screen:
            logger.info(f"  Output file: {output_file}")
        
    except Exception as e:
        logger.error(f"Error retrieving form: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Get a form by ID from GoCanvas API v3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using config file (canvas_api_config.json)
  python canvas_api_get_forms_v3.py --form-id 12345
  
  # Using Basic Auth (username/password)
  python canvas_api_get_forms_v3.py -u user@example.com -p password --form-id 12345
  
  # Using Bearer token
  python canvas_api_get_forms_v3.py --bearer-token YOUR_TOKEN --form-id 12345
  
  # Output to screen/console
  python canvas_api_get_forms_v3.py --form-id 12345 --output-to-screen
  
  # Get specific version
  python canvas_api_get_forms_v3.py --form-id 12345 --version 5
  
  # Custom output file
  python canvas_api_get_forms_v3.py --form-id 12345 -o my_form.json
        """
    )
    
    # Authentication options (mutually exclusive)
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
        '--form-id',
        dest='form_id',
        type=int,
        default=None,
        help='Form ID to retrieve (required, or set in config file)'
    )
    
    parser.add_argument(
        '--status',
        dest='status',
        choices=['new', 'pending', 'published', 'archived', 'testing'],
        default='published',
        help='Status filter (default: published)'
    )
    
    parser.add_argument(
        '--version',
        dest='version',
        type=int,
        default=None,
        help='Optional version number to retrieve'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        default=None,
        help='Path for output file (default: form_{form_id}_{name}.json, ignored if --output-to-screen is used)'
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
        help='Path for log file (default: canvas_api_get_forms_v3.log)'
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
        form_id=args.form_id,
        status=args.status,
        version=args.version,
        output_file=args.output_file,
        output_to_screen=args.output_to_screen,
        log_file=args.log_file,
        log_level=args.log_level,
        config_file=args.config_file
    )
