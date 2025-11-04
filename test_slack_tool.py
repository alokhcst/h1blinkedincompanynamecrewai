#!/usr/bin/env python
"""Test the Slack Message Logger Tool"""
import os
from src.h1blinkedincompanynamecrewai.tools.slack_tool import SlackJobsTool

# Check for token
slack_token = os.environ.get("SLACK_BOT_TOKEN")
if not slack_token:
    print("❌ SLACK_BOT_TOKEN not set!")
    print("\nTo set it:")
    print("  PowerShell: $env:SLACK_BOT_TOKEN = 'xoxb-your-token'")
    print("  Bash: export SLACK_BOT_TOKEN='xoxb-your-token'")
    print("\nGet your token from: https://api.slack.com/apps")
    exit(1)

print(f"✓ SLACK_BOT_TOKEN is set: {slack_token[:15]}...")
print("\n" + "="*80)

# Create tool
tool = SlackJobsTool()

print("\nTesting SlackJobsTool - Message Logger...")
print(f"Channel: #h1bjobs")
print(f"Days back: 30")
print(f"Action: Read and log ALL messages")
print("\n" + "="*80 + "\n")

# Run the tool
result = tool._run(
    channel_name="h1bjobs",
    days_back=30,
    output_file_path="output/slack_messages_test.txt"
)

print("Tool Result (first 2000 chars):")
print(result[:2000])
if len(result) > 2000:
    print(f"\n... and {len(result) - 2000} more characters")

print("\n" + "="*80)
print(f"\nCheck output file:")
print("  - output/slack_messages_test.txt")
print("\nThis file contains ALL messages from the channel with:")
print("  - Message number")
print("  - Date and time")
print("  - User")
print("  - Full text")
print("  - Attachments (if any)")
print("  - Files (if any)")

