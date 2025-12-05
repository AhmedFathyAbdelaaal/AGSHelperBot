import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_perms(self, interaction: discord.Interaction) -> bool:
        """Checks if the user has the required role."""
        # Block specific user
        if interaction.user.id == 123456789012345678: # REPLACE THIS WITH THE USER ID
            await interaction.response.send_message("🚫 You are blocked from using this bot.", ephemeral=True)
            return False

        if not any(role.name == "isAdmin" for role in interaction.user.roles):
            await interaction.response.send_message("🚫 You are not allowed to use this bot. You need the 'isAdmin' role.", ephemeral=True)
            return False
        return True

    @app_commands.command(name="cleanmsgs", description="Delete X amount of latest messages from a specific user")
    @app_commands.describe(user_id="The ID of the user whose messages you want to delete", amount="The number of messages to delete")
    async def clean_msgs(self, interaction: discord.Interaction, user_id: str, amount: int):
        """Deletes a specified amount of messages from a specific user."""
        if not await self.check_perms(interaction):
            return

        # Check if bot has permissions to manage messages
        if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
            await interaction.response.send_message("🚫 I don't have permission to manage messages in this channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            target_id = int(user_id)
        except ValueError:
            await interaction.followup.send("Invalid User ID provided. Please provide a numeric ID.", ephemeral=True)
            return

        messages_to_delete = []
        count = 0
        
        # Scan history. Limit scanning to avoid hanging on empty searches.
        # Scanning 500 messages to find 'amount' seems reasonable.
        async for msg in interaction.channel.history(limit=500): 
            if msg.author.id == target_id:
                messages_to_delete.append(msg)
                count += 1
            if count >= amount:
                break
        
        if not messages_to_delete:
            await interaction.followup.send(f"No messages found from user ID {user_id} in the last 500 messages.", ephemeral=True)
            return

        # Delete logic
        # Bulk delete works for messages < 14 days
        two_weeks_ago = discord.utils.utcnow() - timedelta(days=14)
        
        recent_msgs = [m for m in messages_to_delete if m.created_at > two_weeks_ago]
        old_msgs = [m for m in messages_to_delete if m.created_at <= two_weeks_ago]

        deleted_count = 0

        if recent_msgs:
            try:
                await interaction.channel.delete_messages(recent_msgs)
                deleted_count += len(recent_msgs)
            except Exception as e:
                print(f"Error bulk deleting: {e}")

        # For old messages, we must delete one by one (slow)
        for msg in old_msgs:
            try:
                await msg.delete()
                deleted_count += 1
                await asyncio.sleep(1) # Rate limit protection
            except Exception as e:
                print(f"Error deleting old message: {e}")

        await interaction.followup.send(f"Successfully deleted {deleted_count} messages from user ID {user_id}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
