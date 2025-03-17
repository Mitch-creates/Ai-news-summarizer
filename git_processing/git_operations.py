import logging
import os
import subprocess
import time
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Detect GitHub Actions environment
if "GITHUB_ACTIONS" in os.environ:
    logging.info("🔹 Running inside GitHub Actions")
    BLOG_REPOSITORY_PATH = os.path.join(os.getcwd(), "blog_repo")  # Uses `blog_repo/` in GitHub Actions
else:
    logging.info("🔹 Running locally")
    BLOG_REPOSITORY_PATH = os.getenv("BLOG_REPOSITORY_PATH", "C:\\Users\\michi\\Projects\\News-summary-blog")  # Uses local path

# Ensure the directory exists before proceeding
os.makedirs(BLOG_REPOSITORY_PATH, exist_ok=True)

logging.info(f"✅ Using blog repository path: {BLOG_REPOSITORY_PATH}")

def run_git_command(command, cwd):
    """Runs a Git command and handles errors using Popen."""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",  # Ensure proper encoding
            errors="replace"  # Prevent crashes from bad characters
        )

        stdout, stderr = process.communicate()  # Wait for the command to complete

        if process.returncode != 0:  # Check for errors
            logging.error(f"Git command failed: {command} -> {stderr.strip()}")
            return False

        return stdout.strip()  # Return command output if successful

    except Exception as e:
        logging.error(f"Error running Git command {command}: {e}")
        return False

def check_git_changes(repo_path):
    """Check if there are any uncommitted changes in the repository."""
    status_output = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
    return bool(status_output.stdout.strip())

def setup_git():
    """Configures Git user credentials and authentication."""
    try:
        blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH")
        GH_TOKEN = os.getenv("GH_TOKEN")
        repo_url = os.getenv("BLOG_REPOSITORY_URL_HTTPS")
        OWNER = os.getenv("OWNER")
        OWNER_EMAIL = os.getenv("OWNER_EMAIL")

        run_git_command(["git", "config", "--global", "user.name", OWNER], blog_repo_path)
        run_git_command(["git", "config", "--global", "user.email", OWNER_EMAIL], blog_repo_path)

        repo_url_with_token = repo_url.replace("https://", f"https://{GH_TOKEN}@")
        run_git_command(["git", "remote", "set-url", "origin", repo_url_with_token], blog_repo_path)

        logging.info("Git authentication setup complete.")
    except Exception as e:
        logging.error(f"Error setting up Git authentication: {e}")

def fetch_latest_branch():
    """Ensure the latest `develop` branch is checked out and updated safely."""
    try:
        blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH")

        if check_git_changes(blog_repo_path):
            logging.info("Uncommitted changes detected! Stashing changes before switching branches.")
            run_git_command(["git", "stash"], blog_repo_path)

        # Add this step to handle untracked files before switching branches
        untracked_files = run_git_command(["git", "ls-files", "--others", "--exclude-standard"], blog_repo_path)
        if untracked_files:
            logging.info("Untracked files detected. Adding them before switching branches.")
            run_git_command(["git", "add", "."], blog_repo_path)
            run_git_command(["git", "commit", "-m", "Adding untracked files before branch switch"], blog_repo_path)

        # Now, safely switch to develop
        run_git_command(["git", "checkout", "develop"], blog_repo_path)
        run_git_command(["git", "pull", "origin", "develop"], blog_repo_path)

        # Check if stash exists before popping
        stash_list = run_git_command(["git", "stash", "list"], blog_repo_path)
        if stash_list and "stash@{" in stash_list:
            logging.info("Restoring stashed changes...")
            stash_result = run_git_command(["git", "stash", "pop"], blog_repo_path)

            if "conflict" in stash_result.lower():
                logging.warning("Merge conflict detected in stash pop. Attempting auto-resolution...")
                run_git_command(["git", "checkout", "--theirs", "."], blog_repo_path)  # Keep latest version
                run_git_command(["git", "add", "."], blog_repo_path)  # Mark conflicts as resolved
                run_git_command(["git", "commit", "-m", "Auto-resolved stash conflicts"], blog_repo_path)

        logging.info("Develop branch is up to date.")
    except Exception as e:
        logging.error(f"Error fetching latest branch: {e}")


def commit_changes(blogposts):
    """Commit all blog posts together in a single commit."""
    try:
        if not blogposts:
            logging.info("No new blog posts to commit. Skipping GitHub push.")
            return False

        blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH")

        # Check if there are conflicts before adding changes
        merge_status = run_git_command(["git", "diff", "--name-only", "--diff-filter=U"], blog_repo_path)
        if merge_status:
            logging.error("Unresolved merge conflicts detected! Attempting to auto-resolve...")
            run_git_command(["git", "checkout", "--theirs", "."], blog_repo_path)  # Keep latest version
            run_git_command(["git", "add", "."], blog_repo_path)  # Mark conflicts as resolved

        for blogpost in blogposts:
            file_path = blogpost.markdown_file_path

            if not os.path.exists(file_path):
                logging.error(f"File not found: {file_path}. Adding a delay...")
                time.sleep(2)  # Wait for file to be written
                if not os.path.exists(file_path):
                    logging.error(f"File STILL missing after delay: {file_path}")
                    continue  # Skip this file

            run_git_command(["git", "add", file_path], blog_repo_path)

        commit_message = f"Publish {', '.join(blogpost.blogpost_subject for blogpost in blogposts)} Weekly Blogposts"
        commit_result = run_git_command(["git", "commit", "--allow-empty", "-m", commit_message], blog_repo_path)

        if "unmerged files" in commit_result.lower():
            logging.error("Commit failed due to unresolved merge conflicts. Fix manually!")
            return False

        logging.info(f"Successfully committed {len(blogposts)} blog post(s).")
        return True

    except Exception as e:
        logging.error(f"Error committing blog posts: {e}")
        return False
    
def push_changes():
    """Push all committed changes to the develop branch and ensure master is updated after merging."""
    try:
        blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH")
        run_git_command(["git", "push", "origin", "develop"], blog_repo_path)
        logging.info("Successfully pushed changes to remote repository.")

        # Ensure master is updated after merge
        run_git_command(["git", "checkout", "master"], blog_repo_path)
        pull_result = run_git_command(["git", "pull", "origin", "master"], blog_repo_path)

        if "conflict" in pull_result.lower():
            logging.warning("Merge conflict detected in master pull. Attempting auto-resolution...")
            run_git_command(["git", "checkout", "--theirs", "."], blog_repo_path)  # Keep latest version
            run_git_command(["git", "add", "."], blog_repo_path)  # Mark conflicts as resolved
            run_git_command(["git", "commit", "-m", "Auto-resolved merge conflicts in master"], blog_repo_path)

        logging.info("Master branch is now up to date.")
    except Exception as e:
        logging.error(f"Error pushing changes to GitHub: {e}")


def check_existing_pr():
    """Checks if there's already an open PR from `develop` to `master`."""
    try:
        OWNER = os.getenv("OWNER")
        REPO = os.getenv("REPO_NAME")
        GH_TOKEN = os.getenv("GH_TOKEN")

        api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls?state=open"
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to check existing PRs: {response.json()}")
            return None

        for pr in response.json():
            if pr["head"]["ref"] == "develop" and pr["base"]["ref"] == "master":
                return pr["number"]

        return None

    except Exception as e:
        logging.error(f"Error checking for existing PRs: {e}")
        return None
def create_pull_request():
    """Creates a new PR from `develop` to `master`."""
    try:
        OWNER = os.getenv("OWNER")
        REPO = os.getenv("REPO_NAME")
        GH_TOKEN = os.getenv("GH_TOKEN")

        api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        payload = {
            "title": "Automated Blogpost Updates",
            "head": "develop",
            "base": "master",
            "body": "This PR contains all weekly blogpost updates."
        }

        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 201:
            pr_number = response.json().get("number")
            logging.info(f"Pull request created successfully! PR number: {pr_number}")
            return pr_number
        else:
            logging.error(f"Failed to create pull request: {response.json()}")
            return None

    except Exception as e:
        logging.error(f"Error creating PR: {e}")
        return None
def commit_and_push_all(blogposts):
    """Process each blog post separately but commit & push everything together."""
    try:
        setup_git()
        fetch_latest_branch()

        if commit_changes(blogposts):
            push_changes()

            existing_pr = check_existing_pr()
            if existing_pr:
                logging.info(f"Existing PR found: #{existing_pr}. Skipping new PR creation.")
                return existing_pr
            return create_pull_request()

        logging.info("No changes detected. Skipping PR creation.")
        return None

    except Exception as e:
        logging.error(f"Error during commit and push process: {e}")
        return None
    
import time

import time

def merge_pull_request(pr_number):
    """Merges an open PR (`develop` → `master`)."""
    if pr_number is None:
        logging.info("No valid PR found. Skipping merge.")
        return

    REPO = os.getenv("REPO_NAME")
    OWNER = os.getenv("OWNER")
    GH_TOKEN = os.getenv("GH_TOKEN")
    blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH")

    pr_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    # Wait for GitHub to calculate mergeability
    attempts = 0
    while attempts < 10:
        pr_response = requests.get(pr_url, headers=headers)
        pr_data = pr_response.json()

        mergeable_state = pr_data.get("mergeable_state", "unknown")
        logging.info(f"Checking mergeability of PR #{pr_number}: {mergeable_state}")

        if mergeable_state == "clean":
            break
        elif mergeable_state == "dirty":
            logging.warning(f"PR #{pr_number} has conflicts. Attempting auto-resolution...")
            
            # Checkout master and pull latest changes
            run_git_command(["git", "checkout", "master"], blog_repo_path)
            run_git_command(["git", "pull", "origin", "master"], blog_repo_path)

            # Merge develop into master with conflict resolution
            run_git_command(["git", "merge", "--strategy-option=theirs", "develop"], blog_repo_path)
            run_git_command(["git", "add", "."], blog_repo_path)  # Stage resolved files
            run_git_command(["git", "commit", "-m", "Auto-resolved merge conflicts"], blog_repo_path)
            run_git_command(["git", "push", "origin", "master"], blog_repo_path)

            logging.info(f"Successfully force-merged `develop` into `master`.")
            return True
        else:
            logging.info("Waiting for GitHub to determine mergeability...")
            time.sleep(10)
            attempts += 1

    # If mergeable, merge via API
    merge_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}/merge"
    merge_payload = {"commit_message": f"Auto-merging PR #{pr_number}"}
    merge_response = requests.put(merge_url, json=merge_payload, headers=headers)

    if merge_response.status_code == 200:
        logging.info(f"Pull request #{pr_number} merged successfully!")

        # Ensure master is updated after merge
        run_git_command(["git", "checkout", "master"], blog_repo_path)
        run_git_command(["git", "pull", "origin", "master"], blog_repo_path)

        logging.info("Master branch is now up to date.")
        return True
    else:
        logging.error(f"Failed to merge PR #{pr_number}: {merge_response.json()}")
        return False