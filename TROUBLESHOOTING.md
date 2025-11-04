# Troubleshooting Guide

## Common Installation & Runtime Issues

### 1. ModuleNotFoundError: No module named 'dotenv'

**Error:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Cause:** The `python-dotenv` package is missing from dependencies.

**Solution:**
```bash
# Option 1: Install using UV (recommended)
uv pip install python-dotenv

# Option 2: Add to pyproject.toml and reinstall
# Already added in latest version: python-dotenv>=1.0.0,<2.0.0
crewai install

# Option 3: Install directly with pip
pip install python-dotenv
```

**Verify:**
```bash
python -c "from dotenv import dotenv_values; print('✓ Working!')"
```

---

### 2. File Access Denied During Installation

**Error:**
```
error: failed to remove file `...pandas/_libs/algos.cp311-win_amd64.pyd`: Access is denied. (os error 5)
```

**Cause:** A Python process or IDE is using files in the virtual environment.

**Solution:**
1. Close all Python processes
2. Close VS Code or your IDE
3. Close any Jupyter notebooks
4. Restart terminal
5. Try installation again:
```bash
crewai install
```

**Alternative:**
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
uv pip install -e .
```

---

### 3. ERROR: Missing SLACK_BOT_TOKEN

**Error:**
```
ERROR: Missing SLACK_BOT_TOKEN environment variable
```

**Solution:**

**Windows (PowerShell):**
```powershell
$env:SLACK_BOT_TOKEN = "xoxb-your-token-here"
```

**Linux/Mac:**
```bash
export SLACK_BOT_TOKEN="xoxb-your-token-here"
```

**Permanent (`.env` file):**
```bash
# Create .env file in project root
SLACK_BOT_TOKEN=xoxb-your-token-here
OPENAI_API_KEY=sk-your-key-here
SERPER_API_KEY=your-key-here
```

**Verify:**
```bash
python -c "import os; print('Token:', 'SET' if os.environ.get('SLACK_BOT_TOKEN') else 'NOT SET')"
```

---

### 4. ERROR: Could not find Slack channel #h1bjobs

**Error:**
```
ERROR: Could not find Slack channel #h1bjobs
```

**Possible Causes:**
1. Channel doesn't exist
2. Bot not invited to channel
3. Bot missing permissions

**Solution:**

**Step 1: Invite bot to channel**
- Go to Slack
- Open #h1bjobs channel
- Type: `/invite @YourBotName`

**Step 2: Check bot permissions**
- Go to https://api.slack.com/apps
- Select your app
- Go to "OAuth & Permissions"
- Verify these scopes:
  - `channels:history`
  - `channels:read`
- Reinstall app if needed

**Step 3: Verify channel name**
- Channel names are case-sensitive
- Use channel name without `#` in code
- Example: `h1bjobs` not `#h1bjobs`

---

### 5. No Jobs Found Matching Companies

**Error:**
```
No jobs found matching companies from knowledge/H1BCompanyNameAtlanta.txt
```

**Possible Causes:**
1. Company names don't match Slack messages
2. No messages in time window
3. No LinkedIn job URLs in messages

**Solution:**

**Check Slack data:**
```bash
# View raw JSON to see what was fetched
cat output/slack_jobs_raw.json

# Check how many messages were fetched
python -c "import json; data=json.load(open('output/slack_jobs_raw.json')); print(f'Messages: {len(data[\"messages\"])}')"
```

**Check company matching:**
1. Open `output/slack_jobs_raw.json`
2. Look for company names in messages
3. Compare with `knowledge/H1BCompanyNameAtlanta.txt`
4. Add missing companies to the list

**Increase time window:**
- Edit `src/h1blinkedincompanynamecrewai/config/tasks.yaml`
- Change `days_back: 30` to `days_back: 60` or higher

---

### 6. Jobs Matched to Wrong Companies

**Issue:** Jobs are assigned to incorrect companies.

**Cause:** Multiple job postings in one message (FIXED in latest version).

**Verify Fix:**
```bash
python test_slack_parser_logging.py
```

Look for per-attachment processing:
```
Message 1: Processing 3 attachment(s)
  Attachment 1: Found company: Google
  Attachment 2: Found company: Amazon
  Attachment 3: Found company: EY
```

If you see message-level matching instead, update to latest code.

---

### 7. Import Errors After Installation

**Error:**
```
ImportError: cannot import name 'X' from 'Y'
```

**Solution:**

**Reinstall dependencies:**
```bash
# Clean install
rm -rf .venv
python -m venv .venv
.venv\Scripts\activate
crewai install
```

**Or using UV:**
```bash
uv pip install -e .
```

**Verify Python version:**
```bash
python --version
# Should be 3.10, 3.11, 3.12, or 3.13
```

---

### 8. CrewAI Run Hangs or Times Out

**Issue:** `crewai run` starts but never completes.

**Possible Causes:**
1. API rate limits
2. Network issues
3. Large message history

**Solution:**

**Check API quotas:**
- OpenAI: https://platform.openai.com/usage
- Serper: https://serper.dev/dashboard

**Reduce time window:**
```yaml
# In tasks.yaml
days_back: 7  # Instead of 30
```

**Check logs for errors:**
- Look for timeout messages
- Check for API error responses
- Verify network connectivity

---

### 9. Linter/Type Errors

**Error:**
```
error: Argument of type "X" cannot be assigned to parameter "Y"
```

**These are warnings, not errors.** The code will still run.

**To suppress:**
```bash
# Add to code
# type: ignore[specific-error]
```

Or ignore linter in IDE settings.

---

### 10. Virtual Environment Not Activated

**Issue:** Commands not found or using wrong Python version.

**Symptoms:**
```
'crewai' is not recognized as an internal or external command
```

**Solution:**

**Activate virtual environment:**

**Windows (PowerShell):**
```powershell
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**Verify:**
```bash
which python  # Linux/Mac
where python  # Windows
# Should show path to .venv
```

---

## Quick Diagnostics

Run these commands to diagnose issues:

```bash
# 1. Check Python version
python --version

# 2. Check if virtual environment is active
python -c "import sys; print('VEnv:', '.venv' in sys.prefix)"

# 3. Check required packages
python -c "import crewai, dotenv, slack_sdk; print('✓ All packages installed')"

# 4. Check environment variables
python -c "import os; vars=['OPENAI_API_KEY', 'SERPER_API_KEY', 'SLACK_BOT_TOKEN']; [print(f'{v}: {'SET' if os.getenv(v) else 'NOT SET'}') for v in vars]"

# 5. Test Slack connection
python test_slack_logging.py

# 6. Test parser
python test_slack_parser_logging.py
```

---

## Getting Help

If issues persist:

1. **Check Logs:** Look for ERROR or WARNING messages in console output
2. **Enable Debug Logging:** Set `logging.DEBUG` in tools
3. **Review Documentation:**
   - `SLACK_SETUP.md` - Slack configuration
   - `SETUP_INSTRUCTIONS.md` - Serper setup
   - `SLACK_DEBUGGING_GUIDE.md` - Slack-specific issues
4. **Test Components:** Use test scripts to isolate issues
5. **Check Dependencies:** Ensure all packages are installed correctly

---

## Prevention

**Best Practices:**
- Always use virtual environments
- Keep `.env` file for API keys
- Add `output/` to `.gitignore`
- Test after major changes
- Review logs regularly
- Keep dependencies updated

---

**Last Updated:** November 4, 2025

