"""
Test script to verify SlackParserTool with detailed logging
"""
from src.h1blinkedincompanynamecrewai.tools.slack_parser_tool import SlackParserTool

print("=" * 80)
print("Testing SlackParserTool with detailed logging")
print("=" * 80)

print("\nCalling SlackParserTool...")
print("-" * 80)

tool = SlackParserTool()
result = tool._run(
    slack_json_path="output/slack_jobs_raw.json",
    companies_file_path="knowledge/H1BCompanyNameAtlanta.txt",
    output_file_path="output/slack_parsed_jobs_test.txt"
)

print("-" * 80)
print("\nTool Result:")
print(result)
print("\n" + "=" * 80)
print("Check the console output above for detailed logging")
print("=" * 80)

