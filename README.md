# Canvas-API-v3-Tools

Tools to address Canvas API migration from v2 to v3

This project provides tools to retrieve submissions from the GoCanvas API and transform them from v3 format to v2 format.

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
   - Set `form_id` to the ID of the form you want to retrieve

## Usage

### Retrieve Submissions

Retrieve submissions from the GoCanvas API:

```bash
python canvas_api_v3.py
```

Options:
- `-u, --username`: GoCanvas username (overrides config file)
- `-p, --password`: GoCanvas password (overrides config file)
- `--bearer-token`: OAuth Bearer token (overrides config file)
- `-d, --days`: Number of days to look back (default: 7)
- `--form-id`: Filter by form ID (overrides config file)
- `-o, --output-file`: Output directory name (default: auto-generated timestamp)
- `--log-file`: Log file path (default: canvas_api_v3.log)
- `--log-level`: Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `--config-file`: Path to config file (default: canvas_api_config.json)

The script will:
1. Retrieve the form structure from the API
2. Retrieve all submissions for the specified date range
3. Save each submission as a v3 JSON file
4. Transform each submission to v2 format and save as `*_v2.json`

### Transform Existing Submissions

Transform a single submission from v3 to v2 format:

```bash
python canvas_transform_v3_to_v2.py
```

Options:
- `-f, --form`: Path to form structure JSON file (default: Canvas_Sample_Form_Nested.json)
- `-v, --v3`: Path to v3 submission JSON file (default: Canvas_v3.json)
- `-o, --output`: Output file path (default: Canvas_v3_transformed.json)
- `--log-file`: Log file path (default: canvas_transform_v3_to_v2.log)
- `--log-level`: Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

## Output Structure

When retrieving submissions, the script creates an output directory with:
- `form_{form_id}_{form_name}.json`: The form structure
- `submission_{id}_{number}.json`: Original v3 format submissions
- `submission_{id}_{number}_v2.json`: Transformed v2 format submissions

## Security

**Important**: The `canvas_api_config.json` file contains sensitive credentials and is excluded from version control via `.gitignore`. Never commit this file to the repository.

## License

See LICENSE file for details.
