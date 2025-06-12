#!/usr/bin/env python3

import os
import re
import requests
from typing import List, Dict, Set
import json
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN not found in environment or .env file")
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

DEFAULT_REPO = None
REPO = os.environ.get('GITHUB_REPO', DEFAULT_REPO)
if not REPO:
    print("Error: GITHUB_REPO environment variable is required")
    sys.exit(1)
print(f"Using repository: {REPO}")

DEFAULT_LABELS = {}
def get_valid_labels() -> Set[str]:
    env_labels = os.environ.get('VALID_LABELS')
    if env_labels:
        return {label.strip() for label in env_labels.split(',')}
    else:
        print("Error: VALID_LABELS environment variable is required")
        sys.exit(1)

VALID_LABELS = get_valid_labels()
print(f"Using labels: {', '.join(sorted(VALID_LABELS))}")

BASE_URL = f"https://api.github.com/repos/{REPO}/issues"
METADATA_FILE = ".fetch_metadata.json"

def load_metadata() -> Dict:
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {'last_fetch': '1970-01-01T00:00:00Z', 'issues': {}}

def save_metadata(metadata: Dict) -> None:
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def extract_slug(title: str) -> str:
    match = re.search(r'\[([\w-]+)\]', title)
    return match.group(1) if match else "unknown"

def fetch_comments(comments_url: str) -> List[Dict]:
    try:
        response = requests.get(
            comments_url,
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching comments: {e}")
        print("Response:", getattr(e.response, 'text', 'No response text'))
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding comments JSON: {e}")
        return []

def process_issue(issue: Dict, label: str, metadata: Dict) -> None:
    issue_id = str(issue['number'])
    issue_key = f"{label}/{issue_id}"
    
    # Check if issue needs updating
    if issue_key in metadata['issues']:
        last_updated = metadata['issues'][issue_key]['updated_at']
        if issue['updated_at'] <= last_updated:
            print(f"Skipping issue {issue_id} - no updates since {last_updated}")
            return

    slug = extract_slug(issue['title'])
    directory = f"{label}/{slug}/{issue_id}"
    os.makedirs(directory, exist_ok=True)
    
    # Save main issue data
    with open(f"{directory}/issue.json", 'w') as f:
        json.dump(issue, f, indent=2)
    
    # Fetch and save comments if they exist
    if issue['comments'] > 0:
        print(f"Fetching {issue['comments']} comments for issue {issue_id}")
        comments = fetch_comments(issue['comments_url'])
        if comments:
            with open(f"{directory}/comments.json", 'w') as f:
                json.dump(comments, f, indent=2)
    
    # Update metadata
    metadata['issues'][issue_key] = {
        'updated_at': issue['updated_at'],
        'path': directory
    }
    
    print(f"Saved issue {issue_id} with slug '{slug}' under label '{label}' ({issue['comments']} comments)")

def fetch_and_process_issues(label: str, metadata: Dict) -> None:
    page = 1
    total_processed = 0
    
    while True:
        try:
            print(f"Fetching page {page} for label '{label}'...")
            response = requests.get(
                BASE_URL,
                headers=HEADERS,
                params={
                    'state': 'all',
                    'per_page': 100,
                    'page': page,
                    'labels': label,
                    'since': metadata['last_fetch']  # Only fetch issues updated since last fetch
                },
                timeout=30
            )
            
            if response.status_code == 401:
                print("Error: Invalid authentication token")
                print("Response:", response.text)
                sys.exit(1)
            
            if response.status_code == 403:
                print("Error: API rate limit exceeded or permission denied")
                print("Response:", response.text)
                sys.exit(1)
                
            response.raise_for_status()
            
            batch = response.json()
            if not batch:
                break
                
            print(f"Retrieved {len(batch)} issues")
            
            for issue in batch:
                process_issue(issue, label, metadata)
                total_processed += 1
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            print("Response:", getattr(e.response, 'text', 'No response text'))
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print("Response text:", response.text)
            sys.exit(1)
    
    return total_processed

def main():
    metadata = load_metadata()
    total_issues = 0
    
    for label in VALID_LABELS:
        print(f"\nProcessing issues with label: {label}")
        processed = fetch_and_process_issues(label, metadata)
        total_issues += processed
        print(f"Completed processing {processed} issues for label '{label}'")
    
    # Update last fetch time
    metadata['last_fetch'] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_metadata(metadata)
    
    print(f"\nDone! Processed {total_issues} total issues")

if __name__ == "__main__":
    main() 