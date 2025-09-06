import discord
from discord.ext import commands
import os
from dotenv import load_dotenv 
import logging
import csv
import json
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
bot_token = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

CHANNEL_FILE = "channels.json"

def read_csv_as_list_of_dicts(filepath):
    """
    Reads a CSV file and returns its data as a list of dictionaries.
    Each dictionary represents a row, with column headers as keys.
    """
    data = []
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

def load_channels():
    if os.path.exists(CHANNEL_FILE):
        with open(CHANNEL_FILE, "r") as f:
            return json.load(f)
    return {}

def save_channels(channels):
    with open(CHANNEL_FILE, "w") as f:
        json.dump(channels, f)

spawnists = read_csv_as_list_of_dicts("thelist.csv")
target_channels = load_channels()

@bot.hybrid_command(name="outchannel", description="Sets output channel for logs.")
async def outchannel(ctx, target_channel_id):
    channel = bot.get_channel(target_channel_id)
    guild_id = str(ctx.guild.id)
    global target_channels
    if channel:
        target_channels[guild_id] = target_channel_id
        save_channels(target_channels)
        await ctx.send(f"Successfully set channel to {target_channel_id} for this guild.")
    else:
        await ctx.send(f"Channel not found {target_channel_id}")

@bot.hybrid_command(name="firstrun", description="Bans all applicable users")
async def firstrun(ctx):
    guild = ctx.guild
    banned_count = 0
    for member in guild.members:
        for row in spawnists:
            # Assuming the CSV has a column 'id' with user IDs
            if str(member.id) == str(row.get('id', '')):
                try:
                    await member.ban(reason=f"Despawner banned {member.id}. Looks like they wont be coming back another time!")
                    await ctx.send(f'{member.mention} has been banned from the server.')
                    await member.send("You have been banned due to your alleged connection with Spawnism.")
                    banned_count += 1
                except discord.Forbidden:
                    await ctx.send("I don't have the necessary permissions to ban this user.")
                except discord.HTTPException as e:
                    await ctx.send(f"An error occurred while trying to ban: {e}")
    if banned_count == 0:
        await ctx.send("No users matched for banning.")

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    channel_id = target_channels.get(guild_id)
    channel = bot.get_channel(channel_id) if channel_id else None
    for row in spawnists:
        if str(member.id) == str(row.get('id', '')):
            try:
                await member.ban(reason=f"Despawner banned {member.id}. Looks like they wont be coming back another time!")
                if channel:
                    await channel.send(f'{member.mention} has been banned from the server.')
                await member.send("You have been banned due to your alleged connection with Spawnism.")
            except discord.Forbidden:
                if channel:
                    await channel.send("I don't have the necessary permissions to ban this user.")
            except discord.HTTPException as e:
                if channel:
                    await channel.send(f"An error occurred while trying to ban: {e}")

@bot.event
async def on_ready():
    # Sync the command tree for hybrid commands
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Command tree synced.")

if __name__ == "__main__":
    bot.run(bot_token)

