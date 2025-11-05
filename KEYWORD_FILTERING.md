# Job Keyword Filtering Feature

## Overview

This document describes the new keyword filtering feature added to the Slack job parser. This feature allows you to refine job listings by matching against specific job titles and role keywords.

## Feature Description

### What It Does

The keyword filtering feature filters Slack job postings to show only those that match BOTH:
1. **Company Match**: Job is from a company in your H1B company list
2. **Keyword Match**: Job title/description contains at least one of your specified keywords

### Why It's Useful

Before this feature, the parser would return ALL jobs from H1B-sponsoring companies, including:
- HR roles
- Legal positions
- Administrative jobs
- Marketing positions
- Sales roles

With keyword filtering, you can focus on:
- ✅ Technical roles (Engineer, Developer, Architect)
- ✅ Data roles (Data Scientist, Data Analyst, Data Engineer)
- ✅ Specific domains (Machine Learning, Cloud, DevOps)
- ✅ Your career level (Senior, Lead, Principal)

## How to Use

### Step 1: Create/Edit Keywords File

The keywords file is located at: `input/job_keywords.txt`

**Format:**
- One keyword per line
- Keywords are case-insensitive
- Use `#` at the start of a line for comments
- Blank lines are ignored

**Example:**
```text
# Technical Roles
Data Engineer
Data Scientist
Machine Learning Engineer
AI Engineer
Software Engineer

# Infrastructure & Cloud
DevOps Engineer
Cloud Engineer
Solutions Architect
System Engineer

# Development
Full Stack Developer
Backend Developer
Frontend Developer
Senior Developer

# Leadership
Lead Engineer
Principal Engineer
Staff Engineer
Engineering Manager
```

### Step 2: Run the Parser

The parser will automatically use the keywords file:

```bash
# Run the full crew
crewai run

# Or test the parser directly
python test_slack_parser_with_keywords.py
```

## Technical Details

### Matching Algorithm

The keyword matching uses **word boundary matching** to ensure accurate results:

```python
# Pattern: \bkeyword\b
# This ensures:
# ✅ "Engineer" matches "Data Engineer"
# ✅ "Engineer" matches "Software Engineer"
# ❌ "Engineer" does NOT match "Engineering"
# ❌ "Analyst" does NOT match "Analysis"
```

### Where Matching Occurs

Keywords are checked against:
1. **Attachment text** - Where Slack stores job posting content
2. **Job title** - Extracted from the job posting

Both are concatenated and checked for keyword matches.

### Processing Flow

```
1. Load keywords from input/job_keywords.txt
2. For each job posting:
   a. Extract company name
   b. Extract job title and description
   c. Check if company matches H1B list
   d. Check if text contains any keyword
   e. Include job ONLY if BOTH match
3. Output filtered results
```

## Example Results

### Without Keyword Filtering

```
=== Slack Jobs Matched ===
Total jobs: 17
Companies matched: 6

Google, Outside Counsel Spend and Vendor Strategy Lead, 4314013813, https://...
Amazon, Senior Delivery Consultant, Data & GenAI, 4258508007, https://...
EY, Data Management & Strategy Manager, 4304494420, https://...
Georgia Tech, Data Engineer, 4334043398, https://...
TCS, AI Engineer, 4300664136, https://...
... (all jobs from matching companies)
```

### With Keyword Filtering (Engineer, Data, AI)

```
=== Slack Jobs Matched ===
Total jobs: 9
Companies matched: 4

Amazon, Senior Delivery Consultant, Data & GenAI, 4258508007, https://...
EY, Data Management & Strategy Manager, 4304494420, https://...
Georgia Tech, Data Engineer, 4334043398, https://...
TCS, AI Engineer, 4300664136, https://...
... (only jobs matching keywords)
```

## Configuration Files

### New Files Added

1. **`input/job_keywords.txt`**
   - User-editable keyword list
   - Default: 20 common technical job titles
   - Location: `input/` folder (tracked in Git)

### Modified Files

1. **`src/h1blinkedincompanynamecrewai/tools/slack_parser_tool.py`**
   - Added `keywords_file_path` parameter
   - Added `_load_keywords()` method
   - Added `_matches_keywords()` method
   - Integrated keyword filtering in job processing loop

2. **`src/h1blinkedincompanynamecrewai/config/tasks.yaml`**
   - Updated `slack_parser_task` description
   - Added `keywords_file_path` parameter
   - Updated expected output documentation

3. **`.gitignore`**
   - Added exception for `input/*.txt` files
   - Ensures keyword file is tracked in version control

4. **`README.md`**
   - Added Step 7: Customize Job Keywords
   - Updated process flow diagram
   - Added example output with keyword filtering
   - Updated testing section

## Testing

### Test Script

Run the dedicated test script to see keyword filtering in action:

```bash
python test_slack_parser_with_keywords.py
```

This script will:
1. Load existing Slack data (`output/slack_jobs_raw.json`)
2. Apply keyword filtering
3. Output results to `output/slack_parsed_jobs_test_keywords.txt`
4. Compare with non-filtered results
5. Show how many jobs were filtered out

### Expected Output

```
================================================================================
Testing SlackParserTool with Keyword Filtering
================================================================================
✓ All required files found
Input files:
  - Slack JSON: output/slack_jobs_raw.json
  - Companies: knowledge/H1BCompanyNameAtlanta.txt
  - Keywords: input/job_keywords.txt
Output file:
  - output/slack_parsed_jobs_test_keywords.txt

Running SlackParserTool with keyword filtering...
================================================================================
✓ Loaded 50 messages from JSON
✓ Loaded 43 companies
✓ Loaded 20 keywords for filtering
Processing messages to extract jobs
  Message 1: Processing 3 attachment(s)
    Attachment 1: Found company: Amazon
      Keyword match found: 'Data Engineer'
      ✓ Matched job: Amazon - Senior Data Engineer (4258508007)
...
✓ Found 9 total matched jobs
✓ Saved 9 jobs to output/slack_parsed_jobs_test_keywords.txt

Comparison:
  - Without keyword filtering: 17 jobs
  - With keyword filtering: 9 jobs
  - Filtered out: 8 jobs
```

## Customization Tips

### For Data Roles

```text
Data Engineer
Data Scientist
Data Analyst
Machine Learning Engineer
ML Engineer
AI Engineer
Analytics Engineer
Business Intelligence
```

### For Software Engineering

```text
Software Engineer
Backend Engineer
Frontend Engineer
Full Stack Engineer
Senior Software Engineer
Staff Engineer
Principal Engineer
```

### For Cloud & DevOps

```text
Cloud Engineer
DevOps Engineer
Site Reliability Engineer
Infrastructure Engineer
Platform Engineer
Solutions Architect
Cloud Architect
```

### For Leadership

```text
Engineering Manager
Technical Lead
Lead Engineer
Principal Engineer
Staff Engineer
Director of Engineering
VP of Engineering
```

## Troubleshooting

### Issue: Too Few Results

**Problem**: Very few or no jobs returned after filtering

**Solutions:**
1. Add more keywords to `input/job_keywords.txt`
2. Use broader terms (e.g., "Engineer" instead of "Senior Software Engineer")
3. Check if keywords match actual job titles in Slack messages
4. Run without keywords first to see all available jobs: `python test_slack_parser.py`

### Issue: Too Many Results

**Problem**: Still getting irrelevant jobs

**Solutions:**
1. Use more specific keywords
2. Combine role + domain (e.g., "Machine Learning Engineer" instead of just "Engineer")
3. Remove generic terms that match many roles

### Issue: Keywords Not Loading

**Problem**: Warning message about missing keywords file

**Solutions:**
1. Verify file exists: `dir input\job_keywords.txt` (Windows) or `ls input/job_keywords.txt` (Linux/Mac)
2. Check file name spelling (case-sensitive on Linux/Mac)
3. Ensure file has content (not empty)
4. Verify file encoding is UTF-8

## Future Enhancements

Potential improvements for this feature:

1. **Negative Keywords**: Exclude jobs with certain terms (e.g., -"unpaid", -"internship")
2. **Keyword Groups**: Require matches from multiple categories (e.g., role AND technology)
3. **Regex Support**: Allow pattern matching for more complex filtering
4. **Location Filtering**: Add geographical preferences
5. **Experience Level**: Filter by seniority (Junior, Senior, Lead, etc.)
6. **Salary Range**: Filter by posted compensation (if available)

## Version History

- **v1.0** (2025-11-05): Initial release of keyword filtering feature
  - Basic word boundary matching
  - Single keywords file support
  - Integration with Slack parser

## Related Documentation

- [README.md](README.md) - Main project documentation
- [SLACK_SETUP.md](SLACK_SETUP.md) - Slack integration setup
- [SLACK_PARSER_GUIDE.md](SLACK_PARSER_GUIDE.md) - Parser usage guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

