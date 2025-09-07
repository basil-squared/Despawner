import discord
from discord import app_commands
from discord.ext import commands
from utils.utils import Utils
from utils.config import ConfigManager
from utils.error_handler import ErrorHandler

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()

    config_group = app_commands.Group(name="config", description="Configuration commands")

    @config_group.command(name="bans", description="Configure ban behavior")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_bans(self, interaction: discord.Interaction):
        """Configure the ban behavior for the server."""
        guild_id = str(interaction.guild_id)
        config = self.config_manager.get_guild_config(guild_id)

        embed = discord.Embed(
            title="Ban Configuration",
            description="Configure the ban behavior for your server.",
            color=discord.Color.red()
        )

        # Add fields for each ban-related configuration
        for key, value in config.items():
            if "ban" in key:  # Only include ban-related settings
                embed.add_field(
                    name=key.replace("_", " ").title(),
                    value=f"Current: {str(value)}",
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @config_group.command(name="appeal", description="Set appeal link for this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_appeal(self, interaction: discord.Interaction, link: str):
        """Set the appeal link for banned users."""
        guild_id = str(interaction.guild_id)
        if self.config_manager.update_guild_config(guild_id, "appeal_link", link):
            await interaction.response.send_message(
                f"Appeal link updated to: {link}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to update appeal link.",
                ephemeral=True
            )

    @config_group.command(name="channel", description="Set output channel for ban logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the channel where ban logs will be sent."""
        guild_id = str(interaction.guild_id)
        channel_id = channel.id

        if self.config_manager.update_guild_config(guild_id, "log_channel", channel_id):
            await interaction.response.send_message(
                f"Ban log channel updated to: {channel.mention}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to update ban log channel.",
                ephemeral=True
            )

    @config_bans.error
    @config_appeal.error
    @config_channel.error
    async def config_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await ErrorHandler.send_error(
                interaction,
                "Permission Denied",
                "You need Administrator permission to use this command.",
                error_type="MissingPermissions"
            )
        else:
            await ErrorHandler.send_error(
                interaction,
                "Command Error",
                str(error),
                error_type=error.__class__.__name__,
                show_help=True
            )

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))