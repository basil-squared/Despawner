import discord
from discord import app_commands
from discord.ext import commands
from utils.utils import Utils

class SetAppeal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utils = Utils()
        self.appeal_links = {}  # Dictionary to store guild-specific links

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded")
        # Load appeal links for all guilds
        for guild in self.bot.guilds:
            self.appeal_links[str(guild.id)] = Utils.load_appeal_link(Utils, str(guild.id))

    @app_commands.command(name="setappeal", description="Sets appeal link for this server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def setappeallink(self, interaction: discord.Interaction, link: str):
        guild_id = str(interaction.guild_id)
        self.appeal_links[guild_id] = link
        Utils.save_appeal_link(Utils, guild_id, link)
        await interaction.response.send_message(f"Appeal link set to: {link} for this server", ephemeral=True)

    async def ban_with_appeal(self, member: discord.Member, reason: str, keyword: str = None):
        try:
            await member.ban(reason=reason)
            guild_id = str(member.guild.id)
            appeal_link = self.appeal_links.get(guild_id, "")
            
            dm_message = "You have been banned due to your alleged connection with Spawnism or forbidden content."
            if keyword:
                dm_message += f"\nBan triggered by keyword: **{keyword}**."
            if appeal_link:
                dm_message += f"\nIf you believe this is a mistake, you may appeal here: {appeal_link}"
            try:
                await member.send(dm_message)
            except discord.HTTPException:
                pass
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

    @setappeallink.error
    async def on_setappeallink_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You need the 'Ban Members' permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SetAppeal(bot))