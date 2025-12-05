# AGSHelperBot (formerly DeathBot)

AGSHelperBot is a general-purpose Discord helper bot designed to assist with administrative tasks, backups, moderation, and reporting.

## 1. Project Structure

The project has been reorganized for better maintainability and deployment:

```
.
├── data/                   # Stores the SQLite database (reports.db)
├── src/
│   ├── cogs/               # Feature modules (Backup, General, Moderation, Reporting)
│   │   ├── backup.py
│   │   ├── general.py
│   │   ├── moderation.py
│   │   └── reporting.py
│   └── main.py             # Entry point
├── .env                    # Secrets (Token, Folder IDs)
├── .env.example            # Template for secrets
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
└── service_account.json    # Google Drive API credentials (you need to provide this)
```

## 2. Deployment (Coolify / Docker)

This bot is containerized using Docker, making it easy to deploy on Coolify or any VPS.

### Prerequisites
1.  **Discord Bot Token**: Get this from the Discord Developer Portal.
2.  **Google Drive Service Account**: Required for backups (see section 4).

### Setup Steps
1.  **Environment Variables**:
    Create a `.env` file (use `.env.example` as a guide) with:
    ```env
    DISCORD_TOKEN=your_discord_token
    BACKUP_ROOT_FOLDER_ID=your_google_drive_folder_id
    ```

2.  **Google Drive Credentials**:
    Place your `service_account.json` file in the root directory.

3.  **Deploying on Coolify**:
    *   Connect your repository to Coolify.
    *   Select **Dockerfile** as the build pack.
    *   **Persistent Storage**: You should map the `/app/data` directory to a persistent volume so your database isn't lost on redeploys.
    *   **Secrets**: Add your `DISCORD_TOKEN` and `BACKUP_ROOT_FOLDER_ID` in the Coolify environment variables section.
    *   **Service Account**: You might need to mount `service_account.json` as a secret file or config file at `/app/service_account.json`.

### Running Locally (Docker Compose)
```bash
docker-compose up -d --build
```

## 3. Features (Cogs)

*   **General**: Basic commands (`!ping`, `!hello`).
*   **Backup**: Back up channels, threads, and categories to Google Drive.
*   **Moderation**: Bulk delete messages.
*   **Reporting**: Daily reporting system with SQLite database.

## 4. Google Drive Setup (Required for Backup)

1.  **Create a Google Cloud Project**: Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  **Enable Drive API**: Search for "Google Drive API" and enable it.
3.  **Create Service Account**:
    *   Go to "Credentials" -> "Create Credentials" -> "Service Account".
    *   Name it (e.g., "AGSHelper Backup").
    *   Click "Done".
4.  **Get Key**:
    *   Click on the Service Account email -> "Keys" -> "Add Key" -> "Create new key" -> "JSON".
    *   Rename the downloaded file to `service_account.json` and place it in the project root.
5.  **Share Folder**:
    *   Create a folder in your Google Drive.
    *   Share it with the **Service Account email** (give Editor access).
    *   Copy the Folder ID from the URL and put it in your `.env` as `BACKUP_ROOT_FOLDER_ID`.
