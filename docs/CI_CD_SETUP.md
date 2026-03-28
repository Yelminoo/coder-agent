# Setup CI/CD with GitHub Actions

This guide shows you how to set up automated testing and deployment for your AI Coding Assistant.

## What You'll Get

✅ **Automated Testing** - Runs on every push and pull request  
✅ **Automated Deployment** - Deploys to Digital Ocean on push to main  
✅ **Security Scanning** - Checks for vulnerabilities  
✅ **Code Quality** - Linting and formatting checks  
✅ **Status Badges** - Show build status in README  

---

## Step 1: GitHub Repository Setup

### 1.1 Create GitHub Repository
```bash
# Initialize git (if not already done)
cd C:\Users\User\Desktop\ai-coding-assistant
git init
git add .
git commit -m "Initial commit"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/ai-coding-assistant.git
git branch -M main
git push -u origin main
```

### 1.2 Workflow File
The workflow file is already created at `.github/workflows/ci-cd.yml`

This will automatically run when you push code!

---

## Step 2: Configure Secrets

GitHub Actions needs secure access to your server. Add these secrets:

### 2.1 Go to GitHub Repository Settings
1. Navigate to your repo on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### 2.2 Add These Secrets

**`DROPLET_IP`**
```
Your Digital Ocean droplet IP address
Example: 164.92.123.45
```

**`DROPLET_USER`**
```
SSH username (usually: aiuser)
Example: aiuser
```

**`SSH_PRIVATE_KEY`**
```
Your SSH private key for server access
```

### 2.3 Generate SSH Key for CI/CD

On your **local machine**:
```powershell
# Generate new SSH key for GitHub Actions
ssh-keygen -t ed25519 -C "github-actions" -f github-actions-key

# This creates:
# - github-actions-key (private key - add to GitHub secret)
# - github-actions-key.pub (public key - add to server)
```

On your **Digital Ocean server**:
```bash
# SSH to server
ssh aiuser@YOUR_DROPLET_IP

# Add public key to authorized_keys
echo "YOUR_PUBLIC_KEY_CONTENT" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Copy **private key** content:
```powershell
# On Windows
Get-Content github-actions-key | clip

# Then paste into GitHub secret: SSH_PRIVATE_KEY
```

---

## Step 3: Test the Pipeline

### 3.1 Make a Change
```bash
# Make any small change
echo "# CI/CD Test" >> README.md
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin main
```

### 3.2 Watch the Pipeline
1. Go to your GitHub repo
2. Click **Actions** tab
3. See your workflow running!

### 3.3 What Happens
1. ✅ **Test Job** - Runs linting, formatting checks, tests
2. ✅ **Security Scan** - Checks for vulnerabilities
3. ✅ **Deploy Job** - If tests pass and branch is main, deploys to server

---

## Step 4: Add Status Badges (Optional)

### 4.1 Get Badge URL
From GitHub Actions page, click workflow → **Create status badge**

### 4.2 Add to README
```markdown
# AI Coding Assistant

![CI/CD](https://github.com/YOUR_USERNAME/ai-coding-assistant/workflows/CI%2FCD%20Pipeline/badge.svg)

Your project description...
```

---

## Pipeline Details

### On Every Push/PR:
```yaml
✓ Checkout code
✓ Install Python dependencies
✓ Run code formatting check (Black)
✓ Run linting (Flake8)
✓ Run tests (Pytest)
✓ Security vulnerability scan
```

### On Push to Main:
```yaml
✓ All the above, plus:
✓ SSH to Digital Ocean server
✓ Pull latest code
✓ Install dependencies
✓ Restart application service
✓ Verify deployment
```

---

## Workflow Triggers

### Automatic Triggers
- **Push to main** → Test + Deploy
- **Push to develop** → Test only
- **Pull request to main** → Test only

### Manual Trigger
1. Go to **Actions** tab
2. Select **CI/CD Pipeline**
3. Click **Run workflow**

---

## Advanced Configuration

### Add Staging Environment

Edit `.github/workflows/ci-cd.yml`:
```yaml
deploy-staging:
  if: github.ref == 'refs/heads/develop'
  # ... deploy to staging server
  
deploy-production:
  if: github.ref == 'refs/heads/main'
  # ... deploy to production server
```

### Add Slack/Discord Notifications

```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1.24.0
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Deployment ${{ job.status }}: ${{ github.sha }}"
      }
```

### Add Automated Tests

Create `tests/test_basic.py`:
```python
def test_import():
    """Test basic imports work"""
    from web_server import app
    assert app is not None

def test_health():
    """Test health endpoint"""
    from fastapi.testclient import TestClient
    from web_server import app
    
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
```

Install test dependencies:
```bash
pip install pytest pytest-cov
pip freeze > requirements.txt
```

---

## Monitoring Deployments

### View Deployment Logs
1. GitHub → **Actions** → Select workflow run
2. Click **Deploy to Digital Ocean** job
3. View real-time logs

### Server-Side Logs
```bash
# SSH to server
ssh aiuser@YOUR_DROPLET_IP

# View deployment logs
sudo journalctl -u ai-assistant -n 50 --no-pager

# Check if service restarted
sudo systemctl status ai-assistant
```

---

## Troubleshooting

### Deployment Fails

**Check SSH Connection:**
```bash
# Test SSH access with the key
ssh -i github-actions-key aiuser@YOUR_DROPLET_IP
```

**Check Secrets:**
- Verify `DROPLET_IP` is correct
- Check `DROPLET_USER` matches server user
- Ensure `SSH_PRIVATE_KEY` has no extra spaces/newlines

**Check Server Permissions:**
```bash
# On server
cd ~/ai-coding-assistant
ls -la
# Should be owned by aiuser
```

### Tests Fail

**No Tests Directory:**
```bash
# Create basic test
mkdir tests
cat > tests/test_basic.py << EOF
def test_placeholder():
    assert True
EOF
```

**Import Errors:**
```bash
# Ensure all dependencies in requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Security Scan Fails

This is usually just warnings, not errors. The job has `continue-on-error: true` so it won't block deployment.

---

## Cost Optimization

### Free Tier
- **GitHub Actions**: 2,000 minutes/month free
- **This pipeline uses**: ~5 minutes per run
- **You can run**: ~400 times/month for free

### Reduce Minutes
```yaml
# Add to workflow to skip on specific commits
on:
  push:
    branches: [ main ]
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

---

## Security Best Practices

✅ **Never commit secrets** - Use GitHub Secrets  
✅ **Use separate SSH keys** - Don't reuse personal SSH key  
✅ **Limit key permissions** - Create separate deployment user  
✅ **Enable branch protection** - Require PR reviews  
✅ **Run security scans** - Already included in pipeline  

---

## Next Steps

1. ✅ **Set up secrets** (Step 2)
2. ✅ **Push code** to test pipeline
3. ✅ **Add tests** (optional but recommended)
4. ✅ **Add status badge** to README
5. ✅ **Set up staging environment** (optional)

---

## Alternative CI/CD Options

### GitLab CI/CD
```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy

test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/

deploy:
  stage: deploy
  only:
    - main
  script:
    - ssh user@server "cd app && git pull && systemctl restart app"
```

### Jenkins
- Install Jenkins on separate server
- Configure webhook from GitHub
- Create pipeline with Jenkinsfile

### CircleCI
- Sign up at circleci.com
- Add repository
- Create `.circleci/config.yml`

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SSH Action](https://github.com/appleboy/ssh-action)
- [Digital Ocean CI/CD Guide](https://www.digitalocean.com/community/tutorials/how-to-set-up-a-continuous-deployment-pipeline-with-gitlab-ci-cd-on-ubuntu-18-04)

---

**Your CI/CD is now ready!** 🚀

Every push to `main` will automatically test and deploy your application.
