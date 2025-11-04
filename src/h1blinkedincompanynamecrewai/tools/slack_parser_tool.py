from crewai.tools import BaseTool
from typing import Type, List, Optional, Dict
from pydantic import BaseModel, Field
import os
import json
import re
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackParserToolInput(BaseModel):
    """Input schema for SlackParserTool."""
    slack_json_path: str = Field(
        default="output/slack_jobs_raw.json",
        description="Path to the Slack messages raw JSON file"
    )
    companies_file_path: str = Field(
        default="knowledge/H1BCompanyNameAtlanta.txt",
        description="Path to file with company names (one per line)"
    )
    output_file_path: Optional[str] = Field(
        default="output/slack_parsed_jobs.txt",
        description="Output file for parsed jobs"
    )


class SlackParserTool(BaseTool):
    name: str = "SlackParserTool"
    description: str = (
        "Reads Slack messages from a JSON file, matches company names from a list, "
        "extracts job details (company, title, ID, URL), and outputs in plain text format. "
        "Returns ALL jobs where company names match, without keyword filtering."
    )
    args_schema: Type[BaseModel] = SlackParserToolInput

    def _run(
        self,
        slack_json_path: str = "output/slack_jobs_raw.json",
        companies_file_path: str = "knowledge/H1BCompanyNameAtlanta.txt",
        output_file_path: Optional[str] = None
    ) -> str:
        """
        Parse Slack messages, match companies, and extract ALL job details.
        
        Returns:
            Plain text: company_name, job_title, job_id, job_url
        """
        logger.info("=" * 80)
        logger.info("SlackParserTool._run() CALLED")
        logger.info("=" * 80)
        logger.info(f"Parameters:")
        logger.info(f"  - slack_json_path: {slack_json_path}")
        logger.info(f"  - companies_file_path: {companies_file_path}")
        logger.info(f"  - output_file_path: {output_file_path}")
        
        # Step 1: Load Slack messages from JSON
        logger.info(f"STEP 1: Loading Slack messages from JSON")
        messages = self._load_slack_json(slack_json_path)
        if not messages:
            # Check if file exists
            if not os.path.exists(slack_json_path):
                logger.error(f"✗ JSON file not found at {slack_json_path}")
                return f"ERROR: JSON file not found at {slack_json_path}. Make sure slack_jobs_task runs first and creates the file."
            # File exists but is empty or invalid
            logger.error(f"✗ Could not load messages from {slack_json_path}")
            return f"ERROR: Could not load messages from {slack_json_path}. File may be empty or invalid JSON. Check if slack_jobs_task completed successfully."
        
        logger.info(f"✓ Loaded {len(messages)} messages from JSON")
        
        # Step 2: Load company names
        logger.info(f"STEP 2: Loading company names from file")
        companies = self._load_companies(companies_file_path)
        if not companies:
            logger.error(f"✗ Could not load companies from {companies_file_path}")
            return f"ERROR: Could not load companies from {companies_file_path}"
        
        logger.info(f"✓ Loaded {len(companies)} companies")
        logger.info(f"Companies: {companies[:5]}..." if len(companies) > 5 else f"Companies: {companies}")
        logger.info(f"No keyword filtering - returning ALL jobs for matched companies")
        
        # Step 3: Process messages and extract matching jobs
        logger.info(f"STEP 3: Processing messages to extract jobs")
        matched_jobs = []
        processed_job_ids = set()
        
        for idx, msg in enumerate(messages, 1):
            logger.debug(f"Processing message {idx}/{len(messages)}")
            
            # IMPORTANT: Process each attachment separately to handle multi-company messages
            # A single Slack message can have multiple attachments from different companies
            attachments = msg.get('attachments', [])
            
            if attachments:
                logger.debug(f"  Message {idx}: Processing {len(attachments)} attachment(s)")
                
                # Process each attachment individually
                for att_idx, attachment in enumerate(attachments, 1):
                    # Extract text from this specific attachment
                    att_text = self._extract_attachment_text(attachment)
                    
                    if not att_text:
                        logger.debug(f"    Attachment {att_idx}: No text found")
                        continue
                    
                    # Find company match for THIS attachment
                    mentioned_company = self._find_matching_company(att_text, companies)
                    
                    if not mentioned_company:
                        logger.debug(f"    Attachment {att_idx}: No company match")
                        continue
                    
                    logger.info(f"    Attachment {att_idx}: Found company: {mentioned_company}")
                    
                    # Extract LinkedIn job URLs from THIS attachment
                    job_urls = self._extract_linkedin_job_urls_from_text(att_text)
                    
                    if not job_urls:
                        logger.debug(f"    Attachment {att_idx}: No LinkedIn job URLs found")
                        continue
                    
                    logger.info(f"    Attachment {att_idx}: Found {len(job_urls)} job URL(s)")
                    
                    # Process each job URL in this attachment
                    for job_id, job_url in job_urls:
                        # Skip duplicates
                        if job_id in processed_job_ids:
                            logger.debug(f"      Skipping duplicate job ID: {job_id}")
                            continue
                        
                        # Extract job title from attachment text
                        job_title = self._extract_job_title_from_text(att_text, job_url)
                        
                        # Add to results
                        matched_jobs.append({
                            'company': mentioned_company,
                            'job_title': job_title,
                            'job_id': job_id,
                            'job_url': job_url
                        })
                        processed_job_ids.add(job_id)
                        logger.info(f"      ✓ Matched job: {mentioned_company} - {job_title} ({job_id})")
            else:
                # Fallback: Process message-level content (for messages without attachments)
                full_text = self._extract_full_message_text(msg)
                
                if idx <= 3:
                    logger.debug(f"  Message {idx} text preview: {full_text[:200]}...")
                
                mentioned_company = self._find_matching_company(full_text, companies)
                
                if not mentioned_company:
                    logger.debug(f"  Message {idx}: No company match")
                    continue
                
                logger.info(f"  Message {idx}: Found company: {mentioned_company}")
                
                job_urls = self._extract_linkedin_job_urls_from_text(full_text)
                
                if not job_urls:
                    logger.debug(f"  Message {idx}: No LinkedIn job URLs found")
                    continue
                
                logger.info(f"  Message {idx}: Found {len(job_urls)} job URL(s)")
                
                for job_id, job_url in job_urls:
                    if job_id in processed_job_ids:
                        logger.debug(f"    Skipping duplicate job ID: {job_id}")
                        continue
                    
                    job_title = self._extract_job_title_from_text(full_text, job_url)
                    
                    matched_jobs.append({
                        'company': mentioned_company,
                        'job_title': job_title,
                        'job_id': job_id,
                        'job_url': job_url
                    })
                    processed_job_ids.add(job_id)
                    logger.info(f"    ✓ Matched job: {mentioned_company} - {job_title} ({job_id})")
        
        # Step 4: Format output
        logger.info(f"STEP 4: Formatting output")
        
        if not matched_jobs:
            logger.warning(f"✗ No jobs found matching companies")
            logger.warning(f"Processed {len(messages)} messages, found 0 matches")
            return f"Processed {len(messages)} Slack messages. No jobs found matching companies from {companies_file_path}"
        
        logger.info(f"✓ Found {len(matched_jobs)} total matched jobs")
        
        # Generate plaintext output
        plaintext_lines = []
        plaintext_lines.append(f"=== Slack Jobs Matched ===")
        plaintext_lines.append(f"Total jobs: {len(matched_jobs)}")
        plaintext_lines.append(f"Companies matched: {len(set(j['company'] for j in matched_jobs))}")
        plaintext_lines.append("=" * 80)
        plaintext_lines.append("")
        
        for job in matched_jobs:
            line = f"{job['company']}, {job['job_title']}, {job['job_id']}, {job['job_url']}"
            plaintext_lines.append(line)
        
        # Step 5: Save to file
        logger.info(f"STEP 5: Saving output")
        output_path = output_file_path or "output/slack_parsed_jobs.txt"
        self._save_output(output_path, plaintext_lines)
        logger.info(f"✓ Saved {len(matched_jobs)} jobs to {output_path}")
        
        logger.info("=" * 80)
        logger.info(f"SlackParserTool COMPLETE - {len(matched_jobs)} jobs extracted")
        logger.info("=" * 80)
        
        return "\n".join(plaintext_lines)
    
    def _load_slack_json(self, json_path: str) -> List[Dict]:
        """Load Slack messages from JSON file"""
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Absolute path would be: {os.path.abspath(json_path)}")
            return []
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.error(f"JSON file is empty: {json_path}")
                    return []
                
                data = json.loads(content)
                messages = data.get('messages', [])
                if not messages:
                    logger.warning(f"JSON file has no 'messages' field or messages array is empty: {json_path}")
                return messages
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {json_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading JSON from {json_path}: {e}")
            return []
    
    def _load_companies(self, companies_path: str) -> List[str]:
        """Load company names from text file"""
        if not os.path.exists(companies_path):
            logger.error(f"Companies file not found: {companies_path}")
            return []
        
        companies = []
        with open(companies_path, 'r', encoding='utf-8') as f:
            for line in f:
                company = line.strip()
                if company and not company.startswith('#'):
                    companies.append(company)
        
        return companies
    
    def _extract_attachment_text(self, attachment: Dict) -> str:
        """Extract all text from a single attachment"""
        text_parts = []
        
        # Direct attachment text fields
        for key in ['text', 'fallback', 'pretext', 'title']:
            value = attachment.get(key, '')
            if value:
                text_parts.append(value)
        
        # Attachment blocks (CRITICAL: this is where Slack News Alerts put job data)
        att_blocks = attachment.get('blocks', [])
        for block in att_blocks:
            # Extract text from section blocks
            text_obj = block.get('text', {})
            if isinstance(text_obj, dict):
                block_text = text_obj.get('text', '')
                if block_text:
                    text_parts.append(block_text)
        
        # Attachment fields
        fields = attachment.get('fields', [])
        for field in fields:
            text_parts.append(field.get('title', ''))
            text_parts.append(field.get('value', ''))
        
        return ' '.join(text_parts)
    
    def _extract_full_message_text(self, msg: Dict) -> str:
        """Extract all text from a message (text + attachments + blocks)"""
        text_parts = []
        
        # Main text
        text = msg.get('text', '')
        if text:
            text_parts.append(text)
        
        # Attachments (CRITICAL: this is where Slack News Alerts put job data)
        attachments = msg.get('attachments', [])
        for att in attachments:
            # Direct attachment text fields
            for key in ['text', 'fallback', 'pretext', 'title']:
                value = att.get(key, '')
                if value:
                    text_parts.append(value)
            
            # IMPORTANT: Attachments can have their own blocks!
            att_blocks = att.get('blocks', [])
            for block in att_blocks:
                # Extract text from section blocks
                text_obj = block.get('text', {})
                if isinstance(text_obj, dict):
                    block_text = text_obj.get('text', '')
                    if block_text:
                        text_parts.append(block_text)
            
            # Attachment fields
            fields = att.get('fields', [])
            for field in fields:
                text_parts.append(field.get('title', ''))
                text_parts.append(field.get('value', ''))
        
        # Message-level blocks
        blocks = msg.get('blocks', [])
        for block in blocks:
            # Extract text from various block types
            text_obj = block.get('text', {})
            if isinstance(text_obj, dict):
                text_parts.append(text_obj.get('text', ''))
            
            # Rich text elements
            elements = block.get('elements', [])
            for elem in elements:
                if isinstance(elem, dict):
                    elem_text = elem.get('text', '')
                    if elem_text:
                        text_parts.append(elem_text)
                    
                    # Nested elements
                    nested = elem.get('elements', [])
                    for nested_elem in nested:
                        if isinstance(nested_elem, dict):
                            nested_text = nested_elem.get('text', '')
                            if nested_text:
                                text_parts.append(nested_text)
        
        full_text = ' '.join(text_parts)
        return full_text
    
    def _find_matching_company(self, text: str, companies: List[str]) -> Optional[str]:
        """Find if any company name is mentioned in the text"""
        text_lower = text.lower()
        
        # Sort companies by length (longest first) to match more specific names first
        # This prevents "EY" from matching before "Amazon" when both are present
        sorted_companies = sorted(companies, key=len, reverse=True)
        
        # Try word boundary matches first (most accurate)
        # This prevents "EY" from matching in words like "survey" or "they"
        for company in sorted_companies:
            # Create word boundary pattern for the company name
            # This will match "Amazon" in "Amazon Web Services" but not in "Amazonia"
            # and "EY" as a standalone word but not in "survey"
            pattern = r'\b' + re.escape(company.lower()) + r'\b'
            if re.search(pattern, text_lower):
                logger.debug(f"    Word boundary match: '{company}' found in text")
                return company
        
        # Try exact substring matches for companies with special characters
        # (word boundaries don't work well with & or parentheses)
        for company in sorted_companies:
            if company.lower() in text_lower and len(company) > 3:
                logger.debug(f"    Substring match: '{company}' found in text")
                return company
        
        # Try fuzzy matching (handle variations after removing suffixes)
        for company in sorted_companies:
            # Normalize both
            normalized_company = self._normalize_company_name(company)
            normalized_text = self._normalize_company_name(text)
            
            if normalized_company in normalized_text and len(normalized_company) > 3:
                logger.debug(f"    Fuzzy match: '{company}' normalized to '{normalized_company}'")
                return company
        
        return None
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for matching"""
        s = name.lower()
        # Remove common suffixes
        for suffix in [' llc', ' inc', ' corporation', ' corp', ' limited', ' ltd', ' plc', ' consulting']:
            s = s.replace(suffix, '')
        # Remove punctuation
        s = re.sub(r'[.,&()\']', ' ', s)
        # Collapse whitespace
        s = ' '.join(s.split())
        return s
    
    def _extract_linkedin_job_urls_from_text(self, text: str) -> List[tuple]:
        """Extract all LinkedIn job URLs from text"""
        
        # Find all LinkedIn job URLs - handle both plain and Slack markdown format
        # Slack format: <https://www.linkedin.com/jobs/view/12345|Text>
        # Plain format: https://www.linkedin.com/jobs/view/12345
        
        # Pattern to match job IDs from various formats
        patterns = [
            r'<https?://(?:www\.)?linkedin\.com/jobs/view/[^/]+?-(\d+)\|',  # Slack markdown with slug
            r'<https?://(?:www\.)?linkedin\.com/jobs/view/(\d+)\|',  # Slack markdown without slug
            r'https?://(?:www\.)?linkedin\.com/jobs/view/[^/]+?-(\d+)',  # Plain URL with slug
            r'https?://(?:www\.)?linkedin\.com/jobs/view/(\d+)',  # Plain URL without slug
        ]
        
        job_ids = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            job_ids.update(matches)
        
        # Return as (job_id, job_url) tuples
        results = []
        for job_id in sorted(job_ids):  # Sort for consistent ordering
            job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            results.append((job_id, job_url))
        
        logger.debug(f"    Found {len(results)} unique job IDs: {[jid for jid, _ in results]}")
        return results
    
    def _extract_job_title_from_text(self, text: str, job_url: str) -> str:
        """Try to extract job title from text"""
        
        # Pattern 1: Extract from Slack markdown link format
        # Format: <url|Company hiring Job Title in Location>
        slack_link_pattern = r'<[^|]+\|([^>]+hiring\s+([^>]+?)\s+in\s+[^>]+)>'
        match = re.search(slack_link_pattern, text)
        if match:
            # Extract just the job title part (between "hiring" and "in")
            job_title = match.group(2).strip()
            if job_title and len(job_title) > 3:
                return job_title[:150]
        
        # Pattern 2: Look for "Company hiring Job Title in Location" format
        hiring_pattern = r'hiring\s+([A-Z][^\n\r|]+?)\s+in\s+[A-Z]'
        match = re.search(hiring_pattern, text)
        if match:
            title = match.group(1).strip()
            # Stop at common delimiters
            for delimiter in [' at ', ' - ', '  ', '\n']:
                if delimiter in title:
                    title = title.split(delimiter)[0].strip()
            if len(title) > 3:
                return title[:150]
        
        # Pattern 3: Common job title patterns
        patterns = [
            r'(?:Role|Position|Title):\s*([A-Z][^\n\r|]+)',
            r'([A-Z][a-zA-Z\s&/\-]+(?:Engineer|Architect|Manager|Leader|Scientist|Analyst|Developer|Designer|Consultant|Specialist))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                # Clean up
                title = title.replace('*', '').replace('_', '').strip()
                # Stop at line break or excessive content
                if '\n' in title:
                    title = title.split('\n')[0].strip()
                # Limit length
                title = title[:150]
                if len(title) > 5:
                    return title
        
        # Fallback: extract from text if "hiring" pattern exists
        if 'hiring' in text.lower():
            # Try to find job title near "hiring" keyword
            hiring_match = re.search(r'hiring\s+([A-Z][^\n]+?)\s+in\s+', text)
            if hiring_match:
                return hiring_match.group(1).strip()[:150]
        
        return "Job Posting"
    
    def _save_output(self, output_path: str, lines: List[str]) -> None:
        """Save lines to output file"""
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')

