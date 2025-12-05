import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('General Cog loaded.')

    async def cog_check(self, ctx):
        """Checks if the user has the required role for all commands in this Cog."""
        # Block specific user
        if ctx.author.id == 1046752946639093780: # REPLACE THIS WITH THE USER ID
            await ctx.send("🚫 You are blocked from using this bot.")
            return False

        if any(role.name == "hasBotPerms" for role in ctx.author.roles):
            return True
        await ctx.send("🚫 You are not allowed to use this bot. You need the 'hasBotPerms' role.")
        return False

    @commands.command(name='ping', help='Responds with Pong!')
    async def ping(self, ctx):
        await ctx.send('Pong!')

    @commands.command(name='hello', help='Says hello to the user')
    async def hello(self, ctx):
        await ctx.send(f'Hello there, {ctx.author.mention}!')

async def setup(bot):
    await bot.add_cog(General(bot))
