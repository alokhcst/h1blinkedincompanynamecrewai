from crewai.tools import BaseTool
from typing import Type, List, Optional, Dict
from pydantic import BaseModel, Field
import os
import csv
import re
import json
from datetime import datetime, timedelta
import requests
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True  # Override any existing logging config
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure this logger is at DEBUG level


class SlackJobsToolInput(BaseModel):
    """Input schema for SlackJobsTool."""
    channel_name: str = Field(default="h1bjobs", description="Slack channel name to read from (without #)")
    days_back: int = Field(default=30, description="Number of days to look back for messages")
    output_file_path: Optional[str] = Field(
        default="output/slack_jobs.txt",
        description="Plaintext path to save job listings"
    )


class SlackJobsTool(BaseTool):
    name: str = "SlackJobsTool"
    description: str = (
        "Reads ALL messages from a Slack channel (default: #h1bjobs) and logs them to a plain text file. "
        "Each message includes timestamp, user, full text, attachments, and files. "
        "Filters messages from the last N days. Requires SLACK_BOT_TOKEN environment variable."
    )
    args_schema: Type[BaseModel] = SlackJobsToolInput

    def _run(
        self, 
        channel_name: str = "h1bjobs",
        days_back: int = 30,
        output_file_path: Optional[str] = None
    ) -> str:
        """
        Read ALL messages from Slack channel and log them to plain text file.
        
        Args:
            channel_name: Slack channel name (without #)
            days_back: Number of days to look back
            output_file_path: Path to save all messages
        
        Returns:
            Plain text with all messages logged
        """
        logger.info("=" * 80)
        logger.info("SlackJobsTool._run() CALLED")
        logger.info("=" * 80)
        logger.info(f"Parameters:")
        logger.info(f"  - channel_name: {channel_name}")
        logger.info(f"  - days_back: {days_back}")
        logger.info(f"  - output_file_path: {output_file_path}")
        
        # Check for Slack Bot Token
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        if not slack_token:
            logger.error("SLACK_BOT_TOKEN environment variable not found!")
            return "ERROR: Missing SLACK_BOT_TOKEN environment variable. Get it from https://api.slack.com/apps"
        
        logger.info(f"✓ SLACK_BOT_TOKEN found (length: {len(slack_token)})")
        
        # Setup
        output_path = output_file_path or "output/slack_jobs.txt"
        logger.info(f"Output paths:")
        logger.info(f"  - Text file: {output_path}")
        logger.info(f"  - JSON file: {output_path.replace('.txt', '_raw.json')}")
        
        # Calculate time cutoff
        cutoff_timestamp = (datetime.utcnow() - timedelta(days=days_back)).timestamp()
        cutoff_datetime = datetime.utcnow() - timedelta(days=days_back)
        
        logger.info(f"Time window:")
        logger.info(f"  - Current UTC time: {datetime.utcnow().isoformat()}")
        logger.info(f"  - Cutoff date: {cutoff_datetime.isoformat()}")
        logger.info(f"  - Cutoff timestamp: {cutoff_timestamp}")
        
        # Step 1: Get channel ID
        logger.info(f"STEP 1: Looking up Slack channel: #{channel_name}")
        channel_id = self._get_channel_id(slack_token, channel_name)
        if not channel_id:
            logger.error(f"✗ Failed to find channel #{channel_name}")
            return f"ERROR: Could not find Slack channel #{channel_name}. Check channel name and bot permissions."
        
        logger.info(f"✓ Found channel ID: {channel_id}")
        
        # Step 2: Fetch all messages
        logger.info(f"STEP 2: Fetching messages from channel {channel_id}")
        messages = self._fetch_channel_messages(slack_token, channel_id, cutoff_timestamp)
        logger.info(f"✓ Retrieved {len(messages)} total messages from #{channel_name}")
        
        if not messages:
            # Still save empty JSON file so parser doesn't fail
            json_path = output_path.replace('.txt', '_raw.json')
            self._save_raw_json(json_path, [])
            logger.warning(f"✗ No messages found in #{channel_name} in the last {days_back} days. Created empty JSON file.")
            return f"No messages found in #{channel_name} in the last {days_back} days. Created empty JSON file at {json_path}."
        
        # Step 3: Format and log all messages
        logger.info(f"STEP 3: Formatting {len(messages)} messages for output")
        plaintext_lines = []
        plaintext_lines.append(f"=== Messages from #{channel_name} (Last {days_back} days) ===")
        plaintext_lines.append(f"Total messages: {len(messages)}")
        plaintext_lines.append(f"Retrieved: {datetime.utcnow().isoformat()}")
        plaintext_lines.append("=" * 80)
        plaintext_lines.append("")
        
        logger.info(f"Processing messages (oldest first)...")
        for idx, msg in enumerate(reversed(messages), 1):  # Reverse to show oldest first
            if idx <= 3 or idx == len(messages):
                logger.debug(f"  Processing message {idx}/{len(messages)}")
            # Extract ALL message details
            text = msg.get('text', '')
            user = msg.get('user', 'Unknown')
            ts = msg.get('ts', '')
            msg_type = msg.get('type', 'message')
            subtype = msg.get('subtype', '')
            thread_ts = msg.get('thread_ts', '')
            reply_count = msg.get('reply_count', 0)
            
            # Convert timestamp to readable date
            try:
                msg_datetime = datetime.fromtimestamp(float(ts))
                date_str = msg_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except:
                date_str = 'Unknown date'
            
            # Format message header
            plaintext_lines.append(f"{'='*80}")
            plaintext_lines.append(f"Message #{idx}")
            plaintext_lines.append(f"{'='*80}")
            plaintext_lines.append(f"Timestamp: {ts}")
            plaintext_lines.append(f"Date: {date_str}")
            plaintext_lines.append(f"User ID: {user}")
            plaintext_lines.append(f"Type: {msg_type}")
            if subtype:
                plaintext_lines.append(f"Subtype: {subtype}")
            if thread_ts:
                plaintext_lines.append(f"Thread TS: {thread_ts}")
                plaintext_lines.append(f"Replies: {reply_count}")
            plaintext_lines.append("")
            
            # Message text
            plaintext_lines.append("TEXT:")
            plaintext_lines.append(text if text else "(empty)")
            plaintext_lines.append("")
            
            # Reactions
            reactions = msg.get('reactions', [])
            if reactions:
                plaintext_lines.append("REACTIONS:")
                for reaction in reactions:
                    emoji = reaction.get('name', '')
                    count = reaction.get('count', 0)
                    plaintext_lines.append(f"  {emoji}: {count}")
                plaintext_lines.append("")
            
            # Attachments with full details
            attachments = msg.get('attachments', [])
            if attachments:
                plaintext_lines.append(f"ATTACHMENTS: ({len(attachments)} total)")
                for att_idx, att in enumerate(attachments, 1):
                    plaintext_lines.append(f"  Attachment {att_idx}:")
                    
                    # All attachment fields
                    for key in ['title', 'title_link', 'text', 'fallback', 'pretext', 'footer', 'author_name']:
                        value = att.get(key, '')
                        if value:
                            plaintext_lines.append(f"    {key}: {value}")
                    
                    # Fields array
                    fields = att.get('fields', [])
                    if fields:
                        plaintext_lines.append(f"    Fields:")
                        for field in fields:
                            title = field.get('title', '')
                            value = field.get('value', '')
                            plaintext_lines.append(f"      - {title}: {value}")
                    
                    plaintext_lines.append("")
            
            # Files with full details
            files = msg.get('files', [])
            if files:
                plaintext_lines.append(f"FILES: ({len(files)} total)")
                for file_idx, file in enumerate(files, 1):
                    plaintext_lines.append(f"  File {file_idx}:")
                    plaintext_lines.append(f"    Name: {file.get('name', 'Unknown')}")
                    plaintext_lines.append(f"    Title: {file.get('title', '')}")
                    plaintext_lines.append(f"    Mimetype: {file.get('mimetype', '')}")
                    plaintext_lines.append(f"    Size: {file.get('size', 0)} bytes")
                    plaintext_lines.append(f"    URL: {file.get('url_private', '')}")
                    plaintext_lines.append(f"    Permalink: {file.get('permalink', '')}")
                    plaintext_lines.append("")
            
            # Blocks (rich formatting)
            blocks = msg.get('blocks', [])
            if blocks:
                plaintext_lines.append(f"BLOCKS: ({len(blocks)} total)")
                for block_idx, block in enumerate(blocks, 1):
                    block_type = block.get('type', 'unknown')
                    plaintext_lines.append(f"  Block {block_idx} (type: {block_type}):")
                    
                    # Extract text from common block types
                    if block_type == 'section':
                        text_obj = block.get('text', {})
                        if text_obj:
                            plaintext_lines.append(f"    Text: {text_obj.get('text', '')}")
                    elif block_type == 'rich_text':
                        # Rich text can have multiple elements
                        elements = block.get('elements', [])
                        for elem in elements:
                            elem_elements = elem.get('elements', [])
                            for e in elem_elements:
                                e_text = e.get('text', '')
                                if e_text:
                                    plaintext_lines.append(f"    {e_text}")
                    
                    plaintext_lines.append("")
            
            # Metadata
            metadata = msg.get('metadata', {})
            if metadata:
                plaintext_lines.append(f"METADATA:")
                plaintext_lines.append(f"  {json.dumps(metadata, indent=4)}")
                plaintext_lines.append("")
            
            # Edited info
            if msg.get('edited'):
                edited = msg['edited']
                edited_ts = edited.get('ts', '')
                try:
                    edited_datetime = datetime.fromtimestamp(float(edited_ts))
                    edited_str = edited_datetime.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    edited_str = edited_ts
                plaintext_lines.append(f"EDITED: {edited_str} by user {edited.get('user', 'Unknown')}")
                plaintext_lines.append("")
            
            plaintext_lines.append("")
        
        logger.info(f"✓ Formatted {len(messages)} messages into {len(plaintext_lines)} lines")
        
        # Step 4: Save to files
        logger.info(f"STEP 4: Saving output files")
        self._save_all_messages(output_path, plaintext_lines)
        logger.info(f"✓ Saved plaintext to: {output_path}")
        
        # Also save raw JSON for complete data preservation
        json_path = output_path.replace('.txt', '_raw.json')
        self._save_raw_json(json_path, messages)
        logger.info(f"✓ Saved raw JSON to: {json_path}")
        
        logger.info("=" * 80)
        logger.info(f"SlackJobsTool COMPLETE - {len(messages)} messages processed")
        logger.info("=" * 80)
        
        # Return summary with first few messages
        summary_lines = plaintext_lines[:50]  # First 50 lines
        if len(plaintext_lines) > 50:
            summary_lines.append(f"\n... and {len(plaintext_lines) - 50} more lines")
            summary_lines.append(f"\nFull output saved to:")
            summary_lines.append(f"  - Plaintext: {output_path}")
            summary_lines.append(f"  - Raw JSON: {json_path}")
        
        result = "\n".join(summary_lines)
        logger.info(f"Returning {len(summary_lines)} lines of summary")
        return result
    
    def _get_channel_id(self, token: str, channel_name: str) -> Optional[str]:
        """Get Slack channel ID from channel name"""
        url = "https://slack.com/api/conversations.list"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"types": "public_channel,private_channel"}
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()  # Raise exception for HTTP errors
            data = resp.json()
            
            if not data.get('ok'):
                error_msg = data.get('error', 'Unknown error')
                logger.error(f"Slack API error: {error_msg}")
                if error_msg == 'invalid_auth':
                    logger.error("Invalid Slack token. Check your SLACK_BOT_TOKEN environment variable.")
                elif error_msg == 'missing_scope':
                    logger.error("Bot missing required scopes. Check bot permissions in Slack app settings.")
                return None
            
            channels = data.get('channels', [])
            logger.info(f"Found {len(channels)} channels. Searching for: #{channel_name}")
            
            for channel in channels:
                if channel.get('name') == channel_name:
                    channel_id = channel.get('id')
                    logger.info(f"Found channel #{channel_name} with ID: {channel_id}")
                    return channel_id
            
            logger.warning(f"Channel #{channel_name} not found in available channels.")
            logger.warning(f"Available channels: {[c.get('name') for c in channels[:10]]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching channel list: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching channel list: {e}")
            return None
    
    def _fetch_channel_messages(self, token: str, channel_id: str, oldest_ts: float) -> List[Dict]:
        """Fetch messages from a Slack channel"""
        url = "https://slack.com/api/conversations.history"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "channel": channel_id,
            "oldest": str(oldest_ts),
            "limit": 1000
        }
        
        messages = []
        
        try:
            page_count = 0
            while True:
                page_count += 1
                logger.debug(f"Fetching page {page_count} of messages...")
                
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                resp.raise_for_status()  # Raise exception for HTTP errors
                data = resp.json()
                
                if not data.get('ok'):
                    error_msg = data.get('error', 'Unknown error')
                    logger.error(f"Slack API error fetching messages: {error_msg}")
                    if error_msg == 'channel_not_found':
                        logger.error(f"Channel ID {channel_id} not found. Check bot permissions.")
                    elif error_msg == 'missing_scope':
                        logger.error("Bot missing required scopes (channels:history). Check bot permissions.")
                    break
                
                batch = data.get('messages', [])
                messages.extend(batch)
                logger.debug(f"Page {page_count}: Retrieved {len(batch)} messages (total: {len(messages)})")
                
                # Check for pagination
                if not data.get('has_more'):
                    logger.debug("No more pages to fetch")
                    break
                
                # Update cursor for next page
                params['cursor'] = data.get('response_metadata', {}).get('next_cursor')
                if not params.get('cursor'):
                    logger.debug("No cursor for next page")
                    break
            
            logger.info(f"Total messages fetched: {len(messages)} across {page_count} page(s)")
            return messages
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching messages: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    def _save_all_messages(self, txt_path: str, lines: List[str]) -> None:
        """Save all message lines to text file"""
        os.makedirs(os.path.dirname(txt_path) or '.', exist_ok=True)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
    
    def _save_raw_json(self, json_path: str, messages: List[Dict]) -> None:
        """Save raw message data as JSON for complete data preservation"""
        os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'channel': 'h1bjobs',
                'total_messages': len(messages),
                'retrieved_at': datetime.utcnow().isoformat(),
                'messages': messages
            }, f, indent=2)

