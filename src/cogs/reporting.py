import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from datetime import datetime, timezone, timedelta
import csv
import io

# DB Path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'reports.db')

class ReportModal(discord.ui.Modal, title="Submit Daily Report"):
    activity = discord.ui.TextInput(
        label="Activity/Report",
        style=discord.TextStyle.paragraph,
        placeholder="What did you work on today?",
        required=True,
        max_length=2000
    )
    
    blockers = discord.ui.TextInput(
        label="Blockers/Notes",
        style=discord.TextStyle.short,
        placeholder="Any issues blocking you?",
        required=False,
        max_length=1000
    )

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = interaction.user.name
        guild_id = interaction.guild_id
        content_main = self.activity.value
        content_notes = self.blockers.value
        # Store as UTC timestamp
        timestamp = datetime.now(timezone.utc)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO reports (user_id, username, content_main, content_notes, timestamp, guild_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, content_main, content_notes, timestamp, guild_id))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"✅ Report saved for {timestamp.strftime('%Y-%m-%d')}!", ephemeral=True)

class Reporting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = DB_PATH
        self.ensure_db()

    def ensure_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                content_main TEXT,
                content_notes TEXT,
                timestamp DATETIME
            )
        ''')
        
        # Migration: Add guild_id if it doesn't exist
        c.execute("PRAGMA table_info(reports)")
        columns = [info[1] for info in c.fetchall()]
        if 'guild_id' not in columns:
            try:
                c.execute("ALTER TABLE reports ADD COLUMN guild_id INTEGER")
                print("Migrated DB: Added guild_id column.")
            except Exception as e:
                print(f"Migration failed: {e}")

        conn.commit()
        conn.close()

    async def check_lead_perms(self, interaction: discord.Interaction) -> bool:
        # Check for "Lead", "Leadership", "Admin", or "isAdmin" roles
        allowed_roles = ["Lead", "Leadership", "Admin", "isAdmin"]
        if any(role.name in allowed_roles for role in interaction.user.roles):
            return True
        await interaction.response.send_message("🚫 You need a Leadership role to use this command.", ephemeral=True)
        return False

    def parse_timestamp(self, ts_str):
        """Parses timestamp string from SQLite into a datetime object."""
        try:
            # Try ISO format first
            return datetime.fromisoformat(ts_str)
        except ValueError:
            # Fallback for common SQLite string formats
            try:
                # Format: YYYY-MM-DD HH:MM:SS.ssssss
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    # Format: YYYY-MM-DD HH:MM:SS
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # Format: YYYY-MM-DD HH:MM:SS+00:00
                    ts = datetime.strptime(ts_str.split('+')[0], "%Y-%m-%d %H:%M:%S.%f")
            
            # Assume UTC if no tzinfo
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts

    def to_cet(self, utc_dt):
        """Converts UTC datetime to CET (UTC+1)."""
        return utc_dt.astimezone(timezone(timedelta(hours=1)))

    @app_commands.command(name="daily_report", description="Submit your daily report")
    async def daily_report(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReportModal(self.db_path))

    @app_commands.command(name="my_history", description="View your last 5 reports")
    async def my_history(self, interaction: discord.Interaction):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT content_main, content_notes, timestamp FROM reports WHERE user_id = ? AND guild_id = ? ORDER BY timestamp DESC LIMIT 5', (interaction.user.id, interaction.guild_id))
        rows = c.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message("No reports found.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Report History: {interaction.user.name}", color=discord.Color.blue())
        for main, notes, ts_str in rows:
            ts = self.parse_timestamp(ts_str)
            cet_ts = self.to_cet(ts)
            
            val = f"**Activity:** {main}"
            if notes:
                val += f"\n**Notes:** {notes}"
            embed.add_field(name=cet_ts.strftime("%Y-%m-%d %H:%M CET"), value=val, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="lead_view", description="View reports for a specific user")
    @app_commands.describe(user="The user to view")
    async def lead_view(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_lead_perms(interaction):
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT content_main, content_notes, timestamp FROM reports WHERE user_id = ? AND guild_id = ? ORDER BY timestamp DESC LIMIT 5', (user.id, interaction.guild_id))
        rows = c.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message(f"No reports found for {user.name}.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Report History: {user.name}", color=discord.Color.green())
        for main, notes, ts_str in rows:
            ts = self.parse_timestamp(ts_str)
            cet_ts = self.to_cet(ts)
            
            val = f"**Activity:** {main}"
            if notes:
                val += f"\n**Notes:** {notes}"
            embed.add_field(name=cet_ts.strftime("%Y-%m-%d %H:%M CET"), value=val, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="lead_export", description="Export reports for a user within a date range")
    @app_commands.describe(user="The user to export", start="Start date (DD/MM)", end="End date (DD/MM)")
    async def lead_export(self, interaction: discord.Interaction, user: discord.Member, start: str, end: str):
        if not await self.check_lead_perms(interaction):
            return

        # Parse dates
        try:
            current_year = datetime.now().year
            # Parse as UTC for DB query
            start_dt = datetime.strptime(f"{start}/{current_year}", "%d/%m/%Y").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(f"{end}/{current_year}", "%d/%m/%Y").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            await interaction.response.send_message("Invalid date format. Please use DD/MM.", ephemeral=True)
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # We need to be careful with string comparison of dates in SQLite if formats vary, 
        # but since we insert using datetime.now(timezone.utc), it should be consistent ISO format.
        # However, to be safe, we can fetch more and filter in python or rely on ISO string comparison.
        # Let's rely on ISO string comparison which works for YYYY-MM-DD HH:MM:SS...
        
        c.execute('''
            SELECT timestamp, content_main, content_notes 
            FROM reports 
            WHERE user_id = ? AND guild_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        ''', (user.id, interaction.guild_id, start_dt, end_dt))
        rows = c.fetchall()
        conn.close()

        if not rows:
            await interaction.response.send_message("No reports found in that range.", ephemeral=True)
            return

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date (CET)", "Activity", "Notes"])

        for ts_str, main, notes in rows:
            ts = self.parse_timestamp(ts_str)
            cet_ts = self.to_cet(ts)
            writer.writerow([cet_ts.strftime("%Y-%m-%d %H:%M"), main, notes])

        output.seek(0)
        file = discord.File(fp=io.BytesIO(output.getvalue().encode('utf-8')), filename=f"reports_{user.name}_{start.replace('/','-')}_to_{end.replace('/','-')}.csv")
        
        await interaction.response.send_message(f"Export for {user.name}:", file=file, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reporting(bot))
