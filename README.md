# Issue Backup Tool

Downloads and processes issues from any GitHub repository, organizing them by label and slug.

## Requirements

- Python 3.6+
- GitHub Personal Access Token

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory:

```bash
# Required
GITHUB_TOKEN=your_github_token_here

# Required - comma-separated list of labels to fetch
VALID_LABELS=bug,enhancement

# Optional - GitHub repository to fetch from (default: owner/repo)
GITHUB_REPO=owner/repo
```

Or set the variables in your environment:
```bash
export GITHUB_TOKEN='your_github_token'
export VALID_LABELS='bug,enhancement'
export GITHUB_REPO='owner/repo'
```

## Usage

You can either run both scripts at once using:
```bash
./update_threads.sh
```

Or run them separately:

1. First, fetch the issues:
```bash
python fetch_issues.py
```

2. Then, compose human-readable threads:
```bash
python compose_threads.py
```

### Output Structure

The scripts will create the following structure:
```
{label}/
  └── {slug}/
      └── {issue_id}/
          ├── issue.json     # Raw issue data
          ├── comments.json  # Raw comments data (if any)
          └── thread.md      # Human-readable conversation thread
```

where:
- `label` is from the VALID_LABELS configuration (or the issue's label if fetching all)
- `slug` is extracted from the first bracketed term in the issue title, or a fallback if not present
- `issue_id` is the GitHub issue number

### Thread Format

Each `thread.md` file contains:
- Issue title and metadata
- Original issue body
- Chronological comments with timestamps and authors 