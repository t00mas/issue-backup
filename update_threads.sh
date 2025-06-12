#!/bin/bash

# Exit on any error
set -e

echo "Updating issue threads..."

# Run fetch script
echo -e "\nFetching issues from GitHub..."
python fetch_issues.py

# Run compose script
echo -e "\nComposing threads..."
python compose_threads.py

echo -e "\nUpdate complete!" 