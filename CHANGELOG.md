# Changelog

All notable changes to the H1B Job Aggregator project.

## [1.1.0] - 2025-11-05

### Added - Job Keyword Filtering Feature

#### New Features
- **Keyword Filtering System**: Filter jobs by customizable keywords (job titles, roles, technologies)
- **Default Keywords**: Pre-configured with 29 technical and leadership keywords covering:
  - Data & Analytics (7 keywords)
  - AI & Machine Learning (5 keywords)
  - Software Development (8 keywords)
  - Cloud & Architecture (9 keywords)

#### New Files
- `input/job_keywords.txt` - User-editable keyword configuration file
- `test_slack_parser_with_keywords.py` - Test script for keyword filtering
- `KEYWORD_FILTERING.md` - Comprehensive guide for keyword filtering feature
- `CHANGELOG.md` - This file

#### Enhanced Files
- `src/h1blinkedincompanynamecrewai/tools/slack_parser_tool.py`
  - Added `keywords_file_path` parameter
  - Added `_load_keywords()` method
  - Added `_matches_keywords()` method with word boundary matching
  - Integrated keyword filtering in job processing loop
  
- `src/h1blinkedincompanynamecrewai/config/tasks.yaml`
  - Updated `slack_parser_task` to include `keywords_file_path` parameter
  - Updated task description to document keyword filtering
  
- `.gitignore`
  - Added exception for `input/*.txt` to track keyword configuration
  
- `README.md`
  - Added Step 7: Customize Job Keywords section
  - Updated process flow diagram with keyword filtering
  - Expanded keyword examples by category
  - Updated Technical Components section
  - Updated Key Algorithms section
  - Updated Project Structure
  - Updated Support & Documentation links

#### Technical Details
- **Matching Algorithm**: Word boundary regex (`\b`) for precise keyword matching
- **Logic**: Jobs must match BOTH company name AND at least one keyword
- **Case Insensitive**: Keywords are matched regardless of case
- **Flexible**: Empty or missing keywords file results in no filtering (backward compatible)

#### Default Keywords Included
```
Data Engineer, Data Scientist, Machine Learning Engineer, AI Engineer,
Software Engineer, DevOps Engineer, Cloud Engineer, Full Stack Developer,
Backend Developer, Frontend Developer, Senior Developer, Lead Engineer,
Principal Engineer, Staff Engineer, Analytics Engineer, Business Intelligence,
Data Analyst, Solutions Architect, Technical Architect, System Engineer,
Data Engineering Manager, Data Architect, AWS Solutions Architect,
Azure Solutions Architect, Azure Databricks, Snowflake,
Director Data and AI, AI Leader, AI Manager
```

#### Benefits
- **Reduced Noise**: Filter out irrelevant jobs (HR, Legal, Sales, etc.)
- **Focused Results**: Only see jobs matching your career interests
- **Customizable**: Easily add/remove keywords based on job search goals
- **Performance**: ~50% reduction in output volume for typical technical roles

#### Testing
- New test script compares filtered vs non-filtered results
- Shows statistics on how many jobs were filtered out
- Validates keyword matching logic

### Configuration
- Keywords file location: `input/job_keywords.txt`
- One keyword per line
- Lines starting with `#` are comments
- Blank lines ignored
- Case-insensitive matching

### Backward Compatibility
- System works with or without keywords file
- Missing keywords file logs warning but continues without filtering
- No breaking changes to existing functionality

---

## [1.0.0] - 2025-11-04

### Initial Release

#### Features
- Slack channel monitoring (#h1bjobs)
- H1B company matching (43 companies in Atlanta)
- LinkedIn job URL extraction
- Per-attachment processing for multi-company messages
- Word boundary company name matching
- Job ID deduplication
- Plain text output format

#### Components
- SlackJobsTool - Fetch messages from Slack
- SlackParserTool - Parse messages and extract jobs
- CrewAI multi-agent orchestration
- OpenAI GPT-4 integration
- Serper API for search

#### Documentation
- README.md
- SLACK_SETUP.md
- SETUP_INSTRUCTIONS.md
- SLACK_DEBUGGING_GUIDE.md
- AMAZON_MATCHING_FIX.md
- PER_ATTACHMENT_MATCHING_FIX.md
- TROUBLESHOOTING.md

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

