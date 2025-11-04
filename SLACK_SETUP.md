# Slack Integration Setup Guide

This guide shows how to set up Slack integration to read job postings from your `#h1bjobs` channel.

## Step 1: Create a Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. App Name: `H1B Jobs Reader`
5. Select your workspace
6. Click **"Create App"**

## Step 2: Add Bot Scopes (Permissions)

1. In your app settings, go to **"OAuth & Permissions"** (left sidebar)
2. Scroll down to **"Scopes"** → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"** and add these permissions:

   Required scopes:
   - `channels:history` - Read messages from public channels
   - `channels:read` - View basic channel information
   - `groups:history` - Read messages from private channels (if #h1bjobs is private)
   - `groups:read` - View basic info about private channels

## Step 3: Install App to Workspace

1. Scroll to top of **"OAuth & Permissions"** page
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
   - This is your `SLACK_BOT_TOKEN`

## Step 4: Invite Bot to Channel

In Slack:
1. Go to your `#h1bjobs` channel
2. Type: `/invite @H1B Jobs Reader`
3. Or click channel name → Integrations → Add apps → select your bot

The bot needs to be a member of the channel to read messages!

## Step 5: Set Environment Variable

### Windows (PowerShell):

**Current session:**
```powershell
$env:SLACK_BOT_TOKEN = "xoxb-your-token-here"
```

**Permanent:**
```powershell
[System.Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', 'xoxb-your-token-here', 'User')
```

### Linux/Mac (Bash):

```bash
# Add to ~/.bashrc or ~/.zshrc
export SLACK_BOT_TOKEN="xoxb-your-token-here"
source ~/.bashrc
```

## Step 6: Verify Setup

```powershell
# Check token is set
echo $env:SLACK_BOT_TOKEN

# Should start with: xoxb-
```

## Step 7: Test the Integration

Run a simple test:

```powershell
python -c "import os; from src.h1blinkedincompanynamecrewai.tools.slack_tool import SlackJobsTool; tool = SlackJobsTool(); print(tool._run())"
```

## Step 8: Run the Crew

Now you can run the crew which will read from Slack:

```powershell
crewai run
```

The crew will:
1. Run `slack_jobs_task` first - reads from #h1bjobs channel
2. Run `research_task` second - searches LinkedIn companies

## Output Files

- `output/slack_jobs.txt` - Jobs extracted from Slack
- `output/slack_jobs.csv` - CSV with all job details
- `output/companyname_linkedin1_jobs.txt` - Jobs from LinkedIn search
- `output/linkedin_jobs.csv` - LinkedIn jobs CSV

## Troubleshooting

### "Channel not found"
- Make sure the bot is invited to the channel
- Channel name should be without # (use "h1bjobs" not "#h1bjobs")
- Check that the channel exists and is spelled correctly

### "Missing SLACK_BOT_TOKEN"
- Set the environment variable
- Token must start with `xoxb-`
- Restart terminal after setting it

### "Not authorized"
- Check bot permissions in Slack App settings
- Make sure you added all required scopes
- Reinstall the app after adding scopes

### "No jobs found"
- Check that messages in #h1bjobs contain LinkedIn URLs
- URLs should be in format: `https://www.linkedin.com/jobs/view/1234567890`
- Try increasing `days_back` parameter

## Message Format

The tool looks for LinkedIn job URLs in messages. Works best with formats like:

```
@CompanyName is hiring a Senior Data Engineer!
Role: Senior Data Engineer
Location: Atlanta, GA
https://www.linkedin.com/jobs/view/1234567890
```

Or:

```
New job posting:
Company: Microsoft
Position: Cloud Solutions Architect
Apply: https://www.linkedin.com/jobs/view/9876543210
```

The tool will automatically extract:
- Company name (from @mentions or "Company:" lines)
- Job role (from "Role:" or "Position:" lines)
- LinkedIn job URL (automatically detected)
- Job ID (from the URL)

## Rate Limits

Slack API has rate limits:
- Tier 3: ~50 requests per minute
- Tier 4: ~100 requests per minute

The tool fetches up to 1000 messages at a time, which should be fine for most channels.

## Privacy & Security

- The bot can only read messages from channels it's invited to
- It cannot read DMs or private channels it's not a member of
- Bot token should be kept secret (never commit to git)
- Use environment variables, not hardcoded tokens

## Need Help?

- Slack API Docs: https://api.slack.com/docs
- Bot Token Guide: https://api.slack.com/authentication/token-types
- Scopes Reference: https://api.slack.com/scopes

