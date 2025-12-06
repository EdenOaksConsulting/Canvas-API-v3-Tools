# PowerShell script to initialize Git repository and prepare for first commit
# Run this script after Git is installed and available in your PATH

Write-Host "Initializing Git repository..." -ForegroundColor Green

# Initialize git repository
git init

if ($LASTEXITCODE -eq 0) {
    Write-Host "Repository initialized successfully!" -ForegroundColor Green
    
    # Add files (excluding those in .gitignore)
    Write-Host "`nAdding files to staging area..." -ForegroundColor Green
    git add .gitignore
    git add README.md
    git add canvas_api_config.json.example
    git add *.py
    git add requirements.txt
    
    Write-Host "`nFiles staged. Ready for commit!" -ForegroundColor Green
    Write-Host "`nTo commit, run:" -ForegroundColor Yellow
    Write-Host "  git commit -m 'Initial commit: Canvas API submission retrieval and transformation tools'" -ForegroundColor Cyan
    Write-Host "`nTo add a remote repository, run:" -ForegroundColor Yellow
    Write-Host "  git remote add origin <your-github-repo-url>" -ForegroundColor Cyan
    Write-Host "  git branch -M main" -ForegroundColor Cyan
    Write-Host "  git push -u origin main" -ForegroundColor Cyan
} else {
    Write-Host "`nError: Git is not installed or not in your PATH." -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Or use GitHub Desktop from https://desktop.github.com/" -ForegroundColor Yellow
}

