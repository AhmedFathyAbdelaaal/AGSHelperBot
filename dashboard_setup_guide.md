# Deployment Guide: Coolify & Hostinger

To get your new dashboard live at `dash.captionato.cloud` (or `captionato.cloud`), follow these steps carefully. You will be configuring the DNS on Hostinger and the routing/deployment on Coolify.

## Phase 1: Hostinger (DNS Setup)
You need to tell the internet that your domain points to your Coolify VPS.

1. **Log into Hostinger**: Go to your hPanel.
2. **Manage Domain**: Find `captionato.cloud` and click **Manage**.
3. **DNS / Nameservers**: Navigate to the DNS Zone Editor.
4. **Create an A Record**:
   * **Type**: `A`
   * **Name**: `@` (if you want the root `captionato.cloud`) OR `dash` (if you want `dash.captionato.cloud`).
   * **Points to**: `[Your Coolify VPS IP Address]` (e.g., 123.45.67.89).
   * **TTL**: Leave as default (Usually 14400 or 3600).
5. **Save**: Click Add Record. (Note: DNS changes can take a few minutes to propagate).

## Phase 2: Coolify (Project Setup)
Since you added a new service (`dashboard`) to your `docker-compose.yml`, Coolify needs to be updated to recognize and route traffic to it.

1. **Log into Coolify**: Go to your Coolify dashboard.
2. **Open Your Project**: Go to the Project and Environment where `AGSHelperBot` is currently deployed.
3. **Resync / Redeploy**: 
   * Go to your repository settings in Coolify and hit **Deploy** or **Force Redeploy**.
   * Because you are using a Git repository and `docker-compose.yml`, Coolify will read the updated file and automatically spin up the second container (`ags_dashboard`).
4. **Configure the Dashboard Container**:
   * Once the deployment finishes, you should see two resources under your project: the Bot and the Dashboard.
   * Click on the **Dashboard** resource.
5. **Set the Domain (Traefik / Traefik Proxy)**:
   * In the Dashboard resource settings, find the **Domains** field.
   * Enter your domain exactly as you set it up in Hostinger.
     * Example: `https://captionato.cloud` OR `https://dash.captionato.cloud`
   * Coolify will automatically provision an SSL certificate (Let's Encrypt) and route HTTP/HTTPS traffic to this domain.
6. **Double Check Ports**:
   * Ensure that the internal port is set to `3000` (this matches the `port: 3000` we set for Uvicorn in the Dockerfile).

## Phase 3: Verify the Shared Volume (Crucial)
You need to make sure the Bot and the Dashboard are looking at the exact same SQLite files.

1. **Go to Bot Resource in Coolify**:
   * Under **Storage / Volumes**, ensure your `/app/data` is mapped to a persistent volume (e.g., `ags_data_volume:/app/data`).
2. **Go to Dashboard Resource in Coolify**:
   * Under **Storage / Volumes**, it *must* use the exact same persistent volume source mapped to `/app/data`.
   * *If the Dashboard creates an empty database, it's because it's not looking at the bot's volume.* 

## Recap of the Architecture
* `captionato.cloud` → Hostinger DNS → Coolify VPS IP
* Coolify VPS (Traefik) receives request for `captionato.cloud` → Routes to Port `3000` of `ags_dashboard`
* `ags_dashboard` FastApi serves Angular static files.
* Angular calls `/api/status` → FastAPI reads from `/app/data/statuses.db` (which the Discord bot is actively writing to).
