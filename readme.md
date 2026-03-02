# AGSHelperBot (formerly DeathBot)

AGSHelperBot is a general-purpose Discord helper bot designed to assist with administrative tasks, backups, moderation, reporting, and more.

## 1. Project Structure

The project has been reorganized for better maintainability and deployment:

```
.
├── data/                   # Stores SQLite databases (reports.db, requests.db, statuses.db, vclogs.db)
├── src/
│   ├── cogs/               # Feature modules
│   │   ├── backup.py       # Google Drive Backup
│   │   ├── general.py      # Basic commands
│   │   ├── moderation.py   # Cleanup tools
│   │   ├── reporting.py    # Daily reporting
│   │   ├── requests.py     # Bug reports & feature requests
│   │   ├── status.py       # AFK/Status management
│   │   └── vclogger.py     # Voice channel logging
│   └── main.py             # Entry point
├── .env                    # Secrets (Token, Folder IDs)
├── .env.example            # Template for secrets
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
└── service_account.json    # Google Drive API credentials (optional if using env var)
```

## 2. Deployment (Coolify / Docker)

This bot is containerized using Docker, making it easy to deploy on Coolify or any VPS.

### Prerequisites
1.  **Discord Bot Token**: Get this from the Discord [Developer Portal](https://discord.com/developers/applications).
2.  **Google Drive Service Account**: Required for backups (see section 5).

### Setup Steps
1.  **Environment Variables**:
    Create a `.env` file (use `.env.example` as a guide) with:
    ```env
    DISCORD_TOKEN=your_discord_token
    BACKUP_ROOT_FOLDER_ID=your_google_drive_folder_id
    # Optional: If you don't want to use a file for credentials
    GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...} 
    ```

2.  **Google Drive Credentials**:
    *   **Option A (File)**: Place your `service_account.json` file in the root directory.
    *   **Option B (Env Var)**: Paste the content of the JSON file into the `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable (useful for cloud deployment).

3.  **Deploying on Coolify**:
    *   Connect your repository to Coolify.
    *   Select **Dockerfile** as the build pack.
    *   **Persistent Storage**: Map `/app/data` to a persistent volume so databases are not lost on redeploys.
    *   **Secrets**: Add `DISCORD_TOKEN`, `BACKUP_ROOT_FOLDER_ID`, and optionally `GOOGLE_SERVICE_ACCOUNT_JSON`.

### Running Locally (Docker Compose)
```bash
docker-compose up -d --build
```

## 3. Features & Usage

### 🛠 General & Moderation
*   **!ping**: Checks bot latency.
*   **!hello**: Simple greeting.
*   **Cleanup**: `/cleanup [amount]` (Admin only) - Bulk deletes messages.

### 💾 Backup System
Back up text channels, threads, and categories to Google Drive. Captures messages, timestamps, and attachments (images/files).
*   **Requirements**: User must have the `hasBotPerms` role.
*   **Commands**:
    *   `/backup thread [since]`: Backup the current thread (or specify one).
    *   `/backup channel [since]`: Backup the current channel.
    *   `/backup category [since]`: Backup the category the channel is in.
    *   `/backup server [since]` (Admin only): Backup the entire server structure.
    *   **Arg `since`**: Time duration like `7d` (7 days), `24h` (24 hours), `2w` (2 weeks). Leaving it empty backs up everything.

### 📝 Daily Reporting
Log daily work activities and blockers. Useful for team standups.
*   **Commands**:
    *   `/daily_report`: Opens a form to submit "Activity" and "Blockers".
    *   `/my_history`: View your last 5 reports.
    *   `/lead_view [user]`: View reports for a specific user.
    *   `/lead_export [user] [days]`: Export reports to CSV.

### 📋 Request & Bug Tracking
A built-in ticketing system for bugs, feature requests, and ideas.
*   **Commands**:
    *   `/bug_report`: Submit a bug report.
    *   `/feature_request`: Request a new feature.
    *   `/idea_suggest`: Submit a general idea.
    *   **Management (Admins)**:
        *   `/show_bugs`, `/show_features`, `/show_ideas`: List all open requests.
        *   `/show_request [id]`: View details of a specific request (e.g., BUG-1).
        *   `/update_status [id] [status]`: Change status (Untouched, In Progress, Complete, etc.).

### 🚦 Status System
Let others know your current availability.
*   **Commands**:
    *   `/afk`: Set status to "Away".
    *   `/locked-in`: Set status to "Busy Focusing".
    *   `/back`: Reset status to "Active".
    *   `/status [user]`: Check someone's current status.

### 🎙 Voice Channel Logger
Tracks when users join and leave voice channels for auditing.
*   **Commands**:
    *   `/myvclogs`: View your voice sessions for the last 7 days.
    *   `/export_vclogs [days]`: Export all voice logs to CSV (Admin only).

## 4. Permissions

*   **hasBotPerms**: Role required for Backup commands and viewing Request lists.
*   **isAdmin**: Role required for full Server Backup.

## 5. Google Drive Setup (For Backups)

1.  **Create a Google Cloud Project**: [Google Cloud Console](https://console.cloud.google.com/).
2.  **Enable Drive API**: Search for "Google Drive API" and enable it.
3.  **Create Service Account**:
    *   Credentials -> Create Credentials -> Service Account.
    *   Name it (e.g., "AGSHelper Backup").
4.  **Get Key**:
    *   Click Service Account email -> Keys -> Add Key -> JSON.
    *   Save as `service_account.json` or use the content for the `GOOGLE_SERVICE_ACCOUNT_JSON` env var.
5.  **Share Folder**:
    *   Create a folder in Google Drive.
    *   Share it with the **Service Account email** (Editor access).
    *   Copy the Folder ID from the URL into `.env` as `BACKUP_ROOT_FOLDER_ID`.
