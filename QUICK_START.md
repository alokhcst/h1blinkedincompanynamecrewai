# Quick Start Guide

## What This Does

This CrewAI project has two main agents:

1. **Slack Reader** - Reads job postings from your Slack `#h1bjobs` channel
2. **LinkedIn Researcher** - Searches LinkedIn for jobs at specific companies

## Setup (5 minutes)

### 1. Install Dependencies

```powershell
pip install uv
crewai install
```

### 2. Set API Keys

Get these API keys:
- **Serper**: https://serper.dev (free tier: 100 searches)
- **Slack Bot Token**: https://api.slack.com/apps (see SLACK_SETUP.md)
- **OpenAI**: https://platform.openai.com/api-keys

Set them:
```powershell
$env:SERPER_API_KEY = "your_serper_key"
$env:SLACK_BOT_TOKEN = "xoxb-your-slack-token"
$env:OPENAI_API_KEY = "sk-your-openai-key"
```

### 3. Invite Slack Bot to Channel

In Slack:
```
/invite @H1B Jobs Reader
```

(In the #h1bjobs channel)

### 4. Run!

```powershell
crewai run
```

## What Happens When You Run

1. **Slack Reader Agent** reads #h1bjobs channel
   - Extracts job details from last 30 days
   - Looks for LinkedIn URLs in messages
   - Outputs to: `output/slack_jobs.txt`

2. **LinkedIn Researcher Agent** searches companies
   - Reads company URLs from `knowledge/H1BCompanyNameAtlanta.txt`
   - Searches each company for jobs matching keywords
   - Validates jobs are from last 30 days
   - Checks relevance against keywords
   - Outputs to: `output/companyname_linkedin1_jobs.txt`

## Output Files

After running, check these files:

```
output/
├── slack_jobs.txt              # Jobs from Slack channel
├── slack_jobs.csv              # Slack jobs CSV
├── companyname_linkedin1_jobs.txt  # Jobs from LinkedIn
├── linkedin_jobs.csv           # LinkedIn jobs CSV
└── linkedin_company_matches.txt    # Company name mappings
```

## Output Format

Plain text, one job per line:
```
Company Name, Job ID, Job Role, Job URL
```

Example:
```
Microsoft, 4058926781, Senior Data Engineer, https://www.linkedin.com/jobs/view/4058926781
Google, 4059876543, Cloud Solutions Architect, https://www.linkedin.com/jobs/view/4059876543
```

## Testing Individual Tools

### Test Slack Tool Only:
```powershell
python test_slack_tool.py
```

### Test LinkedIn Tool Only:
```powershell
python test_tool.py
```

### Debug Step-by-Step:
```powershell
python debug_step_by_step.py
```

### Interactive Notebook:
```powershell
jupyter notebook linkedin_scraper_notebook.py
```

## Keywords Being Used

The crew searches for jobs matching these keywords:
- leadership
- Snowflake
- Azure Databricks
- Data Architecture
- Data Engineering
- Data Engineering Leader
- AI Engineering Leader
- AWS Solutions Architect
- Azure Solutions Architect
- Data Science
- DevOps
- Cloud Engineering

Edit in `src/h1blinkedincompanynamecrewai/main.py` to customize.

## Troubleshooting

### "Missing SERPER_API_KEY"
→ Set the environment variable (see step 2 above)

### "Missing SLACK_BOT_TOKEN"  
→ Create a Slack app and get the bot token (see SLACK_SETUP.md)

### "Channel not found"
→ Invite the bot to #h1bjobs: `/invite @H1B Jobs Reader`

### "400 Bad Request from Serper"
→ Check your query format or API key validity

### "No jobs found"
→ Either no jobs match your keywords, or they're older than 30 days

### "Crew failure: No valid task outputs"
→ The agent couldn't use the tool (usually missing API key)

## Debug Mode

See detailed debugging guide in the main response or run:
```powershell
# VS Code debugger with breakpoints
code debug_step_by_step.py
# Press F5 to debug

# Or run step-by-step
python debug_step_by_step.py
```

## Advanced Usage

### Change Time Window
Edit `DAYS_BACK = 30` to `DAYS_BACK = 7` for just last week

### Change Slack Channel
Edit `channel_name="h1bjobs"` to your channel name

### Add More Companies
Add LinkedIn company URLs to `knowledge/H1BCompanyNameAtlanta.txt` (one per line)

### Customize Keywords
Edit the keywords list in `src/h1blinkedincompanynamecrewai/main.py`

## Next Steps

1. Run the crew: `crewai run`
2. Check output files in `output/` folder
3. Review and apply to jobs!
4. Run again tomorrow - it deduplicates automatically

## Need Help?

- CrewAI Docs: https://docs.crewai.com
- Serper API: https://serper.dev/docs
- Slack API: https://api.slack.com/docs
- Open an issue in the project repo

