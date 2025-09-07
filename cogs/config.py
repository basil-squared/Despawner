import discord
from discord.ext import commands
from discord import app_commands
from utils.config import ConfigManager
from utils.error_handler import ErrorHandler
from typing import Optional

class ConfigDropdown(discord.ui.Select):
    def __init__(self, setting_name: str, current_value: any):
        self.setting_name = setting_name
        options = []
        
        if setting_name in ['keyword_ban_behavior', 'id_ban_behavior']:
            options = [
                discord.SelectOption(
                    label="Automatic Ban",
                    description="Automatically ban matching users",
                    value="auto",
                    default=current_value == "auto"
                ),
                discord.SelectOption(
                    label="Notify Only",
                    description="Notify staff without banning",
                    value="notify",
                    default=current_value == "notify"
                ),
                discord.SelectOption(
                    label="Ignore",
                    description="Take no action",
                    value="ignore",
                    default=current_value == "ignore"
                )
            ]
        elif isinstance(current_value, bool):
            options = [
                discord.SelectOption(
                    label="Enabled",
                    value="true",
                    default=current_value
                ),
                discord.SelectOption(
                    label="Disabled",
                    value="false",
                    default=not current_value
                )
            ]

        super().__init__(
            placeholder=f"Select {setting_name.replace('_', ' ').title()}",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        value = self.values[0]
        if value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
            
        if await self.view.update_config(interaction, self.setting_name, value):
            await interaction.response.send_message(
                f"Updated {self.setting_name} to {value}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Failed to update {self.setting_name}",
                ephemeral=True
            )

class ConfigView(discord.ui.View):
    def __init__(self, config_manager: ConfigManager, guild_id: str):
        super().__init__(timeout=300)
        self.config_manager = config_manager
        self.guild_id = guild_id
        self.setup_dropdowns()

    def setup_dropdowns(self):
        config = self.config_manager.get_guild_config(self.guild_id)
        for setting, value in config.items():
            self.add_item(ConfigDropdown(setting, value))

    async def update_config(self, interaction: discord.Interaction, setting: str, value: any) -> bool:
        return self.config_manager.update_guild_config(self.guild_id, setting, value)

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()

    @app_commands.command(name="config", description="Configure bot behavior")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_menu(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = self.config_manager.get_guild_config(guild_id)

        embed = discord.Embed(
            title="Server Configuration",
            description="Use the dropdowns below to configure bot behavior",
            color=discord.Color.blue()
        )

        for key, value in config.items():
            embed.add_field(
                name=key.replace("_", " ").title(),
                value=f"Current: {str(value)}",
                inline=False
            )

        view = ConfigView(self.config_manager, guild_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @config_menu.error
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
                "Configuration Error",
                f"An unexpected error occurred while configuring the bot.",
                error_type=error.__class__.__name__,
                show_help=True
            )

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))