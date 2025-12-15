# Canvas-API-v3-Tools

Tools to interact with the GoCanvas API v3, retrieve submissions and forms, and transform data between v3 and v2 formats.

This project provides a modular set of Python scripts for:
- Listing and retrieving forms from the GoCanvas API v3
- Listing and retrieving submissions from the GoCanvas API v3
- Transforming submissions from v3 format to v2 format
- Managing authentication and API interactions through a central client library

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure API credentials:
   - Copy `canvas_api_config.json.example` to `canvas_api_config.json`
   - Edit `canvas_api_config.json` and add your GoCanvas credentials:
     ```json
     {
         "username": "your_username@example.com",
         "password": "your_password",
         "bearer_token": null,
         "form_id": 1234567
     }
     ```
   - You can use either Basic Auth (username/password) or OAuth Bearer token
   - `form_id` is optional and can be used for filtering (not required for form retrieval)

## Architecture

The project uses a modular architecture:

- **`canvas_api_v3.py`**: Core library providing the `CanvasAPIClient` class and common utilities
- **`canvas_api_list_forms_v3.py`**: List all forms
- **`canvas_api_get_forms_v3.py`**: Get a specific form by ID
- **`canvas_api_list_submissions_v3.py`**: List submissions (summary data)
- **`canvas_api_get_submissions_v3.py`**: Get full submission details and transform to v2
- **`canvas_transform_v3_to_v2.py`**: Transform individual submissions from v3 to v2 format

## Scripts Documentation

### Core Library: `canvas_api_v3.py`

This is the central module that provides the `CanvasAPIClient` class and common utilities. It's imported by all other scripts and should not be run directly.

**Key Components:**
- `CanvasAPIClient`: Main API client class for making authenticated requests
- `load_api_config()`: Load configuration from JSON file
- `setup_logging()`: Configure logging
- `get_date_range()`: Calculate date ranges
- `sanitize_filename()`: Clean filenames for safe file system use

### List All Forms: `canvas_api_list_forms_v3.py`

Retrieves and lists all forms from the GoCanvas API v3.

**Usage:**
```bash
python canvas_api_list_forms_v3.py [OPTIONS]
```

**Options:**
- `-u, --username`: GoCanvas username for Basic Auth (default: from config file)
- `-p, --password`: GoCanvas password (required if using username, default: from config file)
- `--bearer-token`: OAuth Bearer token for authentication (default: from config file)
- `--status`: Filter forms by status (`new`, `pending`, `published`, `archived`, `testing`)
- `-o, --output`: Path for output file (default: `working/canvas_forms_TIMESTAMP.json`)
- `--output-to-screen`: Output results to console instead of file
- `--log-file`: Path for log file (default: `list_forms.log`)
- `--log-level`: Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: `INFO`)
- `--config-file`: Path to API config file (default: `canvas_api_config.json`)

**Examples:**
```bash
# List all published forms using config file
python canvas_api_list_forms_v3.py

# List forms with Basic Auth
python canvas_api_list_forms_v3.py -u user@example.com -p password

# List only published forms and output to screen
python canvas_api_list_forms_v3.py --status published --output-to-screen

# Save to custom file
python canvas_api_list_forms_v3.py -o my_forms.json
```

**Output:**
- Saves to `working/canvas_forms_TIMESTAMP.json` by default
- Outputs JSON array of all forms with their IDs, names, and statuses

### Get Form by ID: `canvas_api_get_forms_v3.py`

Retrieves a specific form by ID from the GoCanvas API v3, including full nested structure (sections, sheets, entries).

**Usage:**
```bash
python canvas_api_get_forms_v3.py --form-id FORM_ID [OPTIONS]
```

**Options:**
- `-u, --username`: GoCanvas username for Basic Auth (default: from config file)
- `-p, --password`: GoCanvas password (required if using username, default: from config file)
- `--bearer-token`: OAuth Bearer token for authentication (default: from config file)
- `--form-id`: **Required** - Form ID to retrieve (or set in config file)
- `--status`: Status filter: `new`, `pending`, `published`, `archived`, `testing` (default: `published`)
- `--version`: Optional version number to retrieve specific version
- `-o, --output`: Path for output file (default: `form_{form_id}_{name}.json`)
- `--output-to-screen`: Output results to console instead of file
- `--log-file`: Path for log file (default: `canvas_api_get_forms_v3.log`)
- `--log-level`: Logging level (default: `INFO`)
- `--config-file`: Path to API config file (default: `canvas_api_config.json`)

**Examples:**
```bash
# Get form by ID using config file
python canvas_api_get_forms_v3.py --form-id 12345

# Get specific version of a form
python canvas_api_get_forms_v3.py --form-id 12345 --version 5

# Output to screen
python canvas_api_get_forms_v3.py --form-id 12345 --output-to-screen

# Get archived form
python canvas_api_get_forms_v3.py --form-id 12345 --status archived
```

**Output:**
- Saves form structure as JSON file: `form_{form_id}_{name}.json`
- Includes complete nested structure with sections, sheets, and entries

### List Submissions: `canvas_api_list_submissions_v3.py`

Lists submissions from the GoCanvas API v3. Returns summary data (not full submission details).

**Usage:**
```bash
python canvas_api_list_submissions_v3.py [OPTIONS]
```

**Options:**
- `-u, --username`: GoCanvas username for Basic Auth (default: from config file)
- `-p, --password`: GoCanvas password (required if using username, default: from config file)
- `--bearer-token`: OAuth Bearer token for authentication (default: from config file)
- `-d, --days`: Number of days to look back (default: 7 if no date specified)
- `--start-date`: Start date filter (YYYY-MM-DD format)
- `--end-date`: End date filter (YYYY-MM-DD format, requires --start-date)
- `-f, --form-id`: Filter submissions by form ID (optional, default: from config file)
- `--page`: Page number for pagination (ignored if --all-pages is used, default: 1)
- `--per-page`: Number of results per page (max 100, ignored if --all-pages is used, default: 100)
- `--all-pages`: Automatically paginate and return all submissions (default: True)
- `--no-all-pages`: Return only a single page (disables automatic pagination)
- `-o, --output`: Path for output file (default: `working/submission_list_TIMESTAMP.json`)
- `--output-to-screen`: Output results to console instead of file
- `--log-file`: Path for log file (default: `canvas_api_list_submissions_v3.log`)
- `--log-level`: Logging level (default: `INFO`)
- `--config-file`: Path to API config file (default: `canvas_api_config.json`)

**Examples:**
```bash
# List submissions from last 7 days (default)
python canvas_api_list_submissions_v3.py

# List last 14 days
python canvas_api_list_submissions_v3.py --days 14

# List with specific date range
python canvas_api_list_submissions_v3.py --start-date 2024-01-01 --end-date 2024-01-31

# Filter by form ID
python canvas_api_list_submissions_v3.py --form-id 12345

# Output to screen
python canvas_api_list_submissions_v3.py --output-to-screen

# Get single page only (no pagination)
python canvas_api_list_submissions_v3.py --no-all-pages --page 1 --per-page 50
```

**Output:**
- Saves to `working/submission_list_{start_date}_to_{end_date}.json` by default
- If form_id is specified: `working/submission_list_form_{form_id}_{start_date}_to_{end_date}.json`
- Contains summary data for each submission (ID, form_id, submission_number, created_at, etc.)

### Get Full Submissions: `canvas_api_get_submissions_v3.py`

Retrieves full submission details from the GoCanvas API v3, saves them as v3 JSON files, and optionally transforms them to v2 format.

**Usage:**
```bash
python canvas_api_get_submissions_v3.py [OPTIONS]
```

**Options:**
- `-u, --username`: GoCanvas username for Basic Auth (default: from config file)
- `-p, --password`: GoCanvas password (required if using username, default: from config file)
- `--bearer-token`: OAuth Bearer token for authentication (default: from config file)
- `-d, --days`: Number of days to look back (default: 7 if no date specified)
- `--start-date`: Start date filter (YYYY-MM-DD format)
- `--end-date`: End date filter (YYYY-MM-DD format, requires --start-date)
- `-f, --form-id`: Filter submissions by form ID (optional, default: from config file)
- `-o, --output`: Path for output directory (default: `canvas_submissions_TIMESTAMP`)
- `--log-file`: Path for log file (default: `canvas_api_get_submissions_v3.log`)
- `--log-level`: Logging level (default: `INFO`)
- `--config-file`: Path to API config file (default: `canvas_api_config.json`)

**Examples:**
```bash
# Retrieve submissions from last 7 days (default)
python canvas_api_get_submissions_v3.py

# Retrieve last 14 days
python canvas_api_get_submissions_v3.py --days 14

# Retrieve with specific date range
python canvas_api_get_submissions_v3.py --start-date 2024-01-01 --end-date 2024-01-31

# Filter by form ID
python canvas_api_get_submissions_v3.py --form-id 12345

# Custom output directory
python canvas_api_get_submissions_v3.py -o my_submissions
```

**What it does:**
1. Retrieves list of submissions for the specified date range
2. Saves the submission list as JSON: `submission_list_{start_date}_to_{end_date}.json`
3. For each submission:
   - Retrieves full submission details
   - Saves as `submission_{id}_{number}_v3.json`
   - Retrieves the form associated with the submission (based on submission's `form_id`)
   - Transforms to v2 format and saves as `submission_{id}_{number}_v2.json` (if form available)
4. Forms are cached to avoid redundant API calls

**Output Structure:**
```
canvas_submissions_TIMESTAMP/
├── submission_list_{start_date}_to_{end_date}.json
├── form_{form_id}_{name}_v{version}.json (one per unique form)
├── submission_{id}_{number}_v3.json (full v3 submission)
└── submission_{id}_{number}_v2.json (transformed v2 submission)
```

**Note:** The `form_id` used for transformation is automatically extracted from each submission's data, not from the config file. This allows processing submissions from different forms in a single run.

### Transform Submissions: `canvas_transform_v3_to_v2.py`

Transforms a single submission from v3 format to v2 format. Requires both the submission JSON and the form structure JSON.

**Usage:**
```bash
python canvas_transform_v3_to_v2.py [OPTIONS]
```

**Options:**
- `-f, --form`: Path to form structure JSON file (default: `Canvas_Sample_Form_Nested.json`)
- `-v, --v3`: Path to v3 submission JSON file (default: `Canvas_v3.json`)
- `-o, --output`: Path for output transformed JSON file (default: `Canvas_v3_transformed.json`)
- `--log-file`: Path for log file (default: `canvas_transform_v3_to_v2.log`)
- `--log-level`: Logging level (default: `INFO`)

**Examples:**
```bash
# Transform with default files
python canvas_transform_v3_to_v2.py

# Transform with specific files
python canvas_transform_v3_to_v2.py --form form.json --v3 submission.json --output result.json

# Short form
python canvas_transform_v3_to_v2.py -f form.json -v submission.json -o result.json
```

**Output:**
- Saves transformed submission as JSON file in v2 format

## Output Locations

### Query Results (List Operations)
- **Forms list**: `working/canvas_forms_TIMESTAMP.json`
- **Submissions list**: `working/submission_list_{start_date}_to_{end_date}.json`

### Full Submission Data
- **Output directory**: `canvas_submissions_TIMESTAMP/` (or custom with `-o` option)
- **Submission list**: Saved within the output directory
- **Individual submissions**: Saved as separate files within the output directory
- **Forms**: Saved within the output directory (one per unique form_id)

### Notes
- The `working/` directory is gitignored and contains query result files
- The `canvas_submissions_*/` directories are gitignored and contain full submission data
- All output directories are automatically excluded from version control

## Authentication

All scripts support two authentication methods:

1. **Basic Auth** (username/password):
   ```bash
   python script.py -u user@example.com -p password
   ```

2. **OAuth Bearer Token**:
   ```bash
   python script.py --bearer-token YOUR_TOKEN
   ```

If credentials are configured in `canvas_api_config.json`, you can run scripts without providing authentication on the command line.

## Configuration File

The `canvas_api_config.json` file structure:
```json
{
    "username": "your_username@example.com",
    "password": "your_password",
    "bearer_token": null,
    "form_id": 1234567
}
```

- `username` and `password`: For Basic Auth
- `bearer_token`: For OAuth authentication (set to `null` if using Basic Auth)
- `form_id`: Optional, used for filtering submissions (not required for form operations)

**Note:** The `form_id` in the config is used for filtering only. When retrieving full submissions, the form_id is automatically extracted from each submission's data for proper form retrieval and transformation.

## Security

**Important Security Notes:**

1. **Config Files**: The `canvas_api_config.json` file and all `canvas_api_config_*.json` files contain sensitive credentials and are excluded from version control via `.gitignore`. Never commit these files to the repository.

2. **Output Directories**: The following directories are gitignored:
   - `working/` - Query result files
   - `Test/` - Test files
   - `Old/` - Archive files
   - `canvas_submissions_*/` - Submission output directories
   - `*.log` - Log files

3. **Credentials**: Never hardcode credentials in scripts. Always use the config file or command-line arguments.

4. **History**: All credentials have been removed from git history. If you need to rotate passwords, do so immediately if they were ever committed.

## Common Workflows

### Workflow 1: List All Forms
```bash
# Get list of all forms
python canvas_api_list_forms_v3.py --status published

# Review the output in working/canvas_forms_*.json to find form IDs
```

### Workflow 2: Get a Specific Form
```bash
# Get full form structure
python canvas_api_get_forms_v3.py --form-id 12345
```

### Workflow 3: List Submissions for Review
```bash
# List submissions from last 30 days
python canvas_api_list_submissions_v3.py --days 30

# Review submission_list_*.json in working/ directory
```

### Workflow 4: Retrieve and Transform Submissions
```bash
# Get full submissions with transformation
python canvas_api_get_submissions_v3.py --start-date 2024-01-01 --end-date 2024-01-31

# Results saved in canvas_submissions_TIMESTAMP/ directory
```

### Workflow 5: Transform Existing Submission
```bash
# Transform a previously saved submission
python canvas_transform_v3_to_v2.py -f form.json -v submission_v3.json -o submission_v2.json
```

## Troubleshooting

### Import Errors
If you see "Error importing from canvas_api_v3", ensure all `*_v3.py` files are in the same directory.

### Authentication Errors
- Verify credentials in `canvas_api_config.json`
- Check that you're using the correct authentication method (Basic Auth vs Bearer Token)
- Ensure credentials are valid and have proper API access

### No Submissions Found
- Check date range (default is last 7 days)
- Verify form_id filter if used
- Check API access permissions

### Transformation Failures
- Ensure form data is available (form is retrieved automatically from submission's form_id)
- Check that form structure matches the submission
- Review log files for detailed error messages

## License

See LICENSE file for details.
