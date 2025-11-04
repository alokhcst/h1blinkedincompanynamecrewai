# %% [markdown]
# # LinkedIn Job Scraper for H1B Companies
# 
# This notebook demonstrates how to:
# 1. Read LinkedIn company URLs from a file
# 2. Parse company information
# 3. Use Serper API to search for job listings
# 4. Scrape individual job pages
# 5. Validate job freshness and relevance
# 6. Output results in plain text format
# 
# ## Setup Requirements
# - Python 3.10+
# - Serper API Key from https://serper.dev

# %% [markdown]
# ## 1. Install Dependencies & Import Libraries

# %%
# Install required packages (run once)
# !pip install requests python-dotenv pandas -q

# %%
import os
import csv
import re
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict

print("✓ Libraries imported successfully")

# %% [markdown]
# ## 2. Configuration & API Key Setup

# %%
# Set your Serper API key here
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

if not SERPER_API_KEY:
    print("⚠️  SERPER_API_KEY not set!")
    print("Set it in PowerShell: $env:SERPER_API_KEY = 'your_key'")
    print("Or uncomment and set it below:")
    # SERPER_API_KEY = "your_api_key_here"
else:
    print(f"✓ API Key set: {SERPER_API_KEY[:10]}...")

# Configuration
COMPANIES_FILE = "knowledge/H1BCompanyNameAtlanta.txt"
OUTPUT_CSV = "output/linkedin_jobs.csv"
OUTPUT_TXT = "output/linkedin_jobs.txt"
KEYWORDS = [
    "leadership", "Snowflake", "Azure Databricks", "Data Architecture",
    "Data Engineering", "Data Engineering Leader", "AI Engineering Leader",
    "AWS Solutions Architect", "Azure Solutions Architect", "Data Science",
    "DevOps", "Cloud Engineering"
]
DAYS_BACK = 30

print(f"\n✓ Configuration loaded")
print(f"  Companies file: {COMPANIES_FILE}")
print(f"  Keywords: {len(KEYWORDS)} keywords")
print(f"  Time window: Last {DAYS_BACK} days")

# %% [markdown]
# ## 3. Helper Functions

# %%
def read_linkedin_urls(file_path: str) -> List[str]:
    """Read LinkedIn URLs from file, one per line"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return []
    
    urls = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#') and 'linkedin.com' in url.lower():
                urls.append(url)
    
    # Deduplicate
    urls = list(dict.fromkeys(urls))
    return urls

def parse_linkedin_url(url: str) -> Optional[Dict]:
    """Parse LinkedIn URL to extract company info"""
    url_lower = url.lower()
    
    # Format: /company/slug/...
    if '/company/' in url_lower:
        try:
            after_company = url.split('/company/', 1)[1]
            slug = after_company.split('/')[0]
            name = slug.replace('-', ' ').title()
            return {'name': name, 'slug': slug, 'url': f"https://www.linkedin.com/company/{slug}/"}
        except:
            pass
    
    # Format: /jobs/company-name-jobs-location
    if '/jobs/' in url_lower:
        try:
            after_jobs = url.split('/jobs/', 1)[1]
            parts = after_jobs.split('-')
            if 'jobs' in parts:
                job_idx = parts.index('jobs')
                company_parts = parts[:job_idx]
                name = ' '.join(company_parts).title()
                slug = '-'.join(company_parts)
                return {'name': name, 'slug': slug, 'url': url}
        except:
            pass
    
    return None

def extract_job_id(url: str) -> Optional[str]:
    """Extract job ID from LinkedIn job URL"""
    try:
        if '/jobs/view/' in url:
            after_view = url.split('/jobs/view/', 1)[1]
            job_id = after_view.split('/')[0].split('?')[0]
            return job_id
    except:
        pass
    return None

print("✓ Helper functions defined")

# %% [markdown]
# ## 4. Serper API Functions

# %%
def serper_search(api_key: str, query: str, num_results: int = 50) -> List[Dict]:
    """Search using Serper API"""
    endpoint = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": num_results,
        "gl": "us",
        "hl": "en"
    }
    
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get('organic', [])
    except Exception as e:
        print(f"  ❌ Serper error: {e}")
        return []

def build_company_jobs_query(company_name: str, company_slug: Optional[str]) -> str:
    """Build search query for company jobs"""
    if company_slug:
        return f"linkedin.com {company_slug} jobs"
    return f"linkedin.com {company_name} jobs"

print("✓ Serper API functions defined")

# %% [markdown]
# ## 5. Job Validation Functions

# %%
def extract_posted_date(snippet: str) -> Optional[str]:
    """Extract posted date from job snippet"""
    snippet_lower = snippet.lower()
    
    patterns = [
        (r'(\d+)\s+days?\s+ago', lambda m: f"{m.group(1)} days ago"),
        (r'(\d+)\s+weeks?\s+ago', lambda m: f"{m.group(1)} weeks ago"),
        (r'(\d+)\s+hours?\s+ago', lambda m: f"{m.group(1)} hours ago"),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, snippet_lower)
        if match:
            return formatter(match)
    
    return None

def is_job_fresh(posted_date_str: Optional[str], days_back: int = 30) -> bool:
    """Check if job is fresh (within days_back)"""
    if not posted_date_str:
        return True  # Assume fresh if unknown
    
    try:
        posted_lower = posted_date_str.lower()
        
        if 'hour' in posted_lower:
            return True
        
        if 'day' in posted_lower:
            match = re.search(r'(\d+)\s+days?', posted_lower)
            if match:
                days = int(match.group(1))
                return days <= days_back
        
        if 'week' in posted_lower:
            match = re.search(r'(\d+)\s+weeks?', posted_lower)
            if match:
                weeks = int(match.group(1))
                days = weeks * 7
                return days <= days_back
        
        if 'month' in posted_lower:
            return False
        
        return True
    except:
        return True

def is_job_relevant(title: str, description: str, keywords: List[str]) -> bool:
    """Check if job matches any keywords"""
    combined = f"{title} {description}".lower()
    return any(kw.lower() in combined for kw in keywords)

print("✓ Validation functions defined")

# %% [markdown]
# ## 6. Load and Preview Companies

# %%
# Read companies from file
companies = read_linkedin_urls(COMPANIES_FILE)

print(f"✓ Loaded {len(companies)} companies\n")
print("First 10 companies:")
for i, url in enumerate(companies[:10], 1):
    info = parse_linkedin_url(url)
    if info:
        print(f"  {i:2d}. {info['name']:30s} - {info['slug']}")
    else:
        print(f"  {i:2d}. Could not parse: {url[:50]}")

if len(companies) > 10:
    print(f"\n  ... and {len(companies) - 10} more")

# %% [markdown]
# ## 7. Test Single Company (Detailed)

# %%
# Test with first company
if companies:
    test_url = companies[0]
    print(f"Testing with: {test_url}\n")
    print("=" * 80)
    
    # Parse company
    company_info = parse_linkedin_url(test_url)
    if company_info:
        print(f"Company: {company_info['name']}")
        print(f"Slug: {company_info['slug']}")
        print(f"URL: {company_info['url']}")
        
        # Build query
        query = build_company_jobs_query(company_info['name'], company_info['slug'])
        print(f"\nSearch Query: {query}")
        
        # Search
        print(f"\nSearching with Serper...")
        results = serper_search(SERPER_API_KEY, query, num_results=10)
        print(f"✓ Got {len(results)} results\n")
        
        # Display results
        job_count = 0
        for i, item in enumerate(results[:5], 1):
            url = item.get('link', '')
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            
            is_job = 'linkedin.com/jobs/view/' in url
            job_id = extract_job_id(url) if is_job else None
            posted = extract_posted_date(snippet)
            fresh = is_job_fresh(posted, DAYS_BACK)
            relevant = is_job_relevant(title, snippet, KEYWORDS)
            
            print(f"Result {i}:")
            print(f"  Title: {title[:60]}")
            print(f"  URL: {url[:60]}")
            print(f"  Job ID: {job_id if job_id else 'N/A'}")
            print(f"  Posted: {posted if posted else 'Unknown'}")
            print(f"  Fresh: {'✓' if fresh else '✗'}")
            print(f"  Relevant: {'✓' if relevant else '✗'}")
            print()
            
            if is_job and fresh and relevant:
                job_count += 1
        
        print(f"\n✓ Found {job_count} valid jobs from first 5 results")
    else:
        print("❌ Could not parse company URL")
else:
    print("❌ No companies loaded")

# %% [markdown]
# ## 8. Process All Companies

# %%
# Process all companies
all_jobs = []
processed_job_ids = set()

print(f"Processing {len(companies)} companies...\n")
print("=" * 80)

for idx, company_url in enumerate(companies, 1):
    print(f"\n[{idx}/{len(companies)}] Processing: {company_url[:60]}...")
    
    # Parse company
    company_info = parse_linkedin_url(company_url)
    if not company_info:
        print("  ⚠️  Could not parse URL, skipping")
        continue
    
    company_name = company_info['name']
    print(f"  Company: {company_name}")
    
    # Build query and search
    query = build_company_jobs_query(company_name, company_info['slug'])
    results = serper_search(SERPER_API_KEY, query, num_results=50)
    print(f"  Found {len(results)} search results")
    
    # Extract job URLs
    job_urls = []
    for item in results:
        url = item.get('link', '')
        if url and 'linkedin.com/jobs/view/' in url:
            job_id = extract_job_id(url)
            if job_id and job_id not in processed_job_ids:
                job_urls.append((job_id, url, item))
    
    print(f"  Checking {len(job_urls)} unique job URLs")
    
    # Validate each job
    valid_jobs = 0
    for job_id, job_url, item in job_urls:
        title = item.get('title', '')
        snippet = item.get('snippet', '')
        
        # Check freshness
        posted = extract_posted_date(snippet)
        if not is_job_fresh(posted, DAYS_BACK):
            continue
        
        # Check relevance
        if not is_job_relevant(title, snippet, KEYWORDS):
            continue
        
        # Valid job!
        role = title.replace(' | LinkedIn', '').replace(' - LinkedIn', '')
        all_jobs.append({
            'timestamp': datetime.utcnow().isoformat(),
            'company': company_name,
            'job_id': job_id,
            'role': role,
            'url': job_url,
            'posted': posted or 'Unknown'
        })
        processed_job_ids.add(job_id)
        valid_jobs += 1
    
    print(f"  ✓ Found {valid_jobs} relevant jobs")
    
    # Rate limiting - be nice to the API
    if idx < len(companies):
        import time
        time.sleep(0.5)

print("\n" + "=" * 80)
print(f"\n✓ Processing complete!")
print(f"  Total jobs found: {len(all_jobs)}")
print(f"  Unique job IDs: {len(processed_job_ids)}")

# %% [markdown]
# ## 9. View Results

# %%
# Display results as DataFrame
if all_jobs:
    df = pd.DataFrame(all_jobs)
    print(f"Total jobs found: {len(df)}\n")
    print(df[['company', 'job_id', 'role', 'posted']].head(20))
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"  Companies with jobs: {df['company'].nunique()}")
    print(f"  Total jobs: {len(df)}")
    print("\nTop companies by job count:")
    print(df['company'].value_counts().head(10))
else:
    print("No jobs found")

# %% [markdown]
# ## 10. Save Results

# %%
if all_jobs:
    # Save to CSV
    os.makedirs('output', exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✓ Saved to CSV: {OUTPUT_CSV}")
    
    # Save to plain text
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        for job in all_jobs:
            line = f"{job['company']}, {job['job_id']}, {job['role']}, {job['url']}\n"
            f.write(line)
    print(f"✓ Saved to TXT: {OUTPUT_TXT}")
    
    print("\n✓ All results saved!")
else:
    print("No results to save")

# %% [markdown]
# ## 11. Export for Analysis

# %%
# Export summary
if all_jobs:
    summary = {
        'total_jobs': len(all_jobs),
        'companies_processed': len(companies),
        'companies_with_jobs': df['company'].nunique(),
        'keywords_used': KEYWORDS,
        'days_back': DAYS_BACK,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print("Summary:")
    print(json.dumps(summary, indent=2))
    
    # Save summary
    with open('output/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("\n✓ Summary saved to output/summary.json")

