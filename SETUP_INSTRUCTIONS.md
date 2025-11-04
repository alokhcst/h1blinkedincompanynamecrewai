# Setup Instructions for H1B LinkedIn Company Name CrewAI

## Prerequisites

1. **Python 3.10-3.13** installed
2. **Serper API Key** from https://serper.dev

## Step 1: Get Serper API Key

1. Go to https://serper.dev
2. Sign up for a free account (100 free searches)
3. Get your API key from the dashboard
4. Copy the API key

## Step 2: Set Environment Variable

### On Windows (PowerShell):

**Current session only:**
```powershell
$env:SERPER_API_KEY = "your_api_key_here"
```

**Permanent (all sessions):**
```powershell
[System.Environment]::SetEnvironmentVariable('SERPER_API_KEY', 'your_api_key_here', 'User')
```

Then restart PowerShell for the change to take effect.

### On Linux/Mac (Bash):

**Current session only:**
```bash
export SERPER_API_KEY="your_api_key_here"
```

**Permanent:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export SERPER_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Step 3: Verify Setup

Test that the API key is set:

```powershell
# PowerShell
echo $env:SERPER_API_KEY
```

```bash
# Linux/Mac
echo $SERPER_API_KEY
```

## Step 4: Test the Tool

```powershell
python test_tool.py
```

You should see:
- Companies being processed
- Job listings found
- Output files created

## Step 5: Run the Crew

```powershell
crewai run
```

## Expected Output Files

After successful run:
- `output/companyname_linkedin1_jobs.txt` - Plain text job listings
- `output/linkedin_jobs.csv` - CSV with deduplication data
- `output/linkedin_company_matches.txt` - Company name mappings

## Troubleshooting

### "ERROR: Missing SERPER_API_KEY"
- Make sure you set the environment variable
- Restart your terminal/PowerShell after setting it
- Verify with `echo $env:SERPER_API_KEY` (PowerShell) or `echo $SERPER_API_KEY` (Bash)

### "No jobs found"
- Keywords might be too specific
- Try broader keywords or fewer keywords
- Check that companies in the file have active job postings

### "Crew Failure: No valid task outputs"
- Usually means SERPER_API_KEY is not set
- Run `python test_tool.py` to verify the tool works
- Check the console logs for error messages

## API Usage Limits

- **Serper Free Tier**: 100 searches/month
- Each company processes multiple searches (company page + individual jobs)
- Monitor your usage at https://serper.dev/dashboard
- Consider upgrading if you need to process many companies regularly

## Contact & Support

For issues with:
- CrewAI: https://docs.crewai.com
- Serper API: https://serper.dev/support

