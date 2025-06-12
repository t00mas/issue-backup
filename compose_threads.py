#!/usr/bin/env python3

import os
import json
from datetime import datetime
from typing import List, Dict
import hashlib

def format_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def get_content_hash(filepath: str) -> str:
    """Calculate SHA-256 hash of a file's content."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def load_compose_metadata() -> Dict:
    """Load metadata about previously composed threads."""
    if os.path.exists(".compose_metadata.json"):
        with open(".compose_metadata.json", 'r') as f:
            return json.load(f)
    return {}

def save_compose_metadata(metadata: Dict) -> None:
    """Save metadata about composed threads."""
    with open(".compose_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

def compose_thread(directory: str, metadata: Dict) -> None:
    # Check if files have been modified
    issue_path = os.path.join(directory, "issue.json")
    comments_path = os.path.join(directory, "comments.json")
    
    current_hashes = {
        'issue': get_content_hash(issue_path),
        'comments': get_content_hash(comments_path)
    }
    
    # Skip if nothing has changed
    if directory in metadata:
        old_hashes = metadata[directory]
        if old_hashes == current_hashes:
            print(f"Skipping {directory} - no changes detected")
            return
    
    # Read issue data
    with open(issue_path, "r") as f:
        issue = json.load(f)
    
    # Prepare the conversation thread
    thread = []
    
    # Add issue title and metadata
    thread.append(f"Title: {issue['title']}")
    thread.append(f"Created by: {issue['user']['login']} on {format_date(issue['created_at'])}")
    thread.append(f"State: {issue['state']}")
    thread.append(f"Labels: {', '.join(label['name'] for label in issue['labels'])}")
    thread.append("\n" + "="*80 + "\n")
    
    # Add main issue body
    thread.append("INITIAL POST:")
    thread.append("-"*80)
    thread.append(issue['body'])
    
    # Add comments if they exist
    if os.path.exists(comments_path):
        with open(comments_path, "r") as f:
            comments = json.load(f)
        
        if comments:
            thread.append("\n" + "="*80 + "\n")
            thread.append("COMMENTS:")
            thread.append("-"*80)
            
            for comment in comments:
                thread.append(f"\nOn {format_date(comment['created_at'])}, {comment['user']['login']} wrote:")
                thread.append("-"*40)
                thread.append(comment['body'])
    
    # Write the thread to a file
    output_file = os.path.join(directory, "thread.md")
    with open(output_file, "w") as f:
        f.write("\n\n".join(thread))
    
    # Update metadata
    metadata[directory] = current_hashes

def process_all_threads() -> None:
    metadata = load_compose_metadata()
    processed = 0
    
    # Walk through all label directories
    for label in ['faro', 'app-o11y']:
        if not os.path.exists(label):
            continue
            
        print(f"\nProcessing {label} issues...")
        
        # Walk through slug directories
        for slug in os.listdir(label):
            slug_path = os.path.join(label, slug)
            if not os.path.isdir(slug_path):
                continue
            
            # Walk through issue directories
            for issue_id in os.listdir(slug_path):
                issue_path = os.path.join(slug_path, issue_id)
                if not os.path.isdir(issue_path):
                    continue
                
                if os.path.exists(os.path.join(issue_path, "issue.json")):
                    print(f"Checking thread for {label}/{slug}/{issue_id}")
                    compose_thread(issue_path, metadata)
                    processed += 1
    
    save_compose_metadata(metadata)
    print(f"\nDone! Processed {processed} issue directories")

def main():
    print("Starting to compose conversation threads...")
    process_all_threads()

if __name__ == "__main__":
    main() 