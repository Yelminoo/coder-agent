# CI/CD Quick Reference

## Status Badge

Add this to your README.md:
```markdown
![CI/CD Pipeline](https://github.com/YOUR_USERNAME/ai-coding-assistant/workflows/CI%2FCD%20Pipeline/badge.svg)
```

---

## GitHub Secrets Required

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DROPLET_IP` | Your Digital Ocean droplet IP | `164.92.123.45` |
| `DROPLET_USER` | SSH username on server | `aiuser` |
| `SSH_PRIVATE_KEY` | Private SSH key for deployment | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

---

## Quick Setup Commands

### Generate SSH Key for CI/CD
```bash
ssh-keygen -t ed25519 -C "github-actions" -f github-actions-key
```

### Add Public Key to Server
```bash
# Copy public key
cat github-actions-key.pub

# On server
ssh aiuser@YOUR_DROPLET_IP
echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
```

### Add Private Key to GitHub
```bash
# Copy private key
cat github-actions-key

# Go to GitHub repo → Settings → Secrets → New secret
# Name: SSH_PRIVATE_KEY
# Value: [paste private key content]
```

---

## Trigger Deployment

### Automatic
```bash
git add .
git commit -m "Update feature"
git push origin main
# Automatically deploys if tests pass
```

### Manual
1. Go to GitHub → Actions tab
2. Select "CI/CD Pipeline"
3. Click "Run workflow" → "Run workflow"

---

## View Logs

### GitHub Actions Logs
```
GitHub → Actions → [Select workflow run]
```

### Server Logs
```bash
ssh aiuser@YOUR_DROPLET_IP
sudo journalctl -u ai-assistant -f
```

---

## Test Locally

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term

# Run linting
black --check .
flake8 .
```

---

## Workflow Behavior

| Event | Tests Run? | Deploy? | Branch |
|-------|-----------|---------|--------|
| Push to main | ✅ | ✅ | main |
| Push to develop | ✅ | ❌ | develop |
| Pull request | ✅ | ❌ | any |
| Manual trigger | ✅ | ✅ | selected |

---

## Troubleshooting

### Pipeline Fails on Test
```bash
# Fix issues locally first
pytest tests/ -v
black .
flake8 .

# Then push
git add .
git commit -m "Fix tests"
git push
```

### Pipeline Fails on Deploy
```bash
# Test SSH connection
ssh -i github-actions-key aiuser@DROPLET_IP

# Check server status
ssh aiuser@DROPLET_IP "systemctl status ai-assistant"

# Verify git remote
ssh aiuser@DROPLET_IP "cd ~/ai-coding-assistant && git remote -v"
```

### Secret Not Working
1. Check secret name exactly matches workflow file
2. No extra spaces/newlines in secret value
3. Secret is set in correct repository

---

## Common Tasks

### Skip CI for Commit
```bash
git commit -m "Update docs [skip ci]"
```

### Deploy Specific Branch
Edit `.github/workflows/ci-cd.yml`:
```yaml
if: github.ref == 'refs/heads/YOUR_BRANCH'
```

### Add Environment Variables
```bash
# On server
echo "NEW_VAR=value" >> ~/ai-coding-assistant/.env
sudo systemctl restart ai-assistant
```

---

## Pipeline Stages

```
┌─────────────┐
│   Trigger   │  Push to main
└──────┬──────┘
       │
       ├─────────────┐
       ▼             ▼
┌──────────┐  ┌──────────────┐
│   Test   │  │ Security Scan│
└─────┬────┘  └──────────────┘
      │
      ▼ (if pass)
┌──────────┐
│  Deploy  │
└─────┬────┘
      │
      ▼
┌──────────┐
│ Verify   │
└──────────┘
```

---

## Cost

- **Free tier**: 2,000 minutes/month
- **This pipeline**: ~5 minutes per run
- **~400 free deployments** per month

---

## Resources

- [Full Guide](CI_CD_SETUP.md)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [SSH Action](https://github.com/appleboy/ssh-action)
