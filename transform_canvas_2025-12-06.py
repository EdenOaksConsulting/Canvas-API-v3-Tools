import json
import logging
from collections import defaultdict
from datetime import datetime

# Global debugging options
# Set log level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
# DEBUG level will show all detailed debug information
LOG_CONFIG = {
    'level': 'INFO',  # Default log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'file': 'transform_canvas.log',  # Log file name
}

# Initialize logger
logger = logging.getLogger(__name__)

def setup_logging(log_file=None, log_level='INFO'):
    """Set up logging configuration."""
    if log_file is None:
        log_file = LOG_CONFIG.get('file', 'transform_canvas.log')
    
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
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')  # 'w' mode clears file each run
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

def load_json_file(filename):
    """Load a JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_entry_mapping(form_data):
    """Build a mapping from entry_id to (section_name, sheet_name, guid, label, position)."""
    entry_map = {}
    section_order = []  # Preserve section order
    
    for section in form_data.get('sections', []):
        section_name = section.get('description', '')
        section_position = section.get('position', 0)
        
        # Track section order
        if section_name not in [s['name'] for s in section_order]:
            section_order.append({
                'name': section_name,
                'position': section_position
            })
        
        for sheet in section.get('sheets', []):
            sheet_name = sheet.get('description', '')
            sheet_position = sheet.get('position', 0)
            
            for entry in sheet.get('entries', []):
                entry_id = entry.get('id')
                if entry_id:
                    entry_map[entry_id] = {
                        'section_name': section_name,
                        'section_position': section_position,
                        'sheet_name': sheet_name,
                        'sheet_position': sheet_position,
                        'guid': entry.get('guid', ''),
                        'label': entry.get('label', ''),
                        'position': entry.get('position', 0)
                    }
    
    # Sort sections by position
    section_order.sort(key=lambda x: x['position'])
    
    # Debug: Log entry mapping statistics
    logger.debug("=" * 50)
    logger.debug("entry_mapping statistics")
    logger.debug(f"Total entries mapped: {len(entry_map)}")
    logger.debug(f"Total sections: {len(section_order)}")
    section_counts = {}
    for entry_id, info in entry_map.items():
        section_name = info['section_name']
        section_counts[section_name] = section_counts.get(section_name, 0) + 1
    logger.debug("Entries per section:")
    for section_name, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.debug(f"  {section_name}: {count} entries")
    logger.debug("=" * 50)
    
    # Detailed entry mapping
    logger.debug("Detailed entry mapping:")
    for entry_id, info in list(entry_map.items())[:20]:  # First 20 for debug
        logger.debug(f"  entry_id {entry_id}: section='{info['section_name']}', sheet='{info['sheet_name']}', label='{info['label']}'")
    
    return entry_map, section_order

def format_date(date_str):
    """Convert ISO date to format used in v2: YYYY.MM.DD HH:MM:SS"""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y.%m.%d %H:%M:%S')
    except:
        return date_str

def transform_v3_to_v2(v3_data, form_data):
    """Transform Canvas_v3.json format to Canvas_v2.json format."""
    
    # Build entry mapping
    entry_map, section_order = build_entry_mapping(form_data)
    
    # Extract top-level metadata
    submission_id = str(v3_data.get('id', ''))
    client_guid = v3_data.get('client_guid', '')
    submission_number = v3_data.get('submission_number', '')
    created_at = v3_data.get('created_at', '')
    
    # Group responses by section and sheet
    section_data = defaultdict(lambda: defaultdict(list))
    unmapped_responses = []
    
    for response in v3_data.get('responses', []):
        entry_id = response.get('entry_id')
        if entry_id and entry_id in entry_map:
            entry_info = entry_map[entry_id]
            section_name = entry_info['section_name']
            sheet_name = entry_info['sheet_name']
            
            # Create response object
            response_obj = {
                'Guid': entry_info['guid'],
                'Label': response.get('label', entry_info['label']),
                'Type': response.get('type', ''),
                'Value': response.get('value') if response.get('value') else None
            }
            
            section_data[section_name][sheet_name].append({
                'response': response_obj,
                'position': entry_info['position'],
                'sheet_position': entry_info['sheet_position']
            })
        else:
            unmapped_responses.append(response)
    
    # Debug: Log response processing details (only at DEBUG level)
    logger.debug("=" * 50)
    logger.debug("response processing")
    logger.debug(f"Total responses: {len(v3_data.get('responses', []))}")
    mapped_count = sum(len(sheets[sheet]) for sheets in section_data.values() for sheet in sheets)
    logger.debug(f"Mapped responses: {mapped_count}")
    logger.debug(f"Unmapped responses: {len(unmapped_responses)}")
    if unmapped_responses:
        logger.warning("Unmapped entry_ids found:")
        for resp in unmapped_responses[:10]:
            logger.warning(f"  entry_id: {resp.get('entry_id')}, label: {resp.get('label')}")
    logger.debug("=" * 50)
    
    # Detailed response processing
    logger.debug("Detailed response mapping:")
    for section_name, sheets in list(section_data.items())[:5]:  # First 5 sections
        for sheet_name, responses in sheets.items():
            logger.debug(f"  Section: {section_name}, Sheet: {sheet_name}")
            for resp_data in responses[:3]:  # First 3 responses per sheet
                resp = resp_data['response']
                logger.debug(f"    Label: {resp['Label']}, Type: {resp['Type']}, Value: {resp['Value']}")
    
    if unmapped_responses:
        logger.warning(f"Found {len(unmapped_responses)} unmapped responses")
    
    # Debug: Log section_data structure
    logger.debug("=" * 50)
    logger.debug("section_data structure")
    logger.debug(f"Total sections: {len(section_data)}")
    for section_name, sheets in section_data.items():
        logger.debug(f"Section: '{section_name}'")
        logger.debug(f"  Total sheets: {len(sheets)}")
        for sheet_name, responses in sheets.items():
            logger.debug(f"    Sheet: '{sheet_name}' - {len(responses)} responses")
            # Show first few response labels as examples
            if responses:
                sample_labels = [r['response']['Label'] for r in responses[:3]]
                logger.debug(f"      Sample labels: {sample_labels}")
    logger.debug("=" * 50)
    
    # Full section_data structure
    logger.debug("Full section_data structure:")
    for section_name, sheets in section_data.items():
        logger.debug(f"Section: '{section_name}'")
        for sheet_name, responses in sheets.items():
            logger.debug(f"  Sheet: '{sheet_name}' ({len(responses)} responses)")
            for resp_data in responses:
                resp = resp_data['response']
                logger.debug(f"    - {resp['Label']} ({resp['Type']}): {resp['Value']}")
    
    # Build sections structure preserving order
    sections_list = []
    for section_info in section_order:
        section_name = section_info['name']
        if section_name not in section_data:
            continue
            
        sheets_data = section_data[section_name]
        
        # Sort sheets by position
        sorted_sheets = sorted(sheets_data.items(), 
                              key=lambda x: min([r['sheet_position'] for r in x[1]]))
        
        # For each sheet in the section
        for sheet_name, responses in sorted_sheets:
            # Sort by position
            responses.sort(key=lambda x: x['position'])
            
            # Extract just the response objects
            response_list = [r['response'] for r in responses]
            
            # Create section with screen
            section_obj = {
                'Name': section_name,
                'Screens': {
                    'Screen': {
                        'Name': sheet_name,
                        'ResponseGroups': {},
                        'Responses': {
                            'Response': response_list
                        }
                    }
                }
            }
            sections_list.append(section_obj)
    
    # Extract additional fields from responses if available
    # Look for common field names or check user data
    first_name = None
    last_name = None
    device_date = None
    
    # Try to extract from responses
    for response in v3_data.get('responses', []):
        label = response.get('label', '').lower()
        value = response.get('value', '')
        
        if value:  # Only use non-empty values
            if 'firstname' in label or 'first name' in label:
                first_name = value
            elif 'lastname' in label or 'last name' in label:
                last_name = value
            elif 'devicedate' in label or 'device date' in label:
                device_date = value
    
    # If not found in responses, try to extract from user_id or other metadata
    # Check if there's user information we can use
    # For now, we'll leave these as None if not found in responses
    
    # Try to find UserName from responses (e.g., Hydrographer field)
    user_name = None
    for response in v3_data.get('responses', []):
        label = response.get('label', '').lower()
        value = response.get('value', '')
        # Check if it looks like an email (user name)
        if value and '@' in value and '.' in value:
            user_name = value
            break
    
    # Build the final structure
    result = {
        'Date': format_date(created_at),
        'DeviceDate': device_date,
        'FirstName': first_name,
        'Form': {
            'Id': str(form_data.get('id', '')),
            'Name': form_data.get('name', ''),
            'Status': form_data.get('status', ''),
            'Version': str(form_data.get('version', ''))
        },
        'Id': submission_id,
        'LastName': last_name,
        'No.': submission_number,
        'ResponseID': client_guid,
        'Sections': {
            'Section': sections_list
        }
    }
    
    # Add additional fields if available
    if submission_number:
        result['SubmissionNumber'] = submission_number
    if user_name:
        result['UserName'] = user_name
    
    return result

def main():
    # Set up logging
    log_level = LOG_CONFIG.get('level', 'INFO')
    log_file = LOG_CONFIG.get('file', 'transform_canvas.log')
    setup_logging(log_file, log_level)
    
    # Load the files
    logger.info("Loading files...")
    form_data = load_json_file('Canvas_Sample_Form_Nested.json')
    v3_data = load_json_file('Canvas_v3.json')
    logger.info(f"Loaded form: {form_data.get('name', 'Unknown')} (ID: {form_data.get('id', 'Unknown')})")
    logger.info(f"Loaded submission: {v3_data.get('id', 'Unknown')} (Number: {v3_data.get('submission_number', 'Unknown')})")
    
    # Transform
    logger.info("Transforming data...")
    v2_format = transform_v3_to_v2(v3_data, form_data)
    
    # Save the result
    output_file = 'Canvas_v3_transformed.json'
    logger.info(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(v2_format, f, indent=3, ensure_ascii=False)
    
    logger.info("Transformation complete!")
    logger.info(f"Log file: {log_file}")

if __name__ == '__main__':
    main()

