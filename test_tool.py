#!/usr/bin/env python
"""Test the LinkedInJobsTool directly"""
import os
from src.h1blinkedincompanynamecrewai.tools.custom_tool import LinkedInJobsTool
from dotenv import load_dotenv

load_dotenv()  

# Set your Serper API key
# os.environ["SERPER_API_KEY"] = "your_key_here"

# Create the tool
tool = LinkedInJobsTool()

# Test parameters
companies_file = "knowledge/H1BCompanyNameAtlanta.txt"
keywords = [
    "leadership", "Snowflake", "Azure Databricks", "Data Architecture", 
    "Data Engineering", "Data Engineering Leader", "AI Engineering Leader",
    "AWS Solutions Architect", "Azure Solutions Architect", "Data Science", 
    "DevOps", "Cloud Engineering"
]

print("Testing LinkedInJobsTool...")
print(f"Companies file: {companies_file}")
print(f"Keywords: {', '.join(keywords[:3])}... ({len(keywords)} total)")
print("\n" + "="*80 + "\n")

# Run the tool
result = tool._run(
    companies_file_path=companies_file,
    keywords=keywords,
    output_file_path="output/test_jobs.txt"
)

print("Tool Result:")
print(result)
print("\n" + "="*80)
print(f"\nCheck output files:")
print("- output/test_jobs.txt")
print("- output/linkedin_jobs.csv")
print("- output/linkedin_company_matches.txt")

