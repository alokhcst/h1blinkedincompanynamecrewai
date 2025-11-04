# Per-Attachment Company Matching Fix

## Problem

Jobs were being incorrectly matched to companies. Examples:
- Job ID `4300664136` ([EY job](https://www.linkedin.com/jobs/view/4300664136/)) was matched to **Tata Consultancy Services**
- Job ID `4312365260` (Global Payments job) was matched to **Tata Consultancy Services**

## Root Cause

A **single Slack message can contain multiple attachments from different companies**, but the parser was:
1. Extracting ALL text from the entire message
2. Finding ONE company match for the whole message  
3. Assigning ALL job URLs in that message to that one company

### Example Slack Message Structure

```json
{
  "attachments": [
    {
      "id": 1,
      "blocks": [{ "text": "Global Payments Inc. hiring AI Engineer..." }],
      "fallback": "Global Payments Inc. hiring AI Engineer..."
    },
    {
      "id": 2,
      "blocks": [{ "text": "EY hiring Master Data Governance..." }],
      "fallback": "EY hiring Master Data Governance..."
    },
    {
      "id": 3,
      "blocks": [{ "text": "Tata Consultancy Services hiring..." }],
      "fallback": "Tata Consultancy Services hiring..."
    }
  ]
}
```

**Old Behavior:**
- Extract: "Global Payments Inc. hiring AI Engineer... EY hiring Master Data Governance... Tata Consultancy Services hiring..."
- Match: "Tata Consultancy Services" (longest match wins)
- Result: ALL 3 jobs assigned to Tata ❌

**New Behavior:**
- Process each attachment separately
- Attachment 1 → Global Payments
- Attachment 2 → EY  
- Attachment 3 → Tata
- Result: Each job correctly matched ✓

## Solution

### Changed Processing Logic

**Before (Message-Level Matching):**
```python
# OLD: Process entire message
full_text = self._extract_full_message_text(msg)
mentioned_company = self._find_matching_company(full_text, companies)

# Assign ALL jobs in message to this ONE company
for job_id, job_url in job_urls:
    matched_jobs.append({'company': mentioned_company, ...})
```

**After (Attachment-Level Matching):**
```python
# NEW: Process each attachment individually
attachments = msg.get('attachments', [])
for attachment in attachments:
    # Extract text from THIS attachment only
    att_text = self._extract_attachment_text(attachment)
    
    # Find company for THIS attachment
    mentioned_company = self._find_matching_company(att_text, companies)
    
    # Extract job URLs from THIS attachment
    job_urls = self._extract_linkedin_job_urls_from_text(att_text)
    
    # Match jobs to the correct company
    for job_id, job_url in job_urls:
        matched_jobs.append({'company': mentioned_company, ...})
```

### New Helper Methods

1. **`_extract_attachment_text(attachment)`**
   - Extracts text from a single attachment
   - Processes attachment blocks, fallback, title, fields
   - Returns text for that attachment only

2. **`_extract_linkedin_job_urls_from_text(text)`**
   - Renamed from `_extract_linkedin_job_urls(msg)`
   - Takes text parameter instead of entire message
   - Can be called per-attachment

3. **`_extract_job_title_from_text(text, job_url)`**
   - Renamed from `_extract_job_title(msg, job_url)`
   - Takes text parameter instead of entire message
   - Extracts job title from specific text

### Fallback for Messages Without Attachments

For messages without attachments (rare), the code falls back to message-level processing:
```python
if attachments:
    # Process each attachment separately (primary path)
    ...
else:
    # Fallback: Process message-level content
    full_text = self._extract_full_message_text(msg)
    ...
```

## Results

### Before Fix
```
❌ 4300664136 (EY job) → Incorrectly matched to Tata Consultancy Services
❌ 4312365260 (Global Payments) → Incorrectly matched to Tata Consultancy Services
```

### After Fix
```
✅ 4300664136 → Correctly matched to EY
✅ 4312365260 → Not matched (Global Payments Inc. not in company list)
```

### Output Comparison

**Before (17 jobs from 5 companies):**
- Tata Consultancy Services: 8 jobs (many incorrect)
- EY: 2 jobs
- Others: 7 jobs

**After (11 jobs from 6 companies):**
- Google: 3 jobs
- Amazon: 3 jobs
- EY: 2 jobs ✓ (including 4300664136)
- Georgia Institute of Technology: 1 job
- Tata Consultancy Services: 1 job ✓ (correctly reduced)
- Cognizant: 1 job

## Why Job 4312365260 is Missing

Job 4312365260 is a **Global Payments Inc.** job, but this company is NOT in `H1BCompanyNameAtlanta.txt`. 

**Solution:** Add "Global Payments Inc." or "Global Payments" to your company list if you want to track their jobs.

## Enhanced Logging

The new logging shows attachment-level processing:

```
Processing message 1/11
  Message 1: Processing 3 attachment(s)
    Word boundary match: 'Google' found in text
    Attachment 1: Found company: Google
      ✓ Matched job: Google - Outside Counsel Spend... (4314030020)
    
    Word boundary match: 'Amazon' found in text  
    Attachment 2: Found company: Amazon
      ✓ Matched job: Amazon - Senior Delivery Consultant... (4258508007)
    
    Word boundary match: 'EY' found in text
    Attachment 3: Found company: EY
      ✓ Matched job: EY - Data Management... (4309287936)
```

Each attachment is now processed independently!

## Files Modified

**`src/h1blinkedincompanynamecrewai/tools/slack_parser_tool.py`:**
- Rewrote main processing loop in `_run()` to iterate through attachments
- Added `_extract_attachment_text()` method
- Renamed `_extract_linkedin_job_urls()` → `_extract_linkedin_job_urls_from_text()`
- Renamed `_extract_job_title()` → `_extract_job_title_from_text()`
- Updated fallback logic for messages without attachments

## Testing

```powershell
# Test parser
python test_slack_parser_logging.py

# Verify specific job
cat output/slack_parsed_jobs_test.txt | findstr "4300664136"
# Output: EY, Master Data Governance/Management..., 4300664136, https://...

# Run full crew
crewai run
```

## Key Takeaways

1. **One Message ≠ One Company**: Slack messages can contain multiple job postings from different companies
2. **Attachment-Level Processing**: Each attachment must be matched independently
3. **Company List Matters**: Jobs are only matched if the company is in your list
4. **Detailed Logging**: Per-attachment logging helps debug matching issues

## Future Improvements

1. **Company Aliases**: Add support for variations (e.g., "Global Payments" → "Global Payments Inc.")
2. **Missing Company Warnings**: Log when jobs are found but company isn't in the list
3. **Company List Expansion**: Review Slack data to identify missing companies

