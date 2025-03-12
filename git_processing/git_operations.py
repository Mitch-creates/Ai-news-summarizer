import os
import subprocess
import time
import requests

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
            print(f"Git command failed: {command} -> {stderr.strip()}")
            return False

        return stdout.strip()  # Return command output if successful

    except Exception as e:
        print(f"Error running Git command {command}: {e}")
        return False

def check_git_changes(repo_path):
    """Check if there are any uncommitted changes in the repository."""
    status_output = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
    return bool(status_output.stdout.strip())

def commit_and_push_to_github(BlogpostDTO):
    """Commits a blog post and pushes it to `develop`, creating a PR if necessary."""
    slug = BlogpostDTO.blogpost_metadata.slug
    file_path = BlogpostDTO.markdown_file_path
    commit_message = f"Publish new AI Weekly Summary blogpost: {slug}"

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    repo_url = os.getenv("BLOG_REPOSITORY_URL_HTTPS")
    blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH")
    OWNER = os.getenv("OWNER")
    OWNER_EMAIL = os.getenv("OWNER_EMAIL")
    REPO = os.getenv("REPO_NAME")

    print(f"Blog repository path: {blog_repo_path}")

    run_git_command(['git', 'config', '--global', 'user.name', OWNER], blog_repo_path)
    run_git_command(['git', 'config', '--global', 'user.email', OWNER_EMAIL], blog_repo_path)

    repo_url_with_token = repo_url.replace("https://", f"https://{GITHUB_TOKEN}@")
    run_git_command(['git', 'remote', 'set-url', 'origin', repo_url_with_token], blog_repo_path)

    # Stash any local changes before switching branches
    if check_git_changes(blog_repo_path):
        print("Uncommitted changes detected! Stashing changes before switching branches.")
        run_git_command(["git", "stash"], blog_repo_path)

    run_git_command(["git", "checkout", "develop"], blog_repo_path)
    run_git_command(["git", "pull", "origin", "develop"], blog_repo_path)

    # After pulling changes, restore stashed changes if necessary
    if "No local changes to save" not in run_git_command(["git", "stash", "list"], blog_repo_path):
        print("Restoring stashed changes...")
        run_git_command(["git", "stash", "pop"], blog_repo_path)

    if not check_git_changes(blog_repo_path):
        print("No new changes detected. Skipping commit.")
        return None

    run_git_command(['git', 'add', file_path], blog_repo_path)
    run_git_command(['git', 'commit', '--allow-empty', '-m', commit_message], blog_repo_path)
    run_git_command(['git', 'push', "origin", "develop"], blog_repo_path)

    print(f"Successfully pushed changes to {repo_url}")

    existing_pr_number = check_existing_pr()
    if existing_pr_number:
        print(f"Existing PR found: #{existing_pr_number}. Attempting to merge...")
        return existing_pr_number

    return create_pull_request(slug)

def check_existing_pr():
    """Checks if there's already an open PR from `develop` to `master`."""
    OWNER = os.getenv("OWNER")
    REPO = os.getenv("REPO_NAME")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls?state=open"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to check existing PRs: {response.json()}")
        return None

    for pr in response.json():
        if pr["head"]["ref"] == "develop" and pr["base"]["ref"] == "master":
            return pr["number"]

    return None

def create_pull_request(slug):
    """Creates a new PR from `develop` to `master`."""
    OWNER = os.getenv("OWNER")
    REPO = os.getenv("REPO_NAME")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {
        "title": f"Merge develop into master - {slug}",
        "head": "develop",
        "base": "master",
        "body": f"Automated PR for {slug}"
    }

    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 201:
        pr_number = response.json().get("number")
        print(f"Pull request created successfully! PR number: {pr_number}")
        return pr_number
    else:
        print(f"Failed to create pull request: {response.json()}")
        return None

def merge_pull_request(pr_number):
    """Merges an open PR (`develop` → `master`)."""
    if pr_number is None:
        print("No valid PR found. Cannot merge.")
        return

    REPO = os.getenv("REPO_NAME")
    OWNER = os.getenv("OWNER")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    blog_repo_path = os.getenv("BLOG_REPOSITORY_PATH")

    pr_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    pr_response = requests.get(pr_url, headers=headers)
    pr_data = pr_response.json()

    attempts = 0
    while pr_data.get("mergeable_state") == "unknown" and attempts < 10:
        print("Waiting for GitHub to calculate mergeability...")
        time.sleep(10)
        pr_response = requests.get(pr_url, headers=headers)
        pr_data = pr_response.json()
        attempts += 1

    if pr_data.get("mergeable"):
        merge_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}/merge"
        merge_payload = {"commit_message": f"Auto-merging PR #{pr_number}"}
        merge_response = requests.put(merge_url, json=merge_payload, headers=headers)

        if merge_response.status_code == 200:
            print("Pull request merged successfully!")

            if check_git_changes(blog_repo_path):
                print("Uncommitted changes detected! Stashing changes before switching branches.")
                run_git_command(["git", "stash"], blog_repo_path)

            run_git_command(["git", "checkout", "master"], blog_repo_path)
            run_git_command(["git", "pull", "origin", "master"], blog_repo_path)

            if "No local changes to save" not in run_git_command(["git", "stash", "list"], blog_repo_path):
                print("Restoring stashed changes...")
                run_git_command(["git", "stash", "pop"], blog_repo_path)

            print("Master branch is up to date after PR merge.")
            return
        else:
            print(f"Failed to merge PR: {merge_response.json()}")

    print(f"PR cannot be merged due to: {pr_data.get('mergeable_state')}. Attempting force merge...")

    if check_git_changes(blog_repo_path):
        print("Uncommitted changes detected! Stashing changes before switching branches.")
        run_git_command(["git", "stash"], blog_repo_path)

    run_git_command(["git", "checkout", "master"], blog_repo_path)
    run_git_command(["git", "pull", "--rebase", "origin", "master"], blog_repo_path)

    # After pulling changes, restore stashed changes if necessary
    if "No local changes to save" not in run_git_command(["git", "stash", "list"], blog_repo_path):
        print("Restoring stashed changes...")
        run_git_command(["git", "stash", "pop"], blog_repo_path)

    status_output = subprocess.run(["git", "diff", "master", "develop"], cwd=blog_repo_path, capture_output=True, text=True, encoding="utf-8")
    if status_output.stdout is None or not status_output.stdout.strip():
        print("No new changes to merge. Skipping force merge.")
        return

    run_git_command(["git", "merge", "--no-edit", "-X", "theirs", "develop"], blog_repo_path)
    run_git_command(["git", "push", "origin", "master"], blog_repo_path)

    print("Successfully force-merged `develop` into `master`.")
