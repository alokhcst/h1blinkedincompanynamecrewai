# Slack Jobs Tool - Debugging Guide

## Problem
The `slack_jobs_task` is not reading messages properly. The agent sometimes responds with "I cannot access Slack" instead of actually calling the tool.

## Solution: Enhanced Logging

### What Changed

#### 1. Added Comprehensive Logging to SlackJobsTool
The tool now logs every step with detailed information:

- **Tool Invocation**: Confirms when `_run()` is called
- **Parameters**: Logs all input parameters
- **SLACK_BOT_TOKEN**: Confirms token is set (shows length for security)
- **Time Window**: Shows current time, cutoff date, and timestamp
- **Channel Lookup**: Step-by-step progress finding the channel
- **Message Fetching**: Detailed pagination and message counts
- **File Saving**: Confirms files are written
- **Completion**: Final summary with message count

#### 2. Updated Agent Configuration
Made it crystal clear that the agent MUST use the tool:

```yaml
slack_reader:
  goal: MUST call SlackJobsTool to read ALL messages
  backstory: |
    You are a specialized tool operator. Your ONLY job is to call SlackJobsTool.
    CRITICAL: You MUST use the tool - you CANNOT access Slack directly.
    NEVER say "I cannot access" - instead, immediately call the tool.
```

#### 3. Updated Task Configuration
Added mandatory instructions:

```yaml
slack_jobs_task:
  description: |
    MANDATORY: Call SlackJobsTool with these exact parameters:
      - channel_name: "h1bjobs"
      - days_back: 30
    DO NOT say you cannot access Slack - you MUST use the tool.
```

### Detailed Logging Output

When the tool runs, you'll see:

```
================================================================================
SlackJobsTool._run() CALLED
================================================================================
Parameters:
  - channel_name: h1bjobs
  - days_back: 30
  - output_file_path: None
✓ SLACK_BOT_TOKEN found (length: 55)
Output paths:
  - Text file: output/slack_jobs.txt
  - JSON file: output/slack_jobs_raw.json
Time window:
  - Current UTC time: 2025-11-04T12:00:00.000000
  - Cutoff date: 2025-10-05T12:00:00.000000
  - Cutoff timestamp: 1728129600.0
STEP 1: Looking up Slack channel: #h1bjobs
Found 5 channels. Searching for: #h1bjobs
✓ Found channel #h1bjobs with ID: C12345678
STEP 2: Fetching messages from channel C12345678
Fetching page 1 of messages...
Page 1: Retrieved 50 messages (total: 50)
No more pages to fetch
✓ Retrieved 50 total messages from #h1bjobs
STEP 3: Formatting 50 messages for output
Processing messages (oldest first)...
✓ Formatted 50 messages into 1250 lines
STEP 4: Saving output files
✓ Saved plaintext to: output/slack_jobs.txt
✓ Saved raw JSON to: output/slack_jobs_raw.json
================================================================================
SlackJobsTool COMPLETE - 50 messages processed
================================================================================
```

## How to Debug

### Step 1: Test the Tool Directly

Run the test script to see if the tool works:

```powershell
python test_slack_logging.py
```

This will:
- Check if `SLACK_BOT_TOKEN` is set
- Call the tool directly
- Show all detailed logging
- Save output to `output/slack_jobs_test.txt`

### Step 2: Check for Common Issues

**Issue 1: Token Not Set**
```powershell
# Check if token is set
echo $env:SLACK_BOT_TOKEN

# Set it if missing
$env:SLACK_BOT_TOKEN = "xoxb-your-token-here"
```

**Issue 2: Bot Not Invited to Channel**
- Go to Slack
- Open #h1bjobs channel
- Type `/invite @YourBotName`

**Issue 3: Missing Permissions**
Bot needs these scopes:
- `channels:history` - Read messages from public channels
- `channels:read` - View basic channel info

**Issue 4: Wrong Channel Name**
- Channel name is case-sensitive
- Use `h1bjobs` (without the `#`)

### Step 3: Run the Full Crew

```powershell
crewai run
```

Watch for these log lines:
- `SlackJobsTool._run() CALLED` - Confirms tool was invoked
- `✓ SLACK_BOT_TOKEN found` - Token is available
- `✓ Found channel ID:` - Channel was found
- `✓ Retrieved X total messages` - Messages were fetched
- `✓ Saved plaintext to:` - Files were written

### Step 4: Check Output Files

After running, check:

```powershell
# Check if files exist
ls output/slack_jobs*.txt, output/slack_jobs*.json

# View the plaintext log
cat output/slack_jobs.txt

# Check JSON structure
cat output/slack_jobs_raw.json | Select-Object -First 50
```

## What to Look For in Logs

### ✓ Good Signs
- `SlackJobsTool._run() CALLED` appears
- `✓ SLACK_BOT_TOKEN found`
- `✓ Found channel ID:`
- `✓ Retrieved X total messages` (X > 0)
- `SlackJobsTool COMPLETE`

### ✗ Bad Signs
- No log line with `SlackJobsTool._run() CALLED`
  → Agent didn't call the tool
  → Check agent/task configuration
  
- `ERROR: Missing SLACK_BOT_TOKEN`
  → Set the environment variable
  
- `ERROR: Could not find Slack channel`
  → Check channel name
  → Verify bot is invited to channel
  → Check bot has `channels:read` scope
  
- `Slack API error: invalid_auth`
  → Invalid token
  → Get a new token from Slack
  
- `Slack API error: missing_scope`
  → Bot missing required permissions
  → Add scopes in Slack app settings
  
- `✓ Retrieved 0 total messages`
  → No messages in the time window
  → Try increasing `days_back` parameter
  → Check if channel has any messages

## Troubleshooting Checklist

- [ ] `SLACK_BOT_TOKEN` environment variable is set
- [ ] Token is valid (starts with `xoxb-`)
- [ ] Bot has `channels:history` and `channels:read` scopes
- [ ] Bot is invited to `#h1bjobs` channel
- [ ] Channel name is exactly `h1bjobs` (no `#`)
- [ ] Test script (`test_slack_logging.py`) runs successfully
- [ ] Log shows `SlackJobsTool._run() CALLED`
- [ ] Output files are created in `output/` directory

## Next Steps

After fixing any issues:

1. Run the test script to verify tool works
2. Run `crewai run` to execute the full crew
3. Check both tasks complete:
   - `slack_jobs_task` - Fetches messages
   - `slack_parser_task` - Extracts job details
4. Review output files:
   - `output/slack_jobs.txt` - Human-readable log
   - `output/slack_jobs_raw.json` - Raw data for parsing
   - `output/slack_parsed_jobs.txt` - Extracted job details

## Support

If you still see issues:

1. Run `python test_slack_logging.py` and share the full output
2. Check if the log contains `SlackJobsTool._run() CALLED`
3. Look for any ERROR lines in the output
4. Verify the Slack token is correct and has proper scopes

