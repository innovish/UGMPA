# Deployment Guide

This repository includes GitHub Actions for automated CI/CD workflows.

## Automated Workflows

### 1. Continuous Integration (CI)
**Trigger**: Every push to `main` and all pull requests

**Actions**:
- ✅ Checks Python syntax
- ✅ Verifies critical files exist
- ✅ Ensures security (checks for exposed API keys)
- ✅ Validates dependencies installation

### 2. Deployment Pipeline
**Trigger**: Every push to `main` or manual dispatch

**Actions**:
- ✅ Installs Python and dependencies
- ✅ Creates deployment artifacts
- ✅ Uploads deployment package

## How to Deploy from Cursor

### Method 1: Git Commit & Push (Recommended)

1. **Make your changes** in Cursor
2. **Stage your files**:
   ```bash
   git add .
   ```
3. **Commit your changes**:
   ```bash
   git commit -m "Your descriptive commit message"
   ```
4. **Push to GitHub**:
   ```bash
   git push origin main
   ```

GitHub Actions will automatically run on push!

### Method 2: Using Cursor's Git Integration

1. Open the Source Control panel (Ctrl+Shift+G / Cmd+Shift+G)
2. Stage your changes by clicking the "+" icon
3. Write a commit message
4. Click the checkmark to commit
5. Click "..." menu → "Push" to push to GitHub

### Method 3: Manual Trigger

1. Go to your repository on GitHub: https://github.com/innovish/UGMPA
2. Click on "Actions" tab
3. Select "Deploy to GitHub Pages" workflow
4. Click "Run workflow" button
5. Select the branch (usually `main`)
6. Click "Run workflow"

## Viewing Deployment Status

After pushing, you can:
1. Go to GitHub repository
2. Click "Actions" tab
3. See real-time progress of your workflows
4. Click on any workflow run to see detailed logs

## Workflow Status Badge

To add a workflow status badge to your README:

```markdown
![CI](https://github.com/innovish/UGMPA/workflows/Continuous%20Integration/badge.svg)
```

## Branch Protection Rules (Optional)

To protect your `main` branch:
1. Go to repository Settings
2. Navigate to "Branches"
3. Add rule for `main` branch
4. Enable:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Select your CI workflow

## Local Testing

Test your workflows locally before pushing:

```bash
# Install act (GitHub Actions runner)
# Windows (using Chocolatey):
choco install act-cli

# Or download from: https://github.com/nektos/act/releases

# Run workflows locally
act push  # Simulate push event
act pull_request  # Simulate PR event
```

## Troubleshooting

### Workflow fails with "config.json not found"
- This is expected! `config.json` should be in `.gitignore`
- Create `config.json` locally with your API keys
- GitHub Actions will need API keys set as secrets

### Workflow fails with API key errors
- Go to repository Settings → Secrets and variables → Actions
- Add secret: `GEMINI_API_KEY`
- Workflow can access it via `${{ secrets.GEMINI_API_KEY }}`

### Deploy artifact not found
- Check the "Actions" tab for error details
- Verify all required files are committed
- Ensure `.gitignore` doesn't exclude necessary files

## Next Steps

For production deployment, consider:
- ⚡ Deploy to cloud platforms (Heroku, Render, AWS, etc.)
- 🔒 Set up environment variables for API keys
- 📊 Add monitoring and logging
- 🧪 Write comprehensive tests
- 📈 Set up performance monitoring

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)

