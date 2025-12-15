"""
Get Submissions from GoCanvas API v3

This script retrieves submissions from the GoCanvas API v3 for the last N days.
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
    from canvas_api_v3 import (
        CanvasAPIClient, load_api_config, setup_logging, API_CONFIG_FILE, LOG_CONFIG,
        get_date_range, sanitize_filename, API_CONFIG
    )
except ImportError as e:
    print(f"Error importing from canvas_api_v3: {e}")
    print("Make sure canvas_api_v3.py is in the same directory.")
    sys.exit(1)

# Import get_submissions from canvas_api_list_submissions_v3
try:
    from canvas_api_list_submissions_v3 import get_submissions
except ImportError as e:
    print(f"Error importing from canvas_api_list_submissions_v3: {e}")
    print("Make sure canvas_api_list_submissions_v3.py is in the same directory.")
    sys.exit(1)

# Import transform function from canvas_transform_v3_to_v2.py
try:
    from canvas_transform_v3_to_v2 import transform_v3_to_v2
except ImportError:
    transform_v3_to_v2 = None

# Initialize logger
logger = logging.getLogger(__name__)


def get_submission_by_id(client: CanvasAPIClient, submission_id: int) -> Dict:
    """
    Retrieve a single submission by ID.
    
    Args:
        client: Canvas API client instance
        submission_id: The unique submission ID
        
    Returns:
        Dictionary containing the full submission data
    """
    endpoint = f"submissions/{submission_id}"
    response = client._make_request('GET', endpoint)
    return response.json()


def retrieve_form(client: CanvasAPIClient, form_id: int, output_dir: str, version: int = None) -> Optional[Dict]:
    """
    Retrieve a form from the API and save it to a file.
    
    Args:
        client: Canvas API client instance
        form_id: Form ID to retrieve
        output_dir: Output directory path
        version: Optional version number to retrieve specific version
        
    Returns:
        Form data dictionary if successful, None otherwise
    """
    try:
        if version:
            logger.info(f"Retrieving form ID {form_id}, version {version}...")
        else:
            logger.info(f"Retrieving form ID {form_id}...")
        endpoint = f"forms/{form_id}"
        params = {'status': 'published'}
        if version is not None:
            params['version'] = version
        response = client._make_request('GET', endpoint, params=params)
        form_data = response.json()
        
        # Create filename using form ID, name, and version if specified
        form_name = form_data.get('name', 'Unknown')
        form_version = form_data.get('version', version)
        if form_version:
            filename = f"form_{form_id}_{sanitize_filename(form_name)}_v{form_version}.json"
        else:
            filename = f"form_{form_id}_{sanitize_filename(form_name)}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(form_data, f, indent=3, ensure_ascii=False)
        
        logger.info(f"Saved form {form_id} ({form_name}, version {form_version}) to {filepath}")
        return form_data
        
    except Exception as e:
        logger.error(f"Error retrieving form {form_id}: {e}")
        return None


def process_submission(client: CanvasAPIClient, submission_summary: Dict, 
                      output_dir: str, form_cache: Dict[int, Dict] = None) -> tuple:
    """
    Process a single submission: retrieve, save, and optionally transform.
    
    Args:
        client: Canvas API client instance
        submission_summary: Submission summary from list endpoint
        output_dir: Output directory path
        form_cache: Optional dictionary to cache retrieved forms (key: form_id, value: form_data)
        
    Returns:
        Tuple of (success: bool, transformed: bool)
    """
    submission_id = submission_summary.get('id')
    if not submission_id:
        logger.warning(f"Submission has no ID, skipping")
        return False, False
    
    try:
        # Retrieve full submission
        full_submission = get_submission_by_id(client, submission_id)
        
        # Create filename
        submission_number = submission_summary.get('submission_number', '')
        if submission_number:
            v3_filename = f"submission_{submission_id}_{submission_number}_v3.json"
        else:
            v3_filename = f"submission_{submission_id}_v3.json"
        
        filepath = os.path.join(output_dir, v3_filename)
        
        # Save v3 submission
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_submission, f, indent=3, ensure_ascii=False)
        
        logger.debug(f"Saved submission {submission_id} to {filepath}")
        
        # Get form_id from submission and retrieve form for transformation
        submission_form_id = submission_summary.get('form_id') or full_submission.get('form_id')
        form_data = None
        transformed = False
        
        if submission_form_id and transform_v3_to_v2:
            # Check cache first
            if form_cache is not None and submission_form_id in form_cache:
                form_data = form_cache[submission_form_id]
                logger.debug(f"Using cached form data for form_id {submission_form_id}")
            else:
                # Retrieve form for this specific submission
                try:
                    logger.info(f"Retrieving form {submission_form_id} for submission {submission_id}...")
                    form_data = retrieve_form(client, submission_form_id, output_dir)
                    if form_data and form_cache is not None:
                        form_cache[submission_form_id] = form_data
                except Exception as e:
                    logger.warning(f"Could not retrieve form {submission_form_id} for submission {submission_id}: {e}")
            
            # Transform to v2 format if form_data is available
            if form_data:
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
            else:
                logger.warning(f"No form data available for submission {submission_id} (form_id: {submission_form_id}). Transformation skipped.")
        
        return True, transformed
        
    except Exception as e:
        logger.error(f"Error processing submission {submission_id}: {e}")
        return False, False


def main(username: str = None, password: str = None, bearer_token: str = None,
         days: int = None, start_date: str = None, end_date: str = None,
         form_id: int = None, output_file: str = None,
         log_file: str = None, log_level: str = None, config_file: str = None):
    """
    Retrieve submissions from GoCanvas API for the last N days or specified date range.
    
    Args:
        username: GoCanvas username for Basic Auth
        password: GoCanvas password for Basic Auth
        bearer_token: OAuth Bearer token (alternative to username/password)
        days: Number of days to look back (default: 7 if no date specified)
        start_date: Start date filter (YYYY-MM-DD format)
        end_date: End date filter (YYYY-MM-DD format)
        form_id: Optional form ID to filter submissions
        output_file: Path for output directory (each submission saved to unique file)
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
    form_id = form_id or config.get('form_id')  # form_id from config is used for filtering only
    form_id = form_id or config.get('form_id')
    
    # Set up logging
    if log_level is None:
        log_level = LOG_CONFIG.get('level', 'INFO')
    if log_file is None:
        log_file = LOG_CONFIG.get('file', 'canvas_api_get_submissions_v3.log')
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
    
    # Determine date range
    if days is not None:
        start_date, end_date = get_date_range(days)
        logger.info(f"Using date range: {start_date} to {end_date} (last {days} days)")
    elif not start_date and not end_date:
        # Default to last 7 days if no date specified
        start_date, end_date = get_date_range(7)
        logger.info(f"Using default date range: {start_date} to {end_date} (last 7 days)")
    else:
        if start_date and end_date:
            logger.info(f"Using date range: {start_date} to {end_date}")
        elif start_date:
            logger.info(f"Using start date: {start_date} (no end date)")
        elif end_date:
            logger.info(f"Using end date: {end_date} (no start date)")
    
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
        submission_list = get_submissions(
            client,
            start_date=start_date,
            end_date=end_date,
            form_id=form_id,
            all_pages=True
        )
        
        if not submission_list:
            logger.warning("No submissions found for the specified date range")
            return
        
        logger.info(f"Found {len(submission_list)} submissions.")
        
        # Save submission list as JSON file
        submission_list_filename = f"submission_list_{start_date}_to_{end_date}.json"
        if form_id:
            submission_list_filename = f"submission_list_form_{form_id}_{start_date}_to_{end_date}.json"
        submission_list_filepath = os.path.join(output_dir, submission_list_filename)
        
        with open(submission_list_filepath, 'w', encoding='utf-8') as f:
            json.dump(submission_list, f, indent=3, ensure_ascii=False)
        
        logger.info(f"Saved submission list ({len(submission_list)} submissions) to {submission_list_filepath}")
        print(f"Saved submission list to {submission_list_filepath}")
        
        logger.info(f"Retrieving full details for each submission...")
        
        # Create form cache to avoid retrieving the same form multiple times
        form_cache = {}
        
        # Process each submission
        successful = 0
        failed = 0
        transformed = 0
        transform_failed = 0
        
        for idx, submission_summary in enumerate(submission_list, 1):
            logger.info(f"Processing submission {idx}/{len(submission_list)}: ID {submission_summary.get('id')}")
            success, was_transformed = process_submission(client, submission_summary, output_dir, form_cache)
            
            if success:
                successful += 1
                if was_transformed:
                    transformed += 1
                elif transform_v3_to_v2:
                    transform_failed += 1
            else:
                failed += 1
        
        logger.info("Retrieval complete!")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Log file: {log_file}")
        
        # Print summary
        logger.info(f"\nSummary:")
        logger.info(f"  Total submissions found: {len(submission_list)}")
        logger.info(f"  Submission list saved to: {submission_list_filepath}")
        logger.info(f"  Submissions successfully retrieved: {successful}")
        logger.info(f"  Submissions failed: {failed}")
        if transform_v3_to_v2:
            logger.info(f"  Submissions transformed to v2: {transformed}")
            if transform_failed > 0:
                logger.info(f"  Transformations failed: {transform_failed}")
            logger.info(f"  Unique forms retrieved: {len(form_cache)}")
        logger.info(f"  Date range: {start_date} to {end_date}")
        if form_id:
            logger.info(f"  Form ID filter: {form_id}")
        
    except Exception as e:
        logger.error(f"Error retrieving submissions: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Retrieve submissions from GoCanvas API for the last N days or specified date range',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using Basic Auth (username/password)
  python canvas_api_get_submissions_v3.py -u user@example.com -p password
  
  # Using Bearer token
  python canvas_api_get_submissions_v3.py --bearer-token YOUR_TOKEN
  
  # Retrieve last 14 days
  python canvas_api_get_submissions_v3.py -u user@example.com -p password --days 14
  
  # Retrieve with specific date range
  python canvas_api_get_submissions_v3.py -u user@example.com -p password --start-date 2024-01-01 --end-date 2024-01-31
  
  # Filter by form ID
  python canvas_api_get_submissions_v3.py -u user@example.com -p password --form-id 12345
  
  # Custom output directory
  python canvas_api_get_submissions_v3.py -u user@example.com -p password -o my_submissions
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
        help='Path for log file (default: canvas_api_get_submissions_v3.log)'
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
        config = default_config
    
    # Determine authentication - use command line args if provided, otherwise use defaults
    username = args.username if args.username else config.get('username')
    password = args.password if args.password else config.get('password')
    bearer_token = args.bearer_token if args.bearer_token else config.get('bearer_token')
    
    # Validate authentication
    if args.username and not args.password:
        parser.error("Password is required when using username authentication")
    
    # Validate date arguments
    if args.end_date and not args.start_date:
        parser.error("--end-date requires --start-date")
    
    # Ensure we have some form of authentication
    if not bearer_token and not (username and password):
        parser.error("Authentication required: provide --bearer-token or -u/-p, or configure in config file")
    
    main(
        username=username,
        password=password,
        bearer_token=bearer_token,
        days=args.days,
        start_date=args.start_date,
        end_date=args.end_date,
        form_id=args.form_id,
        output_file=args.output_file,
        log_file=args.log_file,
        log_level=args.log_level,
        config_file=args.config_file
    )
