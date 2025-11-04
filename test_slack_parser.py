#!/usr/bin/env python
"""Test the Slack Parser Tool"""
import os
from src.h1blinkedincompanynamecrewai.tools.slack_parser_tool import SlackParserTool

print("Testing SlackParserTool...")
print("=" * 80)

# Create tool
tool = SlackParserTool()

# Test parameters
slack_json = "output/slack_jobs_raw.json"
companies_file = "knowledge/H1BCompanyNameAtlanta.txt"

# Check if files exist
if not os.path.exists(slack_json):
    print(f"\n❌ Slack JSON not found: {slack_json}")
    print("Run this first to get Slack messages:")
    print("  python test_slack_tool.py")
    exit(1)

if not os.path.exists(companies_file):
    print(f"\n❌ Companies file not found: {companies_file}")
    exit(1)

print(f"\n✓ Slack JSON: {slack_json}")
print(f"✓ Companies file: {companies_file}")
print(f"✓ No keyword filtering - will return ALL jobs")
print("\n" + "=" * 80 + "\n")

# Run the tool
print("Running SlackParserTool...")
result = tool._run(
    slack_json_path=slack_json,
    companies_file_path=companies_file,
    output_file_path="output/slack_parsed_test.txt"
)

print("\nTool Result:")
print("=" * 80)
print(result)
print("=" * 80)

print(f"\n✓ Check output file: output/slack_parsed_test.txt")
print("\nThis file contains:")
print("  - ALL jobs from Slack messages where company name matches your list")
print("  - NO keyword filtering")
print("  - Format: company_name, job_title, job_id, job_url")

