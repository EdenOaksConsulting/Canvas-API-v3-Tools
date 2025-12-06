# Git Repository Setup Instructions

## Prerequisites

You need Git installed on your system. Choose one of these options:

### Option 1: Install Git for Windows
1. Download from: https://git-scm.com/download/win
2. Run the installer with default settings
3. Restart your terminal/PowerShell

### Option 2: Use GitHub Desktop
1. Download from: https://desktop.github.com/
2. Install and sign in to your GitHub account
3. Use the GUI to initialize and commit

## Quick Setup (PowerShell)

Once Git is installed, run:

```powershell
.\initialize_repo.ps1
```

Or manually:

```powershell
# Initialize repository
git init

# Add files (canvas_api_config.json is automatically excluded by .gitignore)
git add .gitignore README.md canvas_api_config.json.example *.py requirements.txt

# Create initial commit
git commit -m "Initial commit: Canvas API submission retrieval and transformation tools"

# Add remote repository (replace with your GitHub repo URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Verify Files to Commit

Before committing, verify that `canvas_api_config.json` is NOT included:

```powershell
git status
```

You should see `canvas_api_config.json` listed under "Untracked files" but it should NOT be staged. The `.gitignore` file will prevent it from being committed.

## Files That Will Be Committed

- `.gitignore` - Excludes sensitive files
- `README.md` - Project documentation
- `canvas_api_config.json.example` - Template config file
- `canvas_api_v3.py` - Main API client and retrieval script
- `canvas_transform_v3_to_v2.py` - Transformation script
- `requirements.txt` - Python dependencies

## Files That Will NOT Be Committed (Protected by .gitignore)

- `canvas_api_config.json` - Contains your actual credentials
- `*.log` - Log files
- `canvas_submissions_*/` - Output directories
- `__pycache__/` - Python cache files

