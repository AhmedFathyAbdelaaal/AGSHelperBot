import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import datetime

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Path to the database file: AGSHelperBot/data/statuses.db
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'statuses.db')
        self.init_db()

    def init_db(self):
        """Initialize the database and create the table if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_status
                     (user_id INTEGER PRIMARY KEY, status TEXT, timestamp TEXT)''')
        conn.commit()
        conn.close()

    def set_status(self, user_id, status):
        """Set or update the status for a user."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        c.execute('''INSERT OR REPLACE INTO user_status (user_id, status, timestamp)
                     VALUES (?, ?, ?)''', (user_id, status, timestamp))
        conn.commit()
        conn.close()

    def get_status(self, user_id):
        """Retrieve the status for a user."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT status FROM user_status WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else "Active"

    @app_commands.command(name="afk", description="Set your status to Away")
    async def afk(self, interaction: discord.Interaction):
        self.set_status(interaction.user.id, "Away")
        await interaction.response.send_message(f"✅ {interaction.user.mention} is now **Away**.", ephemeral=False)

    @app_commands.command(name="locked-in", description="Set your status to Busy Focusing")
    async def locked_in(self, interaction: discord.Interaction):
        self.set_status(interaction.user.id, "Busy Focusing")
        await interaction.response.send_message(f"🔒 {interaction.user.mention} is now **Locked In** (Busy Focusing).", ephemeral=False)

    @app_commands.command(name="back", description="Reset your status to Active")
    async def back(self, interaction: discord.Interaction):
        self.set_status(interaction.user.id, "Active")
        await interaction.response.send_message(f"👋 {interaction.user.mention} is **Back** (Active).", ephemeral=False)

    @app_commands.command(name="status", description="Check the status of a user")
    async def status(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        status_text = self.get_status(target_user.id)
        
        color = discord.Color.green()
        if status_text == "Away":
            color = discord.Color.orange()
        elif status_text == "Busy Focusing":
            color = discord.Color.red()

        embed = discord.Embed(title=f"Status: {target_user.display_name}", color=color)
        if target_user.avatar:
             embed.set_thumbnail(url=target_user.avatar.url)
        embed.add_field(name="Current Status", value=status_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        if not content:
            return

        first_word = content.split()[0]
        
        # Keywords
        away_keywords = {"brb", "afk", "gone", "away"}
        active_keywords = {"bk", "back", "here"}

        user_id = message.author.id

        if first_word in away_keywords:
            current_status = self.get_status(user_id)
            if current_status != "Away":
                self.set_status(user_id, "Away")
                await message.channel.send(f"💤 Set {message.author.mention} to **Away**.")
        
        elif first_word in active_keywords:
             current_status = self.get_status(user_id)
             if current_status != "Active":
                 self.set_status(user_id, "Active")
                 await message.channel.send(f"👋 Set {message.author.mention} to **Active**.")

async def setup(bot):
    await bot.add_cog(Status(bot))
