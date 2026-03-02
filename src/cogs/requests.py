import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from datetime import datetime
import traceback
import math

# Database Path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'requests.db')

# --- Helper Functions ---
def get_status_color(status):
    colors = {
        "Untouched": 0x95a5a6, # Grey
        "In Progress": 0x3498db, # Blue
        "Need Help": 0xe67e22, # Orange
        "Complete": 0x2ecc71, # Green
        "Rejected": 0xe74c3c  # Red
    }
    return colors.get(status, 0x99aab5)

def get_next_id(db_path, req_type_prefix):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Get all IDs matching the prefix
    c.execute("SELECT id FROM requests WHERE id LIKE ?", (f"{req_type_prefix}-%",))
    rows = c.fetchall()
    conn.close()
    
    max_num = 0
    for row in rows:
        try:
            # Parse ID like BUG-101
            num = int(row[0].split('-')[1])
            if num > max_num:
                max_num = num
        except:
            continue
    
    return f"{req_type_prefix}-{max_num + 1}"

# --- Modals ---

class BugReportModal(discord.ui.Modal, title="Bug Report 🪲"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        
        self.issue_title = discord.ui.TextInput(
            label="Issue Title", 
            placeholder="e.g. Login button doesn't work", 
            min_length=5, 
            max_length=100
        )
        self.platform = discord.ui.TextInput(
            label="Platform",
            placeholder="Website, Mobile App, or Discord",
            min_length=3,
            max_length=50
        )
        self.severity = discord.ui.TextInput(
            label="Severity",
            placeholder="Critical, Major, or Minor",
            min_length=3,
            max_length=50
        )
        self.steps = discord.ui.TextInput(
            label="Steps to Reproduce", 
            style=discord.TextStyle.paragraph, 
            placeholder="1. Open dashboard, 2. Click settings, 3. Observe the crash."
        )
        self.expected = discord.ui.TextInput(
            label="Expected vs. Actual", 
            style=discord.TextStyle.paragraph, 
            placeholder="What should have happened vs. what actually happened."
        )

        self.add_item(self.issue_title)
        self.add_item(self.platform)
        self.add_item(self.severity)
        self.add_item(self.steps)
        self.add_item(self.expected)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.submit_request(
            interaction, 
            "Bug", 
            "BUG", 
            self.issue_title.value, 
            self.platform.value, 
            self.severity.value, 
            self.steps.value, 
            self.expected.value, 
            None
        )

class IdeaModal(discord.ui.Modal, title="Idea Suggestion 💡"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        
        self.idea_short = discord.ui.TextInput(
            label="The Idea", 
            placeholder="Elevator pitch in 10 words or less", 
            max_length=100
        )
        self.category = discord.ui.TextInput(
            label="Category",
            placeholder="Community, Website, Fun/Bot, Economy...",
            max_length=50
        )
        self.description = discord.ui.TextInput(
            label="Description", 
            style=discord.TextStyle.paragraph, 
            placeholder="Explain the idea in detail."
        )
        self.why = discord.ui.TextInput(
            label="The 'Why'", 
            style=discord.TextStyle.paragraph, 
            placeholder="How does this help the community or project?"
        )
        self.visual = discord.ui.TextInput(
            label="Visual Reference", 
            placeholder="Link to screenshot/example (Optional)", 
            required=False
        )

        self.add_item(self.idea_short)
        self.add_item(self.category)
        self.add_item(self.description)
        self.add_item(self.why)
        self.add_item(self.visual)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.submit_request(
            interaction, 
            "Idea", 
            "IDEA", 
            self.idea_short.value, 
            self.category.value, 
            self.description.value, 
            self.why.value, 
            self.visual.value, 
            None
        )

class FeatureRequestModal(discord.ui.Modal, title="Feature Request 🚀"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        
        self.feat_name = discord.ui.TextInput(
            label="Feature Name", 
            placeholder="Technical name for the feature", 
            max_length=100
        )
        self.use_case = discord.ui.TextInput(
            label="Use Case", 
            style=discord.TextStyle.paragraph, 
            placeholder="As a [user], I want to [action] so that [benefit]."
        )
        self.functionality = discord.ui.TextInput(
            label="Functionality", 
            style=discord.TextStyle.paragraph, 
            placeholder="Describe functionality step-by-step."
        )
        self.priority = discord.ui.TextInput(
            label="Priority",
            placeholder="High, Medium, or Low",
            max_length=50
        )
        self.impact = discord.ui.TextInput(
            label="Impact",
            placeholder="Affects Everyone, Staff Only, etc.",
            max_length=50
        )

        self.add_item(self.feat_name)
        self.add_item(self.use_case)
        self.add_item(self.functionality)
        self.add_item(self.priority)
        self.add_item(self.impact)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.submit_request(
            interaction, 
            "Feature", 
            "FEAT", 
            self.feat_name.value, 
            self.use_case.value, 
            self.functionality.value, 
            self.priority.value, 
            self.impact.value, 
            None
        )

# --- Pagination View ---
class RequestPaginationView(discord.ui.View):
    def __init__(self, data, title, user_id):
        super().__init__(timeout=180)
        self.data = data
        self.title = title
        self.user_id = user_id
        self.current_page = 0
        self.items_per_page = 5
        self.total_pages = math.ceil(len(data) / self.items_per_page)

    async def update_message(self, interaction):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        batch = self.data[start:end]
        
        embed = discord.Embed(title=f"{self.title} (Page {self.current_page + 1}/{self.total_pages})", color=0x3498db)
        for item in batch:
            # item: (id, status, title, ...)
            req_id, status, title = item[0], item[3], item[5]
            status_emoji = self.get_status_emoji(status)
            embed.add_field(name=f"{status_emoji} {req_id}: {title}", value=f"Status: **{status}**", inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)

    def get_status_emoji(self, status):
        emojis = {
            "Untouched": "⚪",
            "In Progress": "🔵",
            "Need Help": "🟠",
            "Complete": "🟢",
            "Rejected": "🔴"
        }
        return emojis.get(status, "⚪")

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

# --- Main Cog ---

class Requests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS requests (
            id TEXT PRIMARY KEY,
            req_type TEXT,
            user_id INTEGER,
            status TEXT,
            created_at TEXT,
            title TEXT,
            data_1 TEXT,
            data_2 TEXT,
            data_3 TEXT,
            data_4 TEXT,
            data_5 TEXT
        )''')
        conn.commit()
        conn.close()

    async def submit_request(self, interaction, req_type, prefix, title, d1, d2, d3, d4, d5):
        new_id = get_next_id(DB_PATH, prefix)
        created_at = datetime.now().isoformat()
        status = "Untouched"
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO requests (id, req_type, user_id, status, created_at, title, data_1, data_2, data_3, data_4, data_5)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (new_id, req_type, interaction.user.id, status, created_at, title, d1, d2, d3, d4, d5))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(title=f"{req_type} Submitted!", color=get_status_color(status))
        embed.add_field(name="ID", value=new_id)
        embed.add_field(name="Title", value=title)
        embed.set_footer(text=f"Status: {status}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="bug_report", description="Report a bug")
    async def bug_report(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BugReportModal(self))

    @app_commands.command(name="idea_suggest", description="Suggest an idea")
    async def idea_suggest(self, interaction: discord.Interaction):
        await interaction.response.send_modal(IdeaModal(self))

    @app_commands.command(name="feature_request", description="Request a feature")
    async def feature_request(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FeatureRequestModal(self))

    # --- Check for Perms ---
    def has_bot_perms(self, interaction: discord.Interaction):
        return any(role.name == "hasBotPerms" for role in interaction.user.roles) or interaction.user.guild_permissions.administrator

    @app_commands.command(name="show_bugs", description="Show all bug reports (Admin/BotPerms)")
    async def show_bugs(self, interaction: discord.Interaction, status: str = None):
        if not self.has_bot_perms(interaction):
            return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
        await self.show_list(interaction, "Bug", status)

    @app_commands.command(name="show_features", description="Show all feature requests (Admin/BotPerms)")
    async def show_features(self, interaction: discord.Interaction, status: str = None):
        if not self.has_bot_perms(interaction):
            return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
        await self.show_list(interaction, "Feature", status)

    @app_commands.command(name="show_ideas", description="Show all ideas (Admin/BotPerms)")
    async def show_ideas(self, interaction: discord.Interaction, status: str = None):
        if not self.has_bot_perms(interaction):
            return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
        await self.show_list(interaction, "Idea", status)

    async def show_list(self, interaction, req_type, status_filter):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = "SELECT * FROM requests WHERE req_type = ?"
        params = [req_type]
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        query += " ORDER BY created_at DESC"
        
        c.execute(query, tuple(params))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return await interaction.response.send_message(f"No {req_type} requests found.", ephemeral=True)
            
        view = RequestPaginationView(rows, f"{req_type} List", interaction.user.id)
        
        # Manually construct first page
        view.current_page = 0
        start = 0
        end = view.items_per_page
        batch = rows[start:end]
        embed = discord.Embed(title=f"{req_type} List (Page 1/{view.total_pages})", color=0x3498db)
        for item in batch:
             # item: 0=id, 3=status, 5=title
            req_id, status, title = item[0], item[3], item[5]
            status_emoji = view.get_status_emoji(status)
            embed.add_field(name=f"{status_emoji} {req_id}: {title}", value=f"Status: **{status}**", inline=False)
        
        if interaction.response.is_done():
            msg = await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="show_request", description="View details of a specific request (Admin/BotPerms)")
    @app_commands.describe(request_id="The ID of the request (e.g. BUG-101)")
    async def show_request(self, interaction: discord.Interaction, request_id: str):
        if not self.has_bot_perms(interaction):
            return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return await interaction.response.send_message("Request not found.", ephemeral=True)
            
        # Unpack row
        # 0:id, 1:req_type, 2:user_id, 3:status, 4:created_at, 5:title, 6:d1, 7:d2, 8:d3, 9:d4, 10:d5
        req_id, req_type, user_id, status, created_at, title, d1, d2, d3, d4, d5 = row
        
        color = get_status_color(status)
        embed = discord.Embed(title=f"DETAILS: {req_id} - {title}", color=color)
        embed.set_footer(text=f"Submitted by User ID: {user_id} • Status: {status}")
        
        if req_type == "Bug":
            embed.add_field(name="Platform", value=d1, inline=True)
            embed.add_field(name="Severity", value=d2, inline=True)
            embed.add_field(name="Steps to Reproduce", value=d3, inline=False)
            embed.add_field(name="Expected vs Actual", value=d4, inline=False)
            
        elif req_type == "Idea":
            embed.add_field(name="Category", value=d1, inline=True)
            embed.add_field(name="Description", value=d2, inline=False)
            embed.add_field(name="The Why", value=d3, inline=False)
            if d4: embed.add_field(name="Visual Ref", value=d4, inline=False)
            
        elif req_type == "Feature":
            embed.add_field(name="Use Case", value=d1, inline=False)
            embed.add_field(name="Functionality", value=d2, inline=False)
            embed.add_field(name="Priority", value=d3, inline=True)
            embed.add_field(name="Impact", value=d4, inline=True)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="update_status", description="Update status of a request")
    @app_commands.choices(new_status=[
        app_commands.Choice(name="Untouched", value="Untouched"),
        app_commands.Choice(name="In Progress", value="In Progress"),
        app_commands.Choice(name="Need Help", value="Need Help"),
        app_commands.Choice(name="Complete", value="Complete"),
        app_commands.Choice(name="Rejected", value="Rejected")
    ])
    async def update_status(self, interaction: discord.Interaction, request_id: str, new_status: app_commands.Choice[str]):
        if not self.has_bot_perms(interaction):
            return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status.value, request_id))
        
        if c.rowcount == 0:
            conn.close()
            return await interaction.response.send_message(f"Request {request_id} not found.", ephemeral=True)
            
        conn.commit()
        conn.close()
        
        await interaction.response.send_message(f"Updated **{request_id}** status to **{new_status.value}**.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Requests(bot))
