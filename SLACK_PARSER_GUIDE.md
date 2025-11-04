# Slack Parser Tool Guide

## Overview

The Slack Parser Tool reads saved Slack messages from JSON, matches them against your company list, optionally filters by keywords, and extracts job details.

## Workflow

### Step 1: Fetch Slack Messages
```powershell
# First, get messages from Slack
$env:SLACK_BOT_TOKEN = "xoxb-your-token"
python test_slack_tool.py
```

This creates:
- `output/slack_jobs.txt` - Human-readable messages
- `output/slack_jobs_raw.json` - Raw JSON data

### Step 2: Parse and Match Jobs
```powershell
# Parse the JSON and match companies
python test_slack_parser.py
```

This creates:
- `output/slack_parsed_jobs.txt` - Matched jobs in format: `company, title, id, url`

### Step 3: Run Full Crew (All Tasks)
```powershell
crewai run
```

This runs all three tasks sequentially:
1. Slack Reader → Fetches messages
2. Slack Parser → Matches companies and extracts jobs
3. LinkedIn Researcher → Searches additional jobs

## How the Parser Works

### 1. Company Matching

The parser looks for company names from `H1BCompanyNameAtlanta.txt` in the message text.

**Matching strategies:**
- Exact match (case-insensitive)
- Normalized match (ignores punctuation, suffixes like LLC, Inc)
- Handles variations (e.g., "Microsoft" matches "Microsoft Corporation")

**Example companies from your list:**
- Emory University
- EY
- Microsoft
- Deloitte Consulting LLP
- etc.

### 2. Job URL Extraction

Finds LinkedIn job URLs in messages:
```
https://www.linkedin.com/jobs/view/1234567890
```

Extracts:
- Job ID: `1234567890`
- Job URL: Full URL

### 3. Job Title Extraction

Looks for job titles using patterns:
- `Role: Senior Data Engineer`
- `Position: Cloud Architect`
- `hiring a Data Scientist`
- Attachment titles

### 4. Keyword Filtering (Optional)

If keywords provided, checks if ANY keyword appears in:
- Message text
- Job title
- Attachments

**Your keywords:**
- leadership, Snowflake, Azure Databricks, Data Architecture
- Data Engineering, AI Engineering Leader, AWS Solutions Architect
- Azure Solutions Architect, Data Science, DevOps, Cloud Engineering

## Output Format

```
company_name, job_title, job_id, job_url
```

**Example:**
```
=== Slack Jobs Matched ===
Total jobs: 15
Companies matched: 8
Keywords used: Data Engineering, Cloud, AWS, Azure...
================================================================================

Microsoft, Senior Data Engineer, 4058926781, https://www.linkedin.com/jobs/view/4058926781
Google, Cloud Solutions Architect, 4059876543, https://www.linkedin.com/jobs/view/4059876543
Amazon, DevOps Engineer, 4060123456, https://www.linkedin.com/jobs/view/4060123456
...
```

## Command Reference

### Test Individual Components

```powershell
# 1. Fetch Slack messages (creates JSON)
python test_slack_tool.py

# 2. Parse JSON and match companies
python test_slack_parser.py

# 3. Search LinkedIn (separate task)
python test_tool.py
```

### Run Full Pipeline

```powershell
# Set all API keys
$env:SLACK_BOT_TOKEN = "xoxb-..."
$env:SERPER_API_KEY = "..."
$env:OPENAI_API_KEY = "sk-..."

# Run all tasks
crewai run
```

## Customization

### Change Companies List

Edit `knowledge/H1BCompanyNameAtlanta.txt`:
```
Microsoft
Google
Amazon
...
```

### Change Keywords

Edit in the tool call or `main.py`:
```python
keywords = ["Data Engineer", "Cloud", "Python"]
```

### Change Time Window

```python
# In tool call
tool._run(days_back=7)  # Last 7 days only
```

### Skip Keyword Filtering

```python
# Pass empty list or None
tool._run(keywords=None)  # Returns ALL jobs
```

## Integration in CrewAI

When you run `crewai run`, the tasks execute in sequence:

1. **slack_jobs_task** (Slack Reader)
   - Fetches messages from Slack API
   - Saves to `output/slack_jobs_raw.json`

2. **slack_parser_task** (Slack Parser) 
   - Reads the JSON file
   - Matches companies
   - Filters by keywords
   - Saves to `output/slack_parsed_jobs.txt`

3. **research_task** (LinkedIn Researcher)
   - Searches LinkedIn companies
   - Validates jobs
   - Saves to `output/companyname_linkedin1_jobs.txt`

## Tips

### For Maximum Results
- **No keywords**: Get all jobs mentioning your companies
- **Broad keywords**: Use general terms like "Engineer", "Data", "Cloud"
- **30+ days**: Increase `days_back` for more history

### For Focused Results
- **Specific keywords**: Use exact roles like "Senior Data Engineer"
- **Multiple keywords**: Tool returns jobs matching ANY keyword
- **7 days**: Use recent `days_back` for latest postings

## Troubleshooting

### "No jobs found"
- Check if company names in Slack match those in your list
- Try without keywords first to see all matches
- Check the raw JSON to see what text is in messages

### "Company not matched"
- Company name must appear in the Slack message
- Check for variations (add both "EY" and "Ernst & Young")
- Look at normalized matching (ignores punctuation)

### "Keywords too restrictive"
- Start with no keywords to see all jobs
- Add keywords one at a time
- Use partial words (e.g., "Data" matches "Data Engineering", "Data Science")

## Example Workflow

```powershell
# Day 1: Initial fetch
$env:SLACK_BOT_TOKEN = "xoxb-..."
python test_slack_tool.py
python test_slack_parser.py

# Review output/slack_parsed_jobs.txt
# Apply to interesting jobs

# Day 2+: Update and re-parse
python test_slack_tool.py  # Gets new messages
python test_slack_parser.py  # Parses again with deduplication
```

## Advanced: Combine Results

Both Slack and LinkedIn searches can run together:

```powershell
crewai run
```

Then merge results:
```powershell
# Combine all job files
cat output/slack_parsed_jobs.txt, output/companyname_linkedin1_jobs.txt | 
  sort | unique > output/all_jobs_combined.txt
```

This gives you jobs from BOTH Slack AND LinkedIn!

