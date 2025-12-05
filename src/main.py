import discord
import os
import sys
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Add the project root directory to the Python path so we can import src.cogs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True # Required for commands to work

# Setup Bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    print('------')

async def load_extensions():
    # Load cogs from the cogs folder
    cogs_path = os.path.join(os.path.dirname(__file__), 'cogs')
    for filename in os.listdir(cogs_path):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f'src.cogs.{filename[:-3]}')
                print(f'Loaded extension: {filename}')
            except Exception as e:
                print(f'Failed to load extension {filename}.', e)

async def main():
    async with bot:
        await load_extensions()
        if not TOKEN:
            print("Error: DISCORD_TOKEN not found in .env file.")
            return
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
