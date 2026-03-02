import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from datetime import datetime, timezone, timedelta
import csv
import io

class VCLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Store DB in the data folder
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'vclogs.db')
        self.ensure_db()

    def ensure_db(self):
        """Creates the database table if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS voice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                guild_id INTEGER,
                guild_name TEXT,
                channel_id INTEGER,
                channel_name TEXT,
                join_time TIMESTAMP,
                leave_time TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Listens for voice state changes to log joins/leaves."""
        # Ignore bots if you want, but for auditing usually we keep them.
        # if member.bot: return

        timestamp = datetime.now(timezone.utc)

        # Case 1: Join (before.channel is None, after.channel is set)
        if before.channel is None and after.channel is not None:
            self.log_join(member, after.channel, timestamp)
        
        # Case 2: Leave (before.channel is set, after.channel is None)
        elif before.channel is not None and after.channel is None:
            self.log_leave(member, before.channel, timestamp)

        # Case 3: Move (both set, different channels)
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            # Treat move as leaving old channel and joining new one
            self.log_leave(member, before.channel, timestamp)
            self.log_join(member, after.channel, timestamp)

    def log_join(self, member, channel, timestamp):
        """Inserts a new session record."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO voice_sessions (user_id, username, guild_id, guild_name, channel_id, channel_name, join_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (member.id, member.name, member.guild.id, member.guild.name, channel.id, channel.name, timestamp))
            conn.commit()
            conn.close()
            print(f"[VC Log] {member.name} joined {channel.name} in {member.guild.name}")
        except Exception as e:
            print(f"[VC Log Error] Failed to log join: {e}")

    def log_leave(self, member, channel, timestamp):
        """Updates the leave time for the open session."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            # Find the most recent open session for this user in this channel
            c.execute('''
                SELECT id FROM voice_sessions 
                WHERE user_id = ? AND channel_id = ? AND leave_time IS NULL
                ORDER BY join_time DESC
                LIMIT 1
            ''', (member.id, channel.id))
            row = c.fetchone()
            
            if row:
                session_id = row[0]
                c.execute('''
                    UPDATE voice_sessions 
                    SET leave_time = ? 
                    WHERE id = ?
                ''', (timestamp, session_id))
                conn.commit()
                print(f"[VC Log] {member.name} left {channel.name} in {member.guild.name}")
            else:
                print(f"[VC Log] {member.name} left {channel.name} but no open session found (Bot restart?).")
            
            conn.close()
        except Exception as e:
            print(f"[VC Log Error] Failed to log leave: {e}")

    @app_commands.command(name="export_vclogs", description="Export voice chat logs as CSV")
    @app_commands.describe(user="Filter by user (optional)", days="Number of days to look back (default 7)")
    async def export_vclogs(self, interaction: discord.Interaction, user: discord.User = None, days: int = 7):
        """Exports the VC logs to a CSV file."""
        # Check perms (isAdmin)
        if not any(role.name == "isAdmin" for role in interaction.user.roles):
            await interaction.response.send_message("🚫 You need the 'isAdmin' role to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Calculate cutoff date
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = "SELECT guild_name, username, channel_name, join_time, leave_time FROM voice_sessions WHERE join_time > ?"
            params = [cutoff]
            
            if user:
                query += " AND user_id = ?"
                params.append(user.id)
                
            query += " ORDER BY join_time DESC"
            
            c.execute(query, tuple(params))
            rows = c.fetchall()
            conn.close()
            
            if not rows:
                await interaction.followup.send("No logs found for this criteria.")
                return

            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Server", "User", "Channel", "Join Time (UTC)", "Leave Time (UTC)", "Duration"])
            
            for guild_name, username, channel_name, join_str, leave_str in rows:
                duration = "Active"
                
                # Helper to parse timestamp strings from SQLite
                def parse_ts(ts_val):
                    if isinstance(ts_val, datetime): return ts_val
                    if not ts_val: return None
                    try:
                        return datetime.fromisoformat(ts_val)
                    except ValueError:
                        # Fallback for some sqlite formats
                        return datetime.strptime(ts_val.split('.')[0], "%Y-%m-%d %H:%M:%S")

                join_dt = parse_ts(join_str)
                leave_dt = parse_ts(leave_str)

                if join_dt and leave_dt:
                    diff = leave_dt - join_dt
                    duration = str(diff).split('.')[0] # Remove microseconds

                writer.writerow([guild_name, username, channel_name, join_str, leave_str, duration])
                
            output.seek(0)
            file = discord.File(fp=io.BytesIO(output.getvalue().encode('utf-8')), filename=f"vclogs_{days}d.csv")
            await interaction.followup.send(f"Here are the VC logs for the last {days} days:", file=file)
            
        except Exception as e:
            await interaction.followup.send(f"Failed to export logs: {e}")
            print(e)

    @app_commands.command(name="myvclogs", description="View your own voice chat logs for the last 7 days")
    async def my_vclogs(self, interaction: discord.Interaction):
        """Shows the user their own VC logs for the last 7 days."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Calculate cutoff date (7 days ago)
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            
            query = "SELECT channel_name, join_time, leave_time FROM voice_sessions WHERE user_id = ? AND join_time > ? ORDER BY join_time DESC"
            c.execute(query, (interaction.user.id, cutoff))
            rows = c.fetchall()
            conn.close()
            
            if not rows:
                await interaction.followup.send("No voice logs found for you in the last 7 days.", ephemeral=True)
                return

            # Format output
            output_lines = [f"**Your Voice Logs (Last 7 Days)**"]
            
            for channel_name, join_str, leave_str in rows:
                # Helper to parse timestamp
                def parse_ts(ts_val):
                    if isinstance(ts_val, datetime): return ts_val
                    if not ts_val: return None
                    try:
                        return datetime.fromisoformat(ts_val)
                    except ValueError:
                        return datetime.strptime(ts_val.split('.')[0], "%Y-%m-%d %H:%M:%S")

                join_dt = parse_ts(join_str)
                leave_dt = parse_ts(leave_str)
                
                # Format dates for display
                join_fmt = join_dt.strftime("%Y-%m-%d %H:%M") if join_dt else "Unknown"
                
                duration = "Active"
                if join_dt and leave_dt:
                    diff = leave_dt - join_dt
                    # Format duration nicely
                    total_seconds = int(diff.total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m {seconds}s"

                output_lines.append(f"• **{channel_name}**: {join_fmt} ({duration})")

            full_text = "\n".join(output_lines)
            
            if len(full_text) > 1950:
                # Send as file if too long
                file = discord.File(fp=io.BytesIO(full_text.encode('utf-8')), filename="my_vclogs.txt")
                await interaction.followup.send("Your logs are too long to display here. See attached file.", file=file, ephemeral=True)
            else:
                await interaction.followup.send(full_text, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Failed to retrieve logs: {e}", ephemeral=True)
            print(e)

async def setup(bot):
    await bot.add_cog(VCLogger(bot))
