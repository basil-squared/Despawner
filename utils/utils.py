import logging
import os
import csv
import discord
from discord.ext import commands
import json

class Utils:
    CHANNEL_FILE = "channels.json"
    APPEAL_FILE = "appeal_links.json"
    BAN_COUNT_FILE = "ban_count.txt"  # Add this constant
    BANNED_KEYWORDS = ["spawnist", "spawn", "spawnism", "proship", "prosaken", "darkship"]
    
    def __init__(self):
        pass
    
    def read_csv_as_list_of_dicts(self, filepath):
        """
        Reads a CSV file and returns its data as a list of dictionaries.
        Each dictionary represents a row, with column headers as keys.
        """
        data = []
        if not os.path.exists(filepath):
            logging.warning(f"CSV file {filepath} not found.")
            return data
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data

    def load_channels(self):
        if os.path.exists(self.CHANNEL_FILE): 
            with open(self.CHANNEL_FILE, "r") as f:
                return json.load(f)
        return {}
    def save_channels(self,channels)->None:
        with open(self.CHANNEL_FILE, "w") as f:
            json.dump(channels, f)


    def load_appeal_link(self, guild_id: str) -> str:
        """Load appeal link for specific guild"""
        if os.path.exists(self.APPEAL_FILE):
            with open(self.APPEAL_FILE, "r") as f:
                appeals = json.load(f)
                return appeals.get(str(guild_id), "")
        return ""

    def save_appeal_link(self, guild_id: str, link: str) -> None:
        """Save appeal link for specific guild"""
        appeals = {}
        if os.path.exists(self.APPEAL_FILE):
            with open(self.APPEAL_FILE, "r") as f:
                appeals = json.load(f)
        
        appeals[str(guild_id)] = link
        
        with open(self.APPEAL_FILE, "w") as f:
            json.dump(appeals, f)

    def load_ban_count(self) -> int:
        """Load the total number of bans"""
        if os.path.exists(self.BAN_COUNT_FILE):
            with open(self.BAN_COUNT_FILE, "r") as f:
                return int(f.read().strip() or "0")
        return 0

    def increment_ban_count(self) -> int:
        """Increment and save the ban count"""
        count = self.load_ban_count() + 1
        with open(self.BAN_COUNT_FILE, "w") as f:
            f.write(str(count))
        return count
             
    def contains_banned_keyword(self,text):
        if not text:
            return None
        text_lower = str(text).lower()
        for keyword in self.BANNED_KEYWORDS:
            if keyword.lower() in text_lower:
                return keyword
        return None  
    
    async def ban_with_appeal(self, member: discord.Member, reason: str, keyword: str = None):
        try:
            await member.ban(reason=reason)
            dm_message = "You have been banned due to your alleged connection with Spawnism or forbidden content."
            if keyword:
                dm_message += f"\nBan triggered by keyword: **{keyword}**."
            if self.appeal_link:
                dm_message += f"\nIf you believe this is a mistake, you may appeal here: {self.appeal_link}"
            try:
                await member.send(dm_message)
            except discord.HTTPException:
                pass  # Failed to DM user
        except discord.Forbidden:
            pass  # Bot lacks permissions
        except discord.HTTPException:
            pass  # API error

