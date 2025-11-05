"""
Test script for SlackParserTool with keyword filtering
"""
import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from h1blinkedincompanynamecrewai.tools.slack_parser_tool import SlackParserTool

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True
)
logger = logging.getLogger(__name__)

def main():
    """Test the SlackParserTool with keyword filtering"""
    logger.info("=" * 80)
    logger.info("Testing SlackParserTool with Keyword Filtering")
    logger.info("=" * 80)
    
    # Create tool instance
    tool = SlackParserTool()
    
    # Test parameters
    slack_json_path = "output/slack_jobs_raw.json"
    companies_file_path = "knowledge/H1BCompanyNameAtlanta.txt"
    keywords_file_path = "input/job_keywords.txt"
    output_file_path = "output/slack_parsed_jobs_test_keywords.txt"
    
    # Check if required files exist
    if not os.path.exists(slack_json_path):
        logger.error(f"❌ Slack JSON file not found: {slack_json_path}")
        logger.info("Please run the crew first to generate Slack data")
        return
    
    if not os.path.exists(companies_file_path):
        logger.error(f"❌ Companies file not found: {companies_file_path}")
        return
    
    if not os.path.exists(keywords_file_path):
        logger.error(f"❌ Keywords file not found: {keywords_file_path}")
        return
    
    logger.info(f"✓ All required files found")
    logger.info(f"Input files:")
    logger.info(f"  - Slack JSON: {slack_json_path}")
    logger.info(f"  - Companies: {companies_file_path}")
    logger.info(f"  - Keywords: {keywords_file_path}")
    logger.info(f"Output file:")
    logger.info(f"  - {output_file_path}")
    logger.info("")
    
    # Run the tool
    logger.info("Running SlackParserTool with keyword filtering...")
    logger.info("=" * 80)
    
    result = tool._run(
        slack_json_path=slack_json_path,
        companies_file_path=companies_file_path,
        keywords_file_path=keywords_file_path,
        output_file_path=output_file_path
    )
    
    logger.info("=" * 80)
    logger.info("Tool execution completed")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Result:")
    logger.info(result)
    logger.info("")
    
    # Check if output file was created
    if os.path.exists(output_file_path):
        logger.info(f"✓ Output file created: {output_file_path}")
        
        # Read and display first few lines
        with open(output_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            logger.info(f"✓ Output contains {len(lines)} lines")
            logger.info("")
            logger.info("First 10 lines:")
            for i, line in enumerate(lines[:10], 1):
                logger.info(f"  {i}. {line.rstrip()}")
    else:
        logger.error(f"❌ Output file was not created: {output_file_path}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("Test completed")
    logger.info("=" * 80)
    
    # Compare with non-filtered results
    non_filtered_path = "output/slack_parsed_jobs.txt"
    if os.path.exists(non_filtered_path) and os.path.exists(output_file_path):
        with open(non_filtered_path, 'r', encoding='utf-8') as f:
            non_filtered_lines = [line for line in f if line.strip() and not line.startswith('===') and not line.startswith('Total') and not line.startswith('Companies')]
        
        with open(output_file_path, 'r', encoding='utf-8') as f:
            filtered_lines = [line for line in f if line.strip() and not line.startswith('===') and not line.startswith('Total') and not line.startswith('Companies')]
        
        logger.info("")
        logger.info("Comparison:")
        logger.info(f"  - Without keyword filtering: {len(non_filtered_lines)} jobs")
        logger.info(f"  - With keyword filtering: {len(filtered_lines)} jobs")
        logger.info(f"  - Filtered out: {len(non_filtered_lines) - len(filtered_lines)} jobs")

if __name__ == "__main__":
    main()

