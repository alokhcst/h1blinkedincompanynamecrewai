from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field
import os
import csv
import json
import re
from datetime import datetime, timedelta
import requests
import logging
from dotenv import load_dotenv

load_dotenv()   
# Minimal, safe logging setup if none configured by the host app.
# Avoids dependency on an external logging.conf file.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


# This module defines a custom tool for CrewAI that:
# 1) Reads a list of LinkedIn URLs from a file (one per line) - supports both /jobs/ and /company/ formats
# 2) Parses each URL to extract company name and slug
# 3) Optionally scrapes LinkedIn company pages to get official display names
# 4) Fetches recent news for each company via Serper News API
# 5) Searches for recent (last 7 days) LinkedIn job postings matching provided keywords
# 6) Deduplicates results across runs based on URL (via a CSV ledger)
# 7) Appends a plaintext, human-friendly summary to a .txt file
# 8) Writes a mapping file from input URL to LinkedIn company name and URL
#
# Environment requirement: set SERPER_API_KEY to a valid Serper API key


class LinkedInJobsToolInput(BaseModel):
    """Input schema for LinkedInJobsTool."""
    # Path to the companies source file (one LinkedIn URL per line)
    companies_file_path: str = Field(..., description="Path to a plaintext file with one LinkedIn URL per line (jobs or company URLs).")
    # List of job keyword phrases (can also be passed as a comma-separated string)
    keywords: List[str] = Field(..., description="List of job keywords to search for.")
    # Text file path where human-readable lines are appended each run
    output_file_path: Optional[str] = Field(
        default="knowledge/linkedin_jobs.txt",
        description="Plaintext path to append new results each run. CSV for dedupe is managed separately."
    )
    # Text file path where we store mapping from input company to LinkedIn company
    company_map_output_path: Optional[str] = Field(
        default="knowledge/linkedin_company_matches.txt",
        description="Plaintext path to write mapping: input_url, linkedin_company_name, linkedin_company_url"
    )


class LinkedInJobsTool(BaseTool):
    name: str = "LinkedInJobsTool"
    description: str = (
        "Reads a list of LinkedIn URLs from a file (jobs or company pages), extracts company information, searches recent (last 7 days) "
        "LinkedIn job listings using Serper (Google Search) API, filters by provided keywords, deduplicates across runs "
        "(CSV), appends plaintext output to a file, and returns lines: 'companyname, job role, job url'. Requires env var SERPER_API_KEY."
    )
    args_schema: Type[BaseModel] = LinkedInJobsToolInput

    def _run(self, companies_file_path: str, keywords: List[str], output_file_path: Optional[str] = None, company_map_output_path: Optional[str] = None) -> str:
        """Entrypoint executed by CrewAI.
        - Validates API key
        - Reads LinkedIn URLs
        - Iterates through each company's LinkedIn page
        - Uses Serper to browse and find all job URLs
        - Filters jobs from last 30 days
        - Validates job relevance against keywords (checks title and snippet)
        - Returns plaintext: company_name, job_id, job_role, job_url
        """
        # Ensure Serper API key is present
        api_key = os.environ.get("SERPER_API_KEY")
        if not api_key:
            return "ERROR: Missing SERPER_API_KEY environment variable."

        # Paths for outputs: CSV ledger for dedupe, TXT for printable output
        csv_path = "output/linkedin_jobs.csv"
        text_path = output_file_path or "output/linkedin_jobs.txt"
        map_path = company_map_output_path or "output/linkedin_company_matches.txt"

        # Read LinkedIn URLs from file
        linkedin_urls = self._read_linkedin_urls(companies_file_path)
        if not linkedin_urls:
            return f"ERROR: No LinkedIn URLs found in {companies_file_path}. Ensure one URL per line."

        # Normalize keywords to a list even if provided as comma-separated string
        if isinstance(keywords, str):
            keywords_list: List[str] = [k.strip() for k in keywords.split(",") if k.strip()]
        else:
            keywords_list = keywords

        # Convert keywords to lowercase for case-insensitive matching
        keywords_lower = [k.lower() for k in keywords_list]

        # Previous run job IDs to avoid duplicates on re-runs
        existing_job_ids = self._load_existing_job_ids(csv_path)
        # 30-day cutoff
        fresh_cutoff = datetime.utcnow() - timedelta(days=30)

        # Accumulators for newly found CSV rows and human-readable lines
        new_rows: List[List[str]] = []
        plaintext_lines: List[str] = []
        company_map_lines: List[str] = []

        # Iterate through each LinkedIn URL
        for url_entry in linkedin_urls:
            # Parse the LinkedIn URL to extract company information
            company_info = self._parse_linkedin_url(url_entry)
            if not company_info:
                logger.warning(f"Could not parse LinkedIn URL: {url_entry}")
                continue
            
            company_name = company_info.get("name") or "Unknown"
            company_slug = company_info.get("slug")
            company_url = company_info.get("url") or url_entry
            
            logger.info(f"Processing: {company_name} from {url_entry}")
            plaintext_lines.append(f"\n=== Company: {company_name} ===")
            
            # Collect mapping output
            company_map_lines.append(f"{url_entry}, {company_name}, {company_url}")

            # Step 1: Use Serper to scrape the company's LinkedIn jobs page
            jobs_query = self._build_company_jobs_query(company_name, company_slug)
            logger.info(f"Step 1: Scraping jobs page with query: {jobs_query}")
            
            job_results = self._serper_search(api_key, jobs_query)
            logger.info(f"Found {len(job_results)} job listings on the company page")
            
            jobs_found = 0
            jobs_checked = 0
            
            # Step 2: Extract all job URLs from the scraped page
            job_urls_to_check = []
            for item in job_results:
                job_url = item.get("link") or ""
                if job_url and "linkedin.com/jobs/view/" in job_url:
                    job_id = self._extract_job_id(job_url)
                    if job_id and job_id not in existing_job_ids:
                        job_urls_to_check.append(job_url)
            
            logger.info(f"Step 2: Found {len(job_urls_to_check)} unique job URLs to check")
            
            # Step 3: Visit each job URL to validate freshness and relevance
            for job_url in job_urls_to_check:
                jobs_checked += 1
                job_id = self._extract_job_id(job_url)
                
                logger.debug(f"Checking job {jobs_checked}/{len(job_urls_to_check)}: {job_id}")
                
                # Scrape the individual job page using Serper
                job_details = self._scrape_job_page(api_key, job_url)
                
                if not job_details:
                    logger.debug(f"Could not scrape job page: {job_id}")
                    continue
                
                # Step 4: Validate if job is active in last 30 days
                posted_date = job_details.get("posted_date")
                is_fresh = self._is_job_fresh(posted_date, fresh_cutoff)
                
                if not is_fresh:
                    logger.debug(f"Job too old or not fresh: {job_id}")
                    continue
                
                # Step 5: Validate relevance based on keywords
                job_title = job_details.get("title") or ""
                job_description = job_details.get("description") or ""
                
                title_lower = job_title.lower()
                desc_lower = job_description.lower()
                combined_text = f"{title_lower} {desc_lower}"
                
                is_relevant = any(kw in combined_text for kw in keywords_lower)
                
                if not is_relevant:
                    logger.debug(f"Job not relevant: {job_title}")
                    continue
                
                # Extract clean job role
                job_role = self._extract_role(job_title)
                
                # Job passed all validations!
                logger.info(f"✓ Valid job found: {job_role}")
                
                # Persist for dedupe going forward
                new_rows.append([
                    datetime.utcnow().isoformat(),
                    company_name,
                    job_id,
                    job_role,
                    job_url,
                ])
                
                # Output: company_name, job_id, job_role, job_url
                plaintext_lines.append(f"{company_name}, {job_id}, {job_role}, {job_url}")
                existing_job_ids.add(job_id)
                jobs_found += 1

            logger.info(f"Checked {jobs_checked} jobs, found {jobs_found} relevant jobs for {company_name}")
            
            if jobs_found == 0:
                plaintext_lines.append(f"No relevant jobs found in the last 30 days")
            else:
                logger.info(f"✓ Found {jobs_found} relevant jobs for {company_name}")

        # Persist outputs: CSV (for job IDs), TXT (human-readable job lines), company mapping
        if new_rows:
            self._append_rows(csv_path, new_rows)
            self._write_text_lines(text_path, plaintext_lines)
            logger.info(f"Saved {len(new_rows)} jobs to {csv_path}")
        else:
            logger.info("No new jobs found")
            
        if company_map_lines:
            self._write_text_lines(map_path, company_map_lines)
            logger.info(f"Saved {len(company_map_lines)} company mappings to {map_path}")

        # Always return plaintext_lines if we have them (even if no new jobs)
        if plaintext_lines:
            result = "\n".join(plaintext_lines)
            logger.info(f"Returning {len(plaintext_lines)} lines of output")
            return result
        
        # Fallback message
        return f"Processed {len(linkedin_urls)} companies. No new relevant job postings found in the last 7 days matching the provided keywords."

    def _read_linkedin_urls(self, path: str) -> List[str]:
        """Load LinkedIn URLs from a plaintext file, skipping blank lines and comments."""
        if not os.path.exists(path):
            return []
        urls: List[str] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if not url or url.startswith("#"):
                    continue
                # Only accept linkedin.com URLs
                if "linkedin.com" not in url.lower():
                    continue
                urls.append(url)
        # De-duplicate while preserving order
        seen = set()
        deduped: List[str] = []
        for u in urls:
            if u.lower() in seen:
                continue
            seen.add(u.lower())
            deduped.append(u)
        return deduped

    def _parse_linkedin_url(self, url: str) -> Optional[dict]:
        """Parse a LinkedIn URL to extract company name and slug.
        
        Handles formats:
        - https://www.linkedin.com/jobs/company-name-jobs-location
        - https://www.linkedin.com/company/company-slug/jobs/
        """
        url_lower = url.lower()
        
        # Format: /company/slug/...
        if "/company/" in url_lower:
            try:
                after_company = url.split("/company/", 1)[1]
                slug = after_company.split("/")[0]
                # Try to scrape the company page for the display name
                company_page_url = f"https://www.linkedin.com/company/{slug}/"
                scraped_name = self._scrape_linkedin_company_name(company_page_url)
                if scraped_name:
                    return {"name": scraped_name, "slug": slug, "url": company_page_url}
                # Fallback: convert slug to title case
                name = slug.replace("-", " ").title()
                return {"name": name, "slug": slug, "url": company_page_url}
            except Exception:
                pass
        
        # Format: /jobs/company-name-jobs-location
        if "/jobs/" in url_lower:
            try:
                after_jobs = url.split("/jobs/", 1)[1]
                parts = after_jobs.split("-")
                # Extract company name by removing "-jobs" and location suffixes
                if "jobs" in parts:
                    job_idx = parts.index("jobs")
                    company_parts = parts[:job_idx]
                    name = " ".join(company_parts).title()
                    # Use the company name as slug (normalized)
                    slug = "-".join(company_parts)
                    return {"name": name, "slug": slug, "url": url}
            except Exception:
                pass
        
        return None

    def _build_job_query(self, company_name: str, company_slug: Optional[str], keywords: List[str]) -> str:
        """Create a Serper/Google query that targets LinkedIn jobs for a specific company and keywords."""
        keyword_clause = " OR ".join([f'"{k}"' for k in keywords])
        slug_clause = f' OR "company/{company_slug}"' if company_slug else ""
        query = f"site:linkedin.com/jobs \"{company_name}\"{slug_clause} ({keyword_clause})"
        return query

    def _build_company_jobs_query(self, company_name: str, company_slug: Optional[str]) -> str:
        """Create a Serper/Google query to find ALL jobs for a specific company on LinkedIn."""
        if company_slug:
            # Search for LinkedIn jobs with company slug
            query = f"linkedin.com {company_slug} jobs"
        else:
            # Search for LinkedIn jobs with company name
            query = f"linkedin.com {company_name} jobs"
        return query

    def _serper_search(self, api_key: str, query: str) -> List[dict]:
        """Call Serper Search API for a given query and return organic results list."""
        endpoint = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": 50,  # Serper max is typically 50-100, use 50 to be safe
            "gl": "us",
            "hl": "en",
        }
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("organic", [])
            logger.info(f"Serper returned {len(results)} results for query: {query[:100]}")
            return results
        except requests.exceptions.HTTPError as e:
            logger.error(f"Serper HTTP error: {e}")
            try:
                logger.error(f"Response body: {resp.text}")
                logger.error(f"Query that failed: {query}")
                logger.error(f"Payload: {payload}")
            except:
                pass
            return []
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return []

    def _serper_news_search(self, api_key: str, company: str) -> List[dict]:
        """Fetch recent news for a company via Serper News API."""
        endpoint = "https://google.serper.dev/news"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": company,
            "gl": "us",
            "hl": "en",
            "num": 5,
        }
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("news", [])
            return articles
        except Exception:
            return []

    def _serper_is_fresh(self, item: dict, cutoff: datetime) -> bool:
        """Validate that a Serper result appears to be recent; fallback to allowing if unknown."""
        # Serper organic results may include a date for some items; otherwise rely on tbs filter
        date_str = item.get("date")
        if not date_str:
            return True
        try:
            # Attempt common formats
            try:
                parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                parsed = cutoff  # fallback to accept due to tbs filter
            return parsed >= cutoff
        except Exception:
            return True

    def _extract_role(self, title: str) -> str:
        """Derive a concise role from a search result title (removes standard LinkedIn suffixes)."""
        if not title:
            return "Job Posting"
        # Titles often include " - LinkedIn" suffix; strip it
        cleaned = title.replace(" | LinkedIn", "").replace(" - LinkedIn", "")
        return cleaned

    def _extract_job_id(self, url: str) -> Optional[str]:
        """Extract LinkedIn job ID from a job URL.
        Example: https://www.linkedin.com/jobs/view/1234567890 -> 1234567890
        """
        try:
            if "/jobs/view/" in url:
                after_view = url.split("/jobs/view/", 1)[1]
                job_id = after_view.split("/")[0].split("?")[0]
                return job_id
            return None
        except Exception:
            return None

    def _scrape_job_page(self, api_key: str, job_url: str) -> Optional[dict]:
        """Scrape an individual LinkedIn job page using Serper to get title, description, and posted date.
        
        Returns dict with:
        - title: Job title
        - description: Job description snippet
        - posted_date: String like "2 days ago", "1 week ago", etc.
        """
        try:
            # Use Serper to search for this specific job URL
            query = f"{job_url}"
            results = self._serper_search(api_key, query)
            
            if not results:
                return None
            
            # Get the first result (should be the job page itself)
            for item in results:
                if job_url in (item.get("link") or ""):
                    title = item.get("title") or ""
                    snippet = item.get("snippet") or ""
                    
                    # Try to extract posted date from snippet
                    # LinkedIn snippets often contain "Posted X days ago" or similar
                    posted_date = self._extract_posted_date_from_snippet(snippet)
                    
                    return {
                        "title": self._extract_role(title),
                        "description": snippet,
                        "posted_date": posted_date
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error scraping job page {job_url}: {e}")
            return None

    def _extract_posted_date_from_snippet(self, snippet: str) -> Optional[str]:
        """Extract posted date string from job snippet.
        Examples: "2 days ago", "1 week ago", "3 weeks ago"
        """
        snippet_lower = snippet.lower()
        
        # Common patterns
        patterns = [
            "posted ",
            " ago",
            "reposted ",
        ]
        
        for pattern in patterns:
            if pattern in snippet_lower:
                # Try to extract the time phrase
                if "day" in snippet_lower:
                    match = re.search(r'(\d+)\s+days?\s+ago', snippet_lower)
                    if match:
                        return f"{match.group(1)} days ago"
                if "week" in snippet_lower:
                    match = re.search(r'(\d+)\s+weeks?\s+ago', snippet_lower)
                    if match:
                        return f"{match.group(1)} weeks ago"
                if "hour" in snippet_lower:
                    match = re.search(r'(\d+)\s+hours?\s+ago', snippet_lower)
                    if match:
                        return f"{match.group(1)} hours ago"
        
        return None

    def _is_job_fresh(self, posted_date_str: Optional[str], cutoff: datetime) -> bool:
        """Validate if a job is fresh (posted within last 30 days).
        
        Args:
            posted_date_str: String like "2 days ago", "3 weeks ago"
            cutoff: Datetime cutoff (30 days ago)
        """
        if not posted_date_str:
            # If we can't determine, assume it's fresh (will be caught by Serper's tbs filter)
            return True
        
        try:
            posted_lower = posted_date_str.lower()
            
            # Extract number and unit
            if "hour" in posted_lower:
                match = re.search(r'(\d+)\s+hours?', posted_lower)
                if match:
                    hours = int(match.group(1))
                    posted_date = datetime.utcnow() - timedelta(hours=hours)
                    return posted_date >= cutoff
            
            if "day" in posted_lower:
                match = re.search(r'(\d+)\s+days?', posted_lower)
                if match:
                    days = int(match.group(1))
                    if days <= 30:
                        return True
                    return False
            
            if "week" in posted_lower:
                match = re.search(r'(\d+)\s+weeks?', posted_lower)
                if match:
                    weeks = int(match.group(1))
                    days = weeks * 7
                    if days <= 30:
                        return True
                    return False
            
            if "month" in posted_lower:
                # If it's more than 1 month, it's too old
                return False
            
            # Default: assume fresh if we can't parse
            return True
            
        except Exception:
            return True

    def _load_existing_urls(self, csv_path: str) -> set:
        """Load previously saved job URLs from CSV for deduplication across runs."""
        urls = set()
        if not os.path.exists(csv_path):
            return urls
        try:
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("url")
                    if url:
                        urls.add(url)
        except Exception:
            pass
        return urls

    def _load_existing_job_ids(self, csv_path: str) -> set:
        """Load previously saved job IDs from CSV for deduplication across runs."""
        job_ids = set()
        if not os.path.exists(csv_path):
            return job_ids
        try:
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    job_id = row.get("job_id")
                    if job_id:
                        job_ids.add(job_id)
        except Exception:
            pass
        return job_ids

    def _append_rows(self, csv_path: str, rows: List[List[str]]) -> None:
        """Append rows to the CSV ledger, creating it with headers if needed."""
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        file_exists = os.path.exists(csv_path)
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp_utc", "company", "job_id", "role", "url"])
            for r in rows:
                writer.writerow(r)

    def _append_text_lines(self, text_path: str, lines: List[str]) -> None:
        """Append human-readable lines to a text file, creating parent directories if needed."""
        if not lines:
            return
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

    def _write_text_lines(self, text_path: str, lines: List[str]) -> None:
        """Overwrite a text file with a list of lines (used for company mapping output)."""
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

    def _resolve_linkedin_company(self, api_key: str, company: str) -> Optional[dict]:
        """Resolve the official LinkedIn company page for a given company name using scoring.

        Strategy:
        - Run multiple Serper queries (quoted and unquoted) restricted to linkedin.com/company
        - Collect candidates with /company/ in URL, extract slug and title
        - Score candidates by normalized string similarity against the input company
        - Prefer higher similarity, shorter slugs, and presence of 'LinkedIn' suffix in title
        - Optionally scrape page to refine display name
        """
        queries = [
            f"site:linkedin.com/company \"{company}\"",
            f"site:linkedin.com/company {company}",
        ]

        candidates: List[dict] = []
        for q in queries:
            for item in self._serper_search(api_key, q):
                link = item.get("link") or ""
                title = item.get("title") or ""
                if "linkedin.com/company/" not in link:
                    continue
                # Exclude non-company patterns (safety)
                if any(x in link for x in ["/company-beta/", "/learning/", "/school/"]):
                    continue
                slug = None
                try:
                    after = link.split("/company/", 1)[1]
                    slug = after.split("/", 1)[0]
                except Exception:
                    slug = None
                candidates.append({
                    "link": link,
                    "title": title,
                    "slug": slug,
                })

        if not candidates:
            return None

        # Rank candidates
        normalized_target = self._normalize_company_name(company)
        def score_candidate(c: dict) -> float:
            title_clean = (c.get("title") or "").replace(" | LinkedIn", "").replace(" - LinkedIn", "")
            norm_title = self._normalize_company_name(title_clean)
            slug = (c.get("slug") or "").lower()
            # Base similarity from title
            sim_title = self._similarity(normalized_target, norm_title)
            # Bonus if slug resembles the target (handles vanity URLs)
            sim_slug = self._similarity(normalized_target, slug)
            # Penalize very long slugs (likely departments, regions)
            length_penalty = min(len(slug), 40) / 40.0
            # Combine
            return sim_title * 0.7 + sim_slug * 0.3 - 0.15 * length_penalty

        best = max(candidates, key=score_candidate)

        link = best.get("link") or ""
        title = (best.get("title") or "").replace(" | LinkedIn", "").replace(" - LinkedIn", "")
        slug = best.get("slug")

        # Try scraping page for a robust display name; fallback to cleaned title
        scraped_name = self._scrape_linkedin_company_name(link)
        display_name = scraped_name or title or company

        return {"name": display_name, "url": link, "slug": slug}

    def _scrape_linkedin_company_name(self, url: str) -> Optional[str]:
        """Fetch a LinkedIn company page and parse a display name from HTML (og:title or <title>)."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code >= 400:
                return None
            html = resp.text or ""
            og_marker = 'property="og:title"'
            idx = html.find(og_marker)
            if idx != -1:
                content_idx = html.find('content="', idx)
                if content_idx != -1:
                    start = content_idx + len('content="')
                    end = html.find('"', start)
                    if end != -1:
                        name = html[start:end]
                        if name:
                            return name
            t_start = html.lower().find("<title>")
            t_end = html.lower().find("</title>")
            if t_start != -1 and t_end != -1 and t_end > t_start:
                raw = html[t_start + 7:t_end].strip()
                if raw:
                    return raw.replace(" | LinkedIn", "").replace(" - LinkedIn", "")
            return None
        except Exception:
            return None

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company names for fuzzy matching (lowercase, remove punctuation and suffixes)."""
        s = (name or "").lower()
        # Remove punctuation
        for ch in [",", ".", "&", "(", ")", "'", "\"", "-"]:
            s = s.replace(ch, " ")
        # Collapse whitespace
        s = " ".join(s.split())
        # Remove common corporate suffixes
        suffixes = [
            " inc", " llc", " ltd", " limited", " corp", " corporation", " co", " company",
            " plc", " lp", " gmbh", " ag", " srl", " bv", " nv", " pvt", " llp", " pllc",
        ]
        for suf in suffixes:
            if s.endswith(suf):
                s = s[: -len(suf)]
        return s.strip()

    def _similarity(self, a: str, b: str) -> float:
        """Compute a simple token-based similarity between two strings (Jaccard over tokens)."""
        if not a or not b:
            return 0.0
        ta = set(a.split())
        tb = set(b.split())
        inter = len(ta & tb)
        union = len(ta | tb) or 1
        return inter / union
