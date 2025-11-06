# Security Guide

## API Key Security

### ⚠️ Important Security Notice

**API keys are sensitive credentials and should NEVER be committed to Git or shared publicly.**

### Current Protection Measures

1. ✅ **`config.json` is in `.gitignore`** - Your local `config.json` file will not be pushed to GitHub
2. ✅ **No hardcoded API keys** - The application no longer contains hardcoded API keys in the source code
3. ✅ **Example file provided** - `config.json.example` is a template without real credentials

### If Your API Key Was Previously Committed

If you previously committed an API key to this repository, you should:

1. **Immediately revoke the exposed API key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to APIs & Services > Credentials
   - Find and delete/revoke the exposed API key

2. **Generate a new API key:**
   - Create a new API key in Google Cloud Console
   - Update your local `config.json` with the new key

3. **Remove from Git history (optional but recommended):**
   - This requires rewriting Git history, which can be complex
   - Consider using tools like `git filter-branch` or BFG Repo-Cleaner
   - **Note:** If the repository is already public, the key may have been exposed

### Best Practices

1. **Always use `config.json` for local development:**
   - Copy `config.json.example` to `config.json`
   - Add your API key to `config.json` (which is gitignored)
   - Never commit `config.json` to Git

2. **Use environment variables for production:**
   - Set `GEMINI_API_KEY` as an environment variable
   - This is more secure for production deployments

3. **Regularly rotate API keys:**
   - Periodically generate new API keys
   - Revoke old, unused keys

4. **Monitor API usage:**
   - Check Google Cloud Console for unusual API usage
   - Set up alerts for unexpected activity

### Verifying Your Setup

To verify that `config.json` is properly ignored:

```bash
git status
```

You should NOT see `config.json` in the list of tracked files. If you do, it means the file was previously committed and needs to be removed from Git tracking:

```bash
git rm --cached config.json
git commit -m "Remove config.json from Git tracking"
```

