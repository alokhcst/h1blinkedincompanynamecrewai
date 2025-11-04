#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from h1blinkedincompanynamecrewai.crew import H1Blinkedincompanynamecrewai

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'companies_file_path': 'knowledge/H1BCompanyNameAtlanta.txt',
        'keywords': 'leadership, Snowflake, Azure Databricks, Data Architecture, Data Engineering, Data Engineering Leader, AI Engineering Leader, AWS Solutions Architect, Azure Solutions Architect, Data Science, DevOps, Cloud Engineering',
        'current_date_time': str(datetime.now()),
        'current_date': str(datetime.now().date())
    }

    try:
        H1Blinkedincompanynamecrewai().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'companies_file_path': '"knowledge/H1BCompanyNameAtlanta.txt',
        'keywords': 'Description',
        #'keywords': 'Leadership, Snowflake, Azure Databricks, Data Architecture, Data Engineering, Data Engineer, Senior Data Engineer, Principal Data Engineer, Data Engineering Manager, Director of Data Engineering, AI Engineer, Machine Learning Engineer, AI/ML Engineer, AWS Solutions Architect, Azure Solutions Architect, Solutions Architect, Cloud Architect, Data Scientist, Senior Data Scientist, Principal Data Scientist, DevOps Engineer, Senior DevOps Engineer, DevOps Manager, Cloud Engineer, Senior Cloud Engineer, Cloud Infrastructure Engineer, Platform Engineer, Data Platform Engineer, Analytics Engineer, Big Data Engineer, ETL Developer, Data Warehouse Engineer, Business Intelligence Engineer, MLOps Engineer, Staff Engineer, Engineering Manager, Technical Lead, Team Lead, VP of Engineering, Head of Data Engineering, Head of AI',
        'output_file_path': 'knowledge/linkedin_jobs.txt',
        'current_year': str(datetime.now().year)
    }
    try:
        H1Blinkedincompanynamecrewai().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        H1Blinkedincompanynamecrewai().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        H1Blinkedincompanynamecrewai().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        'companies_file_path': trigger_payload.get('companies_file_path', 'knowledge/H1BCompanyNameAtlanta.txt'),
        'keywords': trigger_payload.get('keywords', 'leadership, Snowflake, Azure Databricks, Data Architecture, Data Engineering, Data Engineering Leader, AI Engineering Leader, AWS Solutions Architect, Azure Solutions Architect, Data Science, DevOps, Cloud Engineering'),
        'output_file_path': trigger_payload.get('output_file_path', 'output/linkedin_jobs.txt'),
        "current_year": ""
    }

    try:
        result = H1Blinkedincompanynamecrewai().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
