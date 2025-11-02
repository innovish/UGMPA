# Quick Start: Deploy from Cursor to GitHub

## 🚀 Fast Track (3 Commands)

```bash
git add .
git commit -m "Your changes description"
git push origin main
```

That's it! GitHub Actions will automatically run your CI/CD pipeline.

## 📋 Complete Process

### 1. Make Changes in Cursor
Edit your files as needed.

### 2. Commit Your Changes
```bash
# Stage all changes
git add .

# Commit with a message
git commit -m "Add new feature: audio streaming"

# Push to GitHub
git push origin main
```

### 3. Verify Deployment
- Visit: https://github.com/innovish/UGMPA/actions
- Watch your workflow run in real-time
- Green checkmark = success ✅

## 🔄 Daily Workflow

### Monday: Start Working
```bash
git pull origin main
# Make changes...
git add .
git commit -m "Monday morning updates"
git push origin main
```

### Throughout the Week
```bash
# Small fixes
git commit -am "Quick bug fix"
git push origin main
```

### Friday: Feature Complete
```bash
git add .
git commit -m "Completed feature X with tests"
git push origin main
```

## 🎯 Using Cursor's Git UI

### Option A: Command Palette
1. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
2. Type "Git: Commit"
3. Type "Git: Push"

### Option B: Source Control Panel
1. Click the source control icon in the sidebar (📦)
2. Click "+" next to changed files to stage
3. Type commit message
4. Click ✓ to commit
5. Click "Sync Changes" or "..." → "Push"

### Option C: Terminal in Cursor
1. Open integrated terminal: `Ctrl+`` ` (backtick)
2. Run git commands as shown above

## 📝 Commit Message Best Practices

**Good messages:**
- ✅ `Add user authentication`
- ✅ `Fix chapter parsing bug`
- ✅ `Update audio generation UI`
- ✅ `Refactor TTS provider logic`

**Bad messages:**
- ❌ `fix`
- ❌ `updates`
- ❌ `changes`
- ❌ `asdf`

**Format:**
```
<type>: <subject>

<optional body>

Examples:
feat: Add paragraph splitting feature
fix: Resolve encoding issue with Chinese characters
docs: Update deployment instructions
refactor: Simplify audio conversion logic
test: Add unit tests for chapter parser
```

## 🔍 Check Status Anytime

```bash
# See what changed
git status

# See detailed changes
git diff

# See commit history
git log --oneline -10

# Check remote status
git fetch
git status
```

## 🌿 Working with Branches

### Create a Branch for New Feature
```bash
git checkout -b feature/new-tts-provider
# Make changes...
git add .
git commit -m "Add MiniMax TTS support"
git push origin feature/new-tts-provider
```

### Merge Back to Main
1. Go to GitHub → Pull Requests
2. Create new PR from your branch
3. Review and merge

Or locally:
```bash
git checkout main
git merge feature/new-tts-provider
git push origin main
```

## 🐛 If Something Goes Wrong

### Undo Last Commit (Keep Changes)
```bash
git reset --soft HEAD~1
```

### Undo Last Commit (Discard Changes)
```bash
git reset --hard HEAD~1
```

### Discard Uncommitted Changes
```bash
git checkout .
```

### Revert a Specific Commit
```bash
git revert <commit-hash>
git push origin main
```

### Pull Latest Changes
```bash
git pull origin main
```

## 🔐 Authentication

If prompted for credentials:
- Use a Personal Access Token (not your password)
- Create one: GitHub → Settings → Developer settings → Personal access tokens
- Or use GitHub CLI: `gh auth login`

## 📊 Monitoring Your Deployments

Visit these URLs:
- **Actions**: https://github.com/innovish/UGMPA/actions
- **Code**: https://github.com/innovish/UGMPA
- **Issues**: https://github.com/innovish/UGMPA/issues

## 💡 Pro Tips

1. **Commit Often**: Small, frequent commits are better than big ones
2. **Push Daily**: Keep your remote repository up to date
3. **Write Good Messages**: Your future self will thank you
4. **Check Actions Tab**: Make sure deployments are working
5. **Use Branches**: Keep `main` always working
6. **Pull Before Push**: Always pull latest changes first

## 🆘 Need Help?

1. Check `DEPLOYMENT.md` for detailed info
2. Review GitHub Actions logs
3. See commit history: `git log --graph --oneline`
4. Check Cursor's Git output panel

## ✅ Checklist Before Pushing

- [ ] Code runs locally without errors
- [ ] Tested the feature works
- [ ] Committed all relevant files
- [ ] Wrote a clear commit message
- [ ] Pulled latest changes from remote
- [ ] Ready to deploy

---

**Remember**: Every push triggers automated testing and deployment! 🎉

