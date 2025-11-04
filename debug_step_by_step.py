#!/usr/bin/env python
"""
Step-by-step debug script for LinkedIn Jobs Tool
Set breakpoints at any step to inspect variables
"""
import os
from datetime import datetime
from src.h1blinkedincompanynamecrewai.tools.custom_tool import LinkedInJobsTool

def main():
    # Step 1: Check environment
    print("=" * 80)
    print("STEP 1: Checking Environment")
    print("=" * 80)
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        print("❌ SERPER_API_KEY not set!")
        print("Set it with: $env:SERPER_API_KEY = 'your_key'")
        return
    else:
        print(f"✓ SERPER_API_KEY is set: {api_key[:10]}...")
    
    # Step 2: Initialize tool
    print("\n" + "=" * 80)
    print("STEP 2: Initializing Tool")
    print("=" * 80)
    tool = LinkedInJobsTool()
    print("✓ Tool initialized")
    
    # Step 3: Read companies
    print("\n" + "=" * 80)
    print("STEP 3: Reading Companies File")
    print("=" * 80)
    companies_file = "knowledge/H1BCompanyNameAtlanta.txt"
    companies = tool._read_linkedin_urls(companies_file)
    print(f"✓ Found {len(companies)} companies")
    for i, company in enumerate(companies[:5], 1):
        print(f"  {i}. {company}")
    if len(companies) > 5:
        print(f"  ... and {len(companies) - 5} more")
    
    # Step 4: Parse first company
    print("\n" + "=" * 80)
    print("STEP 4: Parsing First Company URL")
    print("=" * 80)
    if companies:
        first_url = companies[0]
        print(f"URL: {first_url}")
        company_info = tool._parse_linkedin_url(first_url)
        if company_info:
            print(f"✓ Parsed successfully:")
            print(f"  Name: {company_info.get('name')}")
            print(f"  Slug: {company_info.get('slug')}")
            print(f"  URL:  {company_info.get('url')}")
        else:
            print("❌ Could not parse URL")
    
    # Step 5: Build query
    print("\n" + "=" * 80)
    print("STEP 5: Building Search Query")
    print("=" * 80)
    if company_info:
        query = tool._build_company_jobs_query(
            company_info.get('name'), 
            company_info.get('slug')
        )
        print(f"Query: {query}")
    
    # Step 6: Test Serper search
    print("\n" + "=" * 80)
    print("STEP 6: Testing Serper Search (first 3 results)")
    print("=" * 80)
    results = tool._serper_search(api_key, query)
    print(f"✓ Got {len(results)} results")
    for i, item in enumerate(results[:3], 1):
        print(f"\n  Result {i}:")
        print(f"    Title: {item.get('title', 'N/A')[:60]}...")
        print(f"    Link:  {item.get('link', 'N/A')[:60]}...")
        print(f"    Snippet: {item.get('snippet', 'N/A')[:60]}...")
    
    # Step 7: Extract job URLs
    print("\n" + "=" * 80)
    print("STEP 7: Extracting Job URLs")
    print("=" * 80)
    job_urls = []
    for item in results:
        url = item.get("link", "")
        if url and "linkedin.com/jobs/view/" in url:
            job_id = tool._extract_job_id(url)
            if job_id:
                job_urls.append((job_id, url))
    print(f"✓ Found {len(job_urls)} job URLs")
    for i, (job_id, url) in enumerate(job_urls[:3], 1):
        print(f"  {i}. Job ID: {job_id} - {url[:60]}...")
    
    # Step 8: Test scraping first job
    print("\n" + "=" * 80)
    print("STEP 8: Scraping First Job Page")
    print("=" * 80)
    if job_urls:
        job_id, job_url = job_urls[0]
        print(f"Scraping: {job_url}")
        job_details = tool._scrape_job_page(api_key, job_url)
        if job_details:
            print("✓ Scraped successfully:")
            print(f"  Title: {job_details.get('title')}")
            print(f"  Posted: {job_details.get('posted_date')}")
            print(f"  Description: {job_details.get('description', '')[:100]}...")
        else:
            print("❌ Could not scrape job page")
    
    # Step 9: Test keyword matching
    print("\n" + "=" * 80)
    print("STEP 9: Testing Keyword Matching")
    print("=" * 80)
    keywords = ["Data Engineering", "Cloud", "AWS", "Azure", "Snowflake"]
    if job_details:
        title = job_details.get('title', '').lower()
        desc = job_details.get('description', '').lower()
        combined = f"{title} {desc}"
        
        matches = [kw for kw in keywords if kw.lower() in combined]
        if matches:
            print(f"✓ Job matches keywords: {', '.join(matches)}")
        else:
            print(f"❌ No keyword matches found")
            print(f"   Keywords tested: {', '.join(keywords)}")
    
    print("\n" + "=" * 80)
    print("DEBUG SESSION COMPLETE")
    print("=" * 80)
    print("\n💡 Tips:")
    print("  - Set breakpoints in VS Code at any step")
    print("  - Inspect variables in the Debug Console")
    print("  - Use F10 to step over, F11 to step into functions")
    print("  - Modify this script to test specific scenarios")

if __name__ == "__main__":
    main()

