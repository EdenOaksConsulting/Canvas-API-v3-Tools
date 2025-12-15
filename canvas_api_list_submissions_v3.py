"""
List Submissions from GoCanvas API v3

This module provides functions to list/retrieve submissions from the GoCanvas API v3.
It uses the existing canvas_api_config.json for authentication.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Union

# Import CanvasAPIClient from canvas_api_v3
try:
    from canvas_api_v3 import (
        CanvasAPIClient, load_api_config, setup_logging, API_CONFIG_FILE, LOG_CONFIG,
        get_date_range, API_CONFIG
    )
except ImportError as e:
    print(f"Error importing from canvas_api_v3: {e}")
    print("Make sure canvas_api_v3.py is in the same directory.")
    sys.exit(1)

# Initialize logger
logger = logging.getLogger(__name__)


def get_submissions(client: CanvasAPIClient, start_date: str = None, end_date: str = None, 
                   form_id: int = None, page: int = 1, per_page: int = 100,
                   all_pages: bool = False) -> Union[List[Dict], Dict]:
    """
    Retrieve submissions from GoCanvas API.
    
    Args:
        client: Canvas API client instance
        start_date: Start date filter (YYYY-MM-DD format)
        end_date: End date filter (YYYY-MM-DD format)
        form_id: Filter by form ID (optional)
        page: Page number for pagination (ignored if all_pages=True)
        per_page: Number of results per page (max 100, ignored if all_pages=True)
        all_pages: If True, automatically paginate and return all submissions as a list.
                  If False, return a single page result (dict or list depending on API response)
        
    Returns:
        If all_pages=True: List of all submissions
        If all_pages=False: Dictionary containing submissions and pagination info (or list if API returns list)
    """
    def _fetch_page(page_num: int, per_page_size: int) -> Union[Dict, List]:
        """Helper method to fetch a single page of submissions."""
        endpoint = "submissions"
        params = {
            'page': page_num,
            'per_page': min(per_page_size, 100)  # API limit is 100
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if form_id:
            params['form_id'] = form_id
        
        response = client._make_request('GET', endpoint, params=params)
        return response.json()
    
    # If all_pages is False, return single page result
    if not all_pages:
        return _fetch_page(page, per_page)
    
    # Otherwise, paginate through all pages
    all_submissions = []
    current_page = 1
    per_page_size = 100
    
    logger.info(f"Retrieving submissions from {start_date or 'beginning'} to {end_date or 'now'}")
    if form_id:
        logger.info(f"Filtering by form_id: {form_id}")
    
    while True:
        logger.debug(f"Fetching page {current_page}...")
        result = _fetch_page(current_page, per_page_size)
        
        # Handle different response formats
        if isinstance(result, list):
            submissions = result
            has_more = len(submissions) == per_page_size
        elif isinstance(result, dict):
            submissions = result.get('submissions', result.get('data', []))
            # Check for pagination info
            if 'pagination' in result:
                pagination = result['pagination']
                has_more = pagination.get('current_page', current_page) < pagination.get('total_pages', 1)
            elif 'meta' in result:
                meta = result['meta']
                has_more = meta.get('current_page', current_page) < meta.get('total_pages', 1)
            else:
                # If no pagination info, assume more pages if we got a full page
                has_more = len(submissions) == per_page_size
        else:
            submissions = []
            has_more = False
        
        all_submissions.extend(submissions)
        logger.info(f"Retrieved {len(submissions)} submissions from page {current_page} (total: {len(all_submissions)})")
        
        if not has_more or len(submissions) == 0:
            break
        
        current_page += 1
    
    logger.info(f"Total submissions retrieved: {len(all_submissions)}")
    return all_submissions


def main(username: str = None, password: str = None, bearer_token: str = None,
         start_date: str = None, end_date: str = None, days: int = None,
         form_id: int = None, page: int = 1, per_page: int = 100,
         all_pages: bool = True, output_file: str = None, output_to_screen: bool = False,
         log_file: str = None, log_level: str = None, config_file: str = None):
    """
    List submissions from GoCanvas API.
    
    Args:
        username: GoCanvas username for Basic Auth
        password: GoCanvas password for Basic Auth
        bearer_token: OAuth Bearer token (alternative to username/password)
        start_date: Start date filter (YYYY-MM-DD format)
        end_date: End date filter (YYYY-MM-DD format)
        days: Number of days to look back (alternative to start_date/end_date)
        form_id: Filter by form ID (optional)
        page: Page number for pagination (ignored if all_pages=True)
        per_page: Number of results per page (max 100, ignored if all_pages=True)
        all_pages: If True, automatically paginate and return all submissions
        output_file: Path for output file (default: submission_list_TIMESTAMP.json, ignored if output_to_screen=True)
        output_to_screen: If True, output to console instead of file
        log_file: Path for log file
        log_level: Logging level
        config_file: Path to API config file
    """
    # Load config if provided
    if config_file:
        config = load_api_config(config_file)
    else:
        config = API_CONFIG
    
    # Use provided credentials or fall back to config
    username = username or config.get('username')
    password = password or config.get('password')
    bearer_token = bearer_token or config.get('bearer_token')
    form_id = form_id or config.get('form_id')
    
    # Set up logging
    if log_level is None:
        log_level = LOG_CONFIG.get('level', 'INFO')
    if log_file is None:
        log_file = LOG_CONFIG.get('file', 'canvas_api_list_submissions_v3.log')
    setup_logging(log_file, log_level)
    
    # Initialize API client
    try:
        client = CanvasAPIClient(username=username, password=password, bearer_token=bearer_token)
        logger.info("Canvas API client initialized")
    except ValueError as e:
        logger.error(f"Failed to initialize API client: {e}")
        print(f"Error: {e}")
        return
    
    # Determine date range
    if days is not None:
        start_date, end_date = get_date_range(days)
        logger.info(f"Using date range: {start_date} to {end_date} (last {days} days)")
    elif not start_date and not end_date:
        # Default to last 7 days if no date specified
        start_date, end_date = get_date_range(7)
        logger.info(f"Using default date range: {start_date} to {end_date} (last 7 days)")
    
    # Retrieve submissions list
    try:
        logger.info("Retrieving submissions" + (f" from {start_date} to {end_date}" if start_date or end_date else ""))
        if form_id:
            logger.info(f"Filtering by form_id: {form_id}")
        
        submissions_list = get_submissions(
            client,
            start_date=start_date,
            end_date=end_date,
            form_id=form_id,
            page=page,
            per_page=per_page,
            all_pages=all_pages
        )
        
        if not submissions_list:
            logger.warning("No submissions found")
            if output_to_screen:
                print("No submissions found")
            return
        
        # Handle both list and dict responses
        if isinstance(submissions_list, dict):
            # If it's a dict, extract the submissions
            submissions = submissions_list.get('submissions', submissions_list.get('data', []))
        else:
            submissions = submissions_list
        
        logger.info(f"Found {len(submissions)} submissions")
        
        # Format output as JSON string
        output_json = json.dumps(submissions_list, indent=3, ensure_ascii=False)
        
        if output_to_screen:
            # Output to console
            print(output_json)
            logger.info(f"Output {len(submissions)} submissions to console")
        else:
            # Save to file
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                if start_date and end_date:
                    output_file = f'submission_list_{start_date}_to_{end_date}.json'
                    if form_id:
                        output_file = f'submission_list_form_{form_id}_{start_date}_to_{end_date}.json'
                else:
                    output_file = f'submission_list_{timestamp}.json'
            
            # Write to working directory if output_file is a relative path (not absolute)
            if not os.path.isabs(output_file):
                # Create working directory if it doesn't exist
                working_dir = 'working'
                if not os.path.exists(working_dir):
                    os.makedirs(working_dir)
                output_file = os.path.join(working_dir, output_file)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            
            logger.info(f"Saved {len(submissions)} submissions to {output_file}")
            print(f"Saved {len(submissions)} submissions to {output_file}")
        
        # Print summary
        logger.info("\nSummary:")
        logger.info(f"  Total submissions found: {len(submissions)}")
        if start_date:
            logger.info(f"  Start date: {start_date}")
        if end_date:
            logger.info(f"  End date: {end_date}")
        if form_id:
            logger.info(f"  Form ID filter: {form_id}")
        if not all_pages:
            logger.info(f"  Page: {page}, Per page: {per_page}")
        if not output_to_screen:
            logger.info(f"  Output file: {output_file}")
        
    except Exception as e:
        logger.error(f"Error retrieving submissions: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='List submissions from GoCanvas API v3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using config file (canvas_api_config.json)
  python canvas_api_list_submissions_v3.py
  
  # Using Basic Auth (username/password)
  python canvas_api_list_submissions_v3.py -u user@example.com -p password
  
  # Using Bearer token
  python canvas_api_list_submissions_v3.py --bearer-token YOUR_TOKEN
  
  # List last 14 days
  python canvas_api_list_submissions_v3.py --days 14
  
  # List with specific date range
  python canvas_api_list_submissions_v3.py --start-date 2024-01-01 --end-date 2024-01-31
  
  # Filter by form ID
  python canvas_api_list_submissions_v3.py --form-id 12345
  
  # Output to screen/console
  python canvas_api_list_submissions_v3.py --output-to-screen
  
  # Get single page (no pagination)
  python canvas_api_list_submissions_v3.py --no-all-pages --page 1 --per-page 50
  
  # Custom output file
  python canvas_api_list_submissions_v3.py -o my_submissions.json
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
    
    # Date range options
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        '-d', '--days',
        dest='days',
        type=int,
        default=None,
        help='Number of days to look back (default: 7 if no date specified)'
    )
    date_group.add_argument(
        '--start-date',
        dest='start_date',
        default=None,
        help='Start date filter (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--end-date',
        dest='end_date',
        default=None,
        help='End date filter (YYYY-MM-DD format, requires --start-date)'
    )
    
    parser.add_argument(
        '-f', '--form-id',
        dest='form_id',
        type=int,
        default=None,
        help='Filter submissions by form ID (optional, default: from config file)'
    )
    
    # Pagination options
    parser.add_argument(
        '--page',
        dest='page',
        type=int,
        default=1,
        help='Page number for pagination (ignored if --all-pages is used, default: 1)'
    )
    
    parser.add_argument(
        '--per-page',
        dest='per_page',
        type=int,
        default=100,
        help='Number of results per page (max 100, ignored if --all-pages is used, default: 100)'
    )
    
    parser.add_argument(
        '--all-pages',
        dest='all_pages',
        action='store_true',
        default=True,
        help='Automatically paginate and return all submissions (default: True)'
    )
    
    parser.add_argument(
        '--no-all-pages',
        dest='all_pages',
        action='store_false',
        help='Return only a single page (disables automatic pagination)'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        default=None,
        help='Path for output file (default: submission_list_TIMESTAMP.json, ignored if --output-to-screen is used)'
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
        help='Path for log file (default: canvas_api_list_submissions_v3.log)'
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
    
    # Validate date arguments
    if args.end_date and not args.start_date:
        parser.error("--end-date requires --start-date")
    
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
        start_date=args.start_date,
        end_date=args.end_date,
        days=args.days,
        form_id=args.form_id,
        page=args.page,
        per_page=args.per_page,
        all_pages=args.all_pages,
        output_file=args.output_file,
        output_to_screen=args.output_to_screen,
        log_file=args.log_file,
        log_level=args.log_level,
        config_file=args.config_file
    )
