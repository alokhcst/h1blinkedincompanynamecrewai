"""
Test script to verify SlackJobsTool logging works correctly
"""
import os
from src.h1blinkedincompanynamecrewai.tools.slack_tool import SlackJobsTool

print("=" * 80)
print("Testing SlackJobsTool with detailed logging")
print("=" * 80)

# Check environment variable
slack_token = os.environ.get("SLACK_BOT_TOKEN")
if slack_token:
    print(f"✓ SLACK_BOT_TOKEN is set (length: {len(slack_token)})")
else:
    print("✗ SLACK_BOT_TOKEN is NOT set")
    print("  Please set it: $env:SLACK_BOT_TOKEN = 'xoxb-your-token'")

print("\nCalling SlackJobsTool...")
print("-" * 80)

tool = SlackJobsTool()
result = tool._run(
    channel_name="h1bjobs",
    days_back=30,
    output_file_path="output/slack_jobs_test.txt"
)

print("-" * 80)
print("\nTool Result:")
print(result)
print("\n" + "=" * 80)
print("Check the console output above for detailed logging")
print("=" * 80)

