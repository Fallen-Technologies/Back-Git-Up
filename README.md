# Back-Git-Up

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Back-Git-Up is an automated GitHub repository backup service that clones and keeps all your GitHub repositories synchronized to local storage. Every 24 hours, it automatically scans your GitHub account and backs up every repository you own or have access to, no manual intervention required.

Perfect for developers who want peace of mind knowing their code is safely backed up locally, whether it's personal projects, organization repositories, or collaborative work.

## Features

- **Automatic Daily Backups** - Runs every 24 hours to keep your local copies current
- **Multi-Repository Support** - Backs up all repositories you own or have access to (owner, collaborator, organization member)
- **Smart Updates** - Clones new repositories and pulls updates for existing ones
- **Organized Storage** - Preserves GitHub's `username/repo-name` directory structure
- **Docker Ready** - Fully containerized with persistent volume support

## Quick Start

### Prerequisites

- Docker (or Python 3.12+ for local setup)
- GitHub Personal Access Token with `repo` scope

### Docker Setup

Create a `.env` file:

```env
GITHUB_TOKEN=your_github_token_here
```

Docker Compose:

Create a `compose.yml` file:

```yaml
version: '3.8'

services:
  back-git-up:
    image: ghcr.io/fallen-technologies/back-git-up:latest
    container_name: back-git-up
    environment:
      GITHUB_TOKEN: your_github_token
    volumes:
      - ./repos:/app/repos
    restart: unless-stopped
```

Then run:

```bash
docker compose up -d
```

### Local Setup (Without Docker)

1. Install Python 3.12+
2. Install [uv](https://docs.astral.sh/uv/) (Astral's fast Python package manager)
3. Clone this repository
4. Create a `.env` file with your GitHub token:

```env
GITHUB_TOKEN=your_github_token_here
```

5. Sync dependencies:

```bash
uv sync
```

6. Run the script:

```bash
uv run python main.py
```

Add `-v` or `--verbose` flag for detailed output:

```bash
uv run python main.py -v
```

## Getting a GitHub Personal Access Token

1. Go to GitHub **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token** → **Generate new token (classic)**
3. Set a descriptive note (e.g., "Back-Git-Up Backup Service")
4. Select the `repo` scope (Full control of private repositories)
5. Click **Generate token**
6. Copy the token immediately (you won't be able to see it again)
7. Add it to your `.env` file as `GITHUB_TOKEN`


## How It Works

1. **Token Authentication** - Authenticates with GitHub using your personal access token
2. **Repository Discovery** - Fetches all repositories you own or have access to (owner, collaborator, organization member)
3. **Clone/Update** - For each repository:
   - If it doesn't exist locally: Clones it
   - If it already exists: Performs `git pull` to update
4. **Progress Display** - Shows a progress bar with current operation status
5. **Summary Report** - Reports total repositories processed, successes, and failures
6. **Sleep** - Waits 24 hours before repeating the process

## Directory Structure

Repositories are organized in the same structure as GitHub:

```
repos/
├── username/
│   ├── repo1/
│   ├── repo2/
│   └── repo3/
├── organization1/
│   └── repo4/
└── organization2/
    ├── repo5/
    └── repo6/
```

## Verbose Mode

Run with `-v` or `--verbose` flag to see detailed debugging information:

```bash
python main.py --verbose
```

This outputs:
- API request details
- Git operation commands and output
- File system operations
- Detailed error messages and stack traces

## Support

Need help? Submit a ticket on our community Discord:

[![Discord](https://img.shields.io/badge/Discord-%237289DA.svg?logo=discord&logoColor=white)](https://discord.fallenservers.com)
