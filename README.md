# H1B Job Aggregator - AI-Powered Job Discovery System

## Overview

An intelligent multi-agent system that automatically discovers and aggregates H1B-sponsoring job opportunities from Slack channels. The system monitors job postings, matches them against a curated list of H1B-sponsoring companies, and outputs structured job data for easy review and application tracking.

## Purpose & Use Case

### Problem Statement
Finding H1B-sponsored jobs is time-consuming and requires:
- Monitoring multiple job boards and Slack channels
- Manually filtering companies known to sponsor H1B visas
- Cross-referencing job postings with H1B sponsor databases
- Tracking job URLs, IDs, and application status

### Solution
This automated system:
- ✅ **Monitors** Slack channels for job postings (e.g., #h1bjobs)
- ✅ **Matches** job postings against a list of 43+ H1B-sponsoring companies in Atlanta
- ✅ **Extracts** company name, job title, job ID, and LinkedIn URL
- ✅ **Outputs** clean, deduplicated job listings in plain text format
- ✅ **Processes** multiple job postings per message with accurate company attribution

## Target Audience

This tool is designed for:

1. **Job Seekers on H1B/OPT Visa**
   - Need to find companies that sponsor work visas
   - Want to focus efforts on H1B-friendly employers
   - Track job opportunities efficiently

2. **International Students**
   - Graduating students seeking employment authorization
   - Need verified H1B-sponsoring companies
   - Want automated job discovery

3. **Career Services & Immigration Advisors**
   - Supporting international students and professionals
   - Maintaining lists of visa-sponsoring employers
   - Providing job leads to clients

4. **Recruiters & Talent Acquisition**
   - Tracking competitor job postings
   - Monitoring H1B-sponsoring companies
   - Aggregating job market intelligence

## Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT SOURCES                               │
├─────────────────────────────────────────────────────────────────┤
│  1. Slack Channel: #h1bjobs                                     │
│  2. Company List: H1BCompanyNameAtlanta.txt (43 companies)      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT 1: Slack Reader                         │
├─────────────────────────────────────────────────────────────────┤
│  • Connects to Slack API                                        │
│  • Fetches messages from #h1bjobs (last 30 days)                │
│  • Extracts ALL message details (text, attachments, blocks)     │
│  • Saves raw JSON: output/slack_jobs_raw.json                   │
│  • Saves readable log: output/slack_jobs.txt                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT 2: Slack Parser                         │
├─────────────────────────────────────────────────────────────────┤
│  • Loads slack_jobs_raw.json                                    │
│  • Loads H1BCompanyNameAtlanta.txt                              │
│  • For each Slack message:                                      │
│    ├─ Processes each attachment separately                      │
│    ├─ Extracts LinkedIn job URLs                                │
│    ├─ Matches company name (word boundary matching)             │
│    ├─ Extracts job title from job posting text                  │
│    └─ Deduplicates by job ID                                    │
│  • Outputs: output/slack_parsed_jobs.txt                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT                                   │
├─────────────────────────────────────────────────────────────────┤
│  Format: company_name, job_title, job_id, job_url              │
│                                                                 │
│  Example:                                                       │
│  Amazon, Senior Data Engineer, 4258508007,                     │
│    https://www.linkedin.com/jobs/view/4258508007               │
│  EY, Master Data Governance Manager, 4300664136,               │
│    https://www.linkedin.com/jobs/view/4300664136               │
│  Google, Cloud Solutions Architect, 4314030020,                │
│    https://www.linkedin.com/jobs/view/4314030020               │
└─────────────────────────────────────────────────────────────────┘
```

## Technical Components

### AI/ML Framework
- **CrewAI** - Multi-agent orchestration framework
- **OpenAI GPT-4** - Language model for agent reasoning

### APIs & Integrations
- **Slack SDK** (slack-sdk >=3.23.0) - Fetch messages from Slack channels
- **Serper API** - Google Search API (for LinkedIn job discovery)
- **LinkedIn** - Job posting source (via URL extraction)

### Programming & Libraries
- **Python 3.10-3.13** - Core language
- **Pydantic** - Data validation and settings management
- **Regex (re)** - Pattern matching for URLs and company names
- **JSON** - Data serialization for Slack messages
- **Logging** - Detailed execution traces for debugging

### Development Tools
- **UV** - Fast Python package installer and dependency manager
- **Git** - Version control
- **VS Code** - Recommended IDE with debugger configuration

### Key Algorithms
1. **Per-Attachment Processing** - Each Slack message attachment is processed independently to avoid cross-contamination of company matches
2. **Word Boundary Matching** - Regex `\b` patterns ensure accurate company name matching (e.g., "Amazon" in "Amazon Web Services" ✓, but not "EY" in "survey" ✗)
3. **Length-Sorted Company Matching** - Longer, more specific company names are matched first to prevent short-name false positives
4. **Job ID Deduplication** - Prevents duplicate job listings across multiple messages

## Installation & Setup

### Prerequisites
- **Python 3.10 - 3.13** ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **A text editor or IDE** (VS Code recommended)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd h1blinkedincompanynamecrewai
```

### Step 2: Install UV Package Manager

```bash
pip install uv
```

### Step 3: Install Dependencies

```bash
crewai install
```

### Step 4: Set Up API Keys

You need three API keys:

#### 1. OpenAI API Key
- Sign up at https://platform.openai.com/
- Create an API key
- Copy the key (starts with `sk-...`)

#### 2. Serper API Key
- Sign up at https://serper.dev
- Get free API key (2,500 free searches)
- Copy the key

#### 3. Slack Bot Token
- Go to https://api.slack.com/apps
- Create a new app (or use existing)
- Add Bot Token Scopes:
  - `channels:history` - Read messages from public channels
  - `channels:read` - View basic channel info
- Install app to workspace
- Copy Bot User OAuth Token (starts with `xoxb-...`)
- Invite bot to `#h1bjobs` channel: `/invite @YourBotName`

**Detailed setup guides:**
- Serper: See `SETUP_INSTRUCTIONS.md`
- Slack: See `SLACK_SETUP.md`

### Step 5: Configure Environment Variables

**Option A: Create `.env` file** (recommended)
```bash
# Create .env file in project root
cat > .env << EOF
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-key-here
SLACK_BOT_TOKEN=xoxb-your-slack-token-here
EOF
```

**Option B: Set in PowerShell** (Windows)
```powershell
$env:OPENAI_API_KEY = "sk-your-openai-key-here"
$env:SERPER_API_KEY = "your-serper-key-here"
$env:SLACK_BOT_TOKEN = "xoxb-your-slack-token-here"
```

**Option C: Set in Bash** (Linux/Mac)
```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
export SERPER_API_KEY="your-serper-key-here"
export SLACK_BOT_TOKEN="xoxb-your-slack-token-here"
```

### Step 6: Customize Company List

Edit `knowledge/H1BCompanyNameAtlanta.txt` to add/remove companies:

```text
Amazon
Microsoft
Google
EY
Accenture
... (add your companies here)
```

## Running the Application

### Standard Run

```bash
crewai run
```

This will:
1. Fetch messages from Slack #h1bjobs channel
2. Parse messages and match companies
3. Output results to `output/` directory

### Output Files

After running, check these files:

```
output/
├── slack_jobs.txt               # Human-readable Slack message log
├── slack_jobs_raw.json          # Raw Slack API data (for debugging)
└── slack_parsed_jobs.txt        # Final job listings (YOUR MAIN OUTPUT)
```

**Main output format** (`slack_parsed_jobs.txt`):
```
Company Name, Job Title, Job ID, Job URL

Amazon, Senior Data Engineer, 4258508007, https://www.linkedin.com/jobs/view/4258508007
EY, Master Data Governance Manager, 4300664136, https://www.linkedin.com/jobs/view/4300664136
Google, Cloud Solutions Architect, 4314030020, https://www.linkedin.com/jobs/view/4314030020
```

## Testing & Debugging

### Test Individual Tools

**Test Slack Reader:**
```bash
python test_slack_logging.py
```

**Test Slack Parser:**
```bash
python test_slack_parser_logging.py
```

### Debug Mode (VS Code)

1. Open project in VS Code
2. Press `F5` or click "Run and Debug"
3. Select "Python: Current File"
4. Set breakpoints in code
5. Step through execution

Configuration is in `.vscode/launch.json`

### View Detailed Logs

The application logs detailed information to console:

```
================================================================================
SlackJobsTool._run() CALLED
================================================================================
✓ SLACK_BOT_TOKEN found (length: 55)
STEP 1: Looking up Slack channel: #h1bjobs
✓ Found channel ID: C12345678
STEP 2: Fetching messages from channel
✓ Retrieved 50 total messages
STEP 3: Processing messages
  Message 1: Processing 3 attachment(s)
    Attachment 1: Found company: Amazon
      ✓ Matched job: Amazon - Senior Data Engineer (4258508007)
================================================================================
SlackJobsTool COMPLETE - 50 messages processed
================================================================================
```

## Troubleshooting

### "ERROR: Missing SLACK_BOT_TOKEN"
- Ensure environment variable is set
- Check token starts with `xoxb-`
- Verify token is not expired

### "ERROR: Could not find Slack channel #h1bjobs"
- Verify channel name is correct (case-sensitive)
- Invite bot to channel: `/invite @YourBotName`
- Check bot has `channels:read` scope

### "No jobs found matching companies"
- Verify company names in `H1BCompanyNameAtlanta.txt`
- Check Slack channel has recent messages (last 30 days)
- Review `output/slack_jobs_raw.json` to see what was fetched

### "Jobs matched to wrong companies"
- This was fixed in latest version
- Ensure you're using per-attachment processing
- Check logs for "Attachment X: Found company: Y"

## Customization

### Change Slack Channel

Edit `src/h1blinkedincompanynamecrewai/config/tasks.yaml`:

```yaml
slack_jobs_task:
  description: >
    Use SlackJobsTool to read ALL messages from #YOUR_CHANNEL_HERE channel.
    Pass channel_name: "YOUR_CHANNEL_HERE", days_back: 30
```

### Change Time Window

Fetch messages from last 60 days instead of 30:

```yaml
Pass channel_name: "h1bjobs", days_back: 60
```

### Add More Companies

Edit `knowledge/H1BCompanyNameAtlanta.txt`:
- One company per line
- Can include variations (e.g., "IBM" and "IBM Corporation")
- Comments start with `#`

### Modify Output Format

Edit `src/h1blinkedincompanynamecrewai/tools/slack_parser_tool.py`:

Look for this section in `_run()` method:
```python
for job in matched_jobs:
    line = f"{job['company']}, {job['job_title']}, {job['job_id']}, {job['job_url']}"
    plaintext_lines.append(line)
```

Change to your preferred format (e.g., CSV, JSON, etc.)

## Project Structure

```
h1blinkedincompanynamecrewai/
├── src/h1blinkedincompanynamecrewai/
│   ├── main.py                      # Entry point
│   ├── crew.py                      # Agent & task orchestration
│   ├── config/
│   │   ├── agents.yaml              # Agent definitions
│   │   └── tasks.yaml               # Task definitions
│   └── tools/
│       ├── slack_tool.py            # Slack message fetcher
│       └── slack_parser_tool.py     # Job parser & matcher
├── knowledge/
│   └── H1BCompanyNameAtlanta.txt    # Company list (EDIT THIS)
├── output/                          # Generated files (git ignored)
│   ├── slack_jobs.txt
│   ├── slack_jobs_raw.json
│   └── slack_parsed_jobs.txt        # YOUR MAIN OUTPUT
├── tests/                           # Test scripts
│   ├── test_slack_logging.py
│   └── test_slack_parser_logging.py
├── .env                             # API keys (git ignored)
├── README.md                        # This file
├── SLACK_SETUP.md                   # Slack bot setup guide
├── SETUP_INSTRUCTIONS.md            # Serper API setup
└── pyproject.toml                   # Python dependencies
```

## Contributing

If you'd like to improve this project:

1. Add support for more Slack channels
2. Implement LinkedIn company page scraping
3. Add email notifications for new jobs
4. Create a web dashboard
5. Support for other visa types (e.g., TN, E-3)

## Known Limitations

1. **Slack API Rate Limits** - Limited to 1000 messages per request (paginated)
2. **Company Name Variations** - Requires exact or word-boundary matches
3. **Manual Company List** - Must maintain `H1BCompanyNameAtlanta.txt`
4. **No Historical Data** - Only fetches messages from specified time window
5. **LinkedIn URLs Only** - Doesn't parse non-LinkedIn job postings

## Support & Documentation

- **CrewAI Docs**: https://docs.crewai.com
- **Slack API Docs**: https://api.slack.com/docs
- **Serper API Docs**: https://serper.dev/docs
- **Project Issues**: Submit via GitHub Issues
- **Setup Guides**: 
  - `SLACK_SETUP.md` - Slack bot configuration
  - `SETUP_INSTRUCTIONS.md` - Serper API setup
  - `SLACK_DEBUGGING_GUIDE.md` - Troubleshooting Slack issues
  - `AMAZON_MATCHING_FIX.md` - Company matching algorithm details
  - `PER_ATTACHMENT_MATCHING_FIX.md` - Multi-job message handling

## License

This project is provided as-is for educational and personal use.

---

**Built with ❤️ using CrewAI - Making job search easier for international professionals**
