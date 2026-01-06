import os
import subprocess
from pathlib import Path
import requests
import time
import argparse
from dotenv import load_dotenv
from tqdm import tqdm


def get_github_repos(token: str, verbose: bool = False) -> list[dict]:
    """Fetch all repos the authenticated user has access to."""
    if verbose:
        print("[VERBOSE] Preparing GitHub API request...")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    repos = []
    page = 1
    per_page = 100

    print("Fetching repository list from GitHub...")

    while True:
        # Get repos user owns or has access to
        url = f"https://api.github.com/user/repos?page={page}&per_page={per_page}&affiliation=owner,collaborator,organization_member"

        if verbose:
            print(f"[VERBOSE] Requesting page {page} from GitHub API...")

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"GitHub API error: {response.status_code} - {response.text}"
            )

        page_repos = response.json()
        if not page_repos:
            if verbose:
                print(
                    f"[VERBOSE] No more repos found on page {page}, stopping pagination"
                )
            break

        repos.extend(page_repos)
        print(f"  Found {len(repos)} repositories so far...")
        page += 1

        # Be nice to the API
        if verbose:
            print(f"[VERBOSE] Sleeping 0.5s before next request...")
        time.sleep(0.5)

    return repos


def clone_or_update_repo(
    repo_data: dict, base_dir: Path, token: str, verbose: bool = False, pbar=None
) -> bool:
    """Clone a repo if it doesn't exist, or pull updates if it does."""
    repo_name = repo_data["full_name"]  # e.g., "username/repo-name"
    clone_url = repo_data["clone_url"]

    # Inject token into HTTPS URL for authentication
    # Format: https://TOKEN@github.com/user/repo.git
    authenticated_url = clone_url.replace("https://", f"https://{token}@")

    # Create nested directory structure (username/repo-name)
    repo_path = base_dir / repo_name

    if verbose:
        tqdm.write(f"[VERBOSE] Repository: {repo_name}")
        tqdm.write(f"[VERBOSE] Clone URL: {clone_url}")
        tqdm.write(f"[VERBOSE] Target path: {repo_path}")
        tqdm.write(f"[VERBOSE] Using authenticated URL for git operations")

    try:
        if repo_path.exists():
            if verbose:
                tqdm.write(
                    f"[VERBOSE] Repository exists at {repo_path}, performing git pull..."
                )
            if pbar:
                pbar.set_description(f"Updating {repo_name}")
            result = subprocess.run(
                ["git", "-C", str(repo_path), "pull"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if verbose:
                tqdm.write(f"[VERBOSE] Git pull exit code: {result.returncode}")
                if result.stdout:
                    tqdm.write(f"[VERBOSE] Git stdout: {result.stdout.strip()}")
                if result.stderr:
                    tqdm.write(f"[VERBOSE] Git stderr: {result.stderr.strip()}")

            if result.returncode != 0:
                tqdm.write(f"Failed to update {repo_name}: {result.stderr.strip()}")
                return False
        else:
            if verbose:
                tqdm.write(
                    f"[VERBOSE] Repository does not exist, performing git clone..."
                )
                tqdm.write(f"[VERBOSE] Creating parent directory: {repo_path.parent}")
            if pbar:
                pbar.set_description(f"Cloning {repo_name}")
            # Create parent directory if needed
            repo_path.parent.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                ["git", "clone", authenticated_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if verbose:
                tqdm.write(f"[VERBOSE] Git clone exit code: {result.returncode}")
                if result.stdout:
                    tqdm.write(f"[VERBOSE] Git stdout: {result.stdout.strip()}")
                if result.stderr:
                    tqdm.write(f"[VERBOSE] Git stderr: {result.stderr.strip()}")

            if result.returncode != 0:
                tqdm.write(f"Failed to clone {repo_name}: {result.stderr.strip()}")
                return False

        return True

    except subprocess.TimeoutExpired:
        if verbose:
            tqdm.write(f"[VERBOSE] Git operation timed out after 300 seconds")
        tqdm.write(f"Timeout for {repo_name}")
        return False
    except Exception as e:
        if verbose:
            tqdm.write(f"[VERBOSE] Exception occurred: {type(e).__name__}: {e}")
        tqdm.write(f"Error with {repo_name}: {e}")
        return False


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Back up all GitHub repositories")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    if args.verbose:
        print("[VERBOSE] Verbose mode enabled")

    # Load environment variables from .env file
    if args.verbose:
        print("[VERBOSE] Loading .env file...")
    load_dotenv()

    # Get GitHub token from environment
    if args.verbose:
        print("[VERBOSE] Reading GITHUB_TOKEN from environment...")
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in .env file or environment")
        print("Create a .env file with: GITHUB_TOKEN=your_token_here")
        return 1

    if args.verbose:
        print(f"[VERBOSE] Token found (length: {len(token)} characters)")

    # Configure base directory (default: ./repos)
    base_dir = Path(os.getenv("REPOS_DIR", "repos"))
    if args.verbose:
        print(f"[VERBOSE] Target directory: {base_dir.absolute()}")
        print(f"[VERBOSE] Creating directory if it doesn't exist...")
    base_dir.mkdir(exist_ok=True)

    print(f"Back-Git-Up - Backing up repositories to {base_dir.absolute()}\n")

    try:
        # Fetch all repos
        repos = get_github_repos(token, args.verbose)
        print(f"\nFound {len(repos)} total repositories\n")

        # Show list of repo names in verbose mode
        if args.verbose:
            print("[VERBOSE] Repository list:")
            for i, repo in enumerate(repos, 1):
                print(f"[VERBOSE]   {i}. {repo['full_name']}")
            print()

        if args.verbose:
            print("[VERBOSE] Starting clone/update process...")

        # Clone or update each repo
        success_count = 0
        fail_count = 0

        with tqdm(
            total=len(repos), desc="Processing repositories", unit="repo"
        ) as pbar:
            for repo in repos:
                if args.verbose:
                    tqdm.write(
                        f"\n[VERBOSE] ========== Processing {repo['full_name']} ==========="
                    )

                if clone_or_update_repo(repo, base_dir, token, args.verbose, pbar):
                    success_count += 1
                else:
                    fail_count += 1

                pbar.update(1)

        # Summary
        if args.verbose:
            print(f"\n[VERBOSE] Processing complete, generating summary...")
        print(f"\n{'='*60}")
        print(f"Successfully processed: {success_count}")
        if fail_count > 0:
            print(f"Failed: {fail_count}")
        print(f"{'='*60}")

        return 0 if fail_count == 0 else 1

    except Exception as e:
        if args.verbose:
            print(f"\n[VERBOSE] Fatal exception: {type(e).__name__}")
        print(f"\nFatal error: {e}")
        return 1


if __name__ == "__main__":
    while True:
        main()
        print("Sleeping for 24 hours before next backup...")
        one_day = 24 * 60 * 60
        time.sleep(one_day)
