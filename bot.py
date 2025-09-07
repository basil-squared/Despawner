import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
import csv
import json
from datetime import datetime
from utils import Utils
from pathlib import Path

load_dotenv()
logging.basicConfig(level=logging.INFO)
bot_token = os.getenv('DISCORD_BOT_TOKEN')

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="$",
            intents=discord.Intents.all(),
            application_id=os.getenv('APPLICATION_ID')
        )
    
    async def setup_hook(self):
        # Load all cogs
        cogs_dir = Path(__file__).parent / "cogs"
        if cogs_dir.exists():
            for cog_file in cogs_dir.glob("*.py"):
                if cog_file.name != "__init__.py":
                    try:
                        await self.load_extension(f"cogs.{cog_file.stem}")
                        print(f"Loaded cog: {cog_file.stem}")
                    except Exception as e:
                        print(f"Failed to load cog {cog_file.stem}: {str(e)}")

        # Sync commands
        await self.tree.sync()
        print("Command tree synced!")

bot = Bot()

# Update the initial loading
spawnists = Utils.read_csv_as_list_of_dicts(Utils, "thelist.csv")
target_channels = Utils.load_channels(Utils)
# Remove global appeal_link as it's now per-guild







@bot.tree.command(name="outchannel", description="Sets output channel for logs.")
@commands.has_permissions(ban_members=True)
async def outchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_id = str(interaction.guild_id)
    global target_channels
    target_channels[guild_id] = channel.id
    Utils.save_channels(Utils, target_channels)
    await interaction.response.send_message(f"Successfully set channel to {channel.mention}", ephemeral=True)

@bot.tree.command(name="reloadlists", description="Reloads the banlist and keywords from disk.")
@commands.has_permissions(ban_members=True)
async def reloadlists(interaction: discord.Interaction):
    global spawnists, target_channels
    spawnists = Utils.read_csv_as_list_of_dicts(Utils, "thelist.csv")
    target_channels = Utils.load_channels(Utils)
    await interaction.response.send_message("Banlist and channels reloaded from disk.", ephemeral=True)

# Error handler for permission errors


@outchannel.error
@reloadlists.error
async def permission_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need the 'Ban Members' permission to use this command.", ephemeral=True)
    else:
        raise error

@bot.event
async def on_ready():
    # Sync commands globally and per guild for instant updates
    await bot.tree.sync()
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Command tree synced.")

if __name__ == "__main__":
    bot.run(bot_token)

