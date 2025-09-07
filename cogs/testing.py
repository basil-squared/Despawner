import discord
from discord import app_commands
from discord.ext import commands
from utils.utils import Utils
from utils.config import ConfigManager
from utils.error_handler import ErrorHandler

class TestingCog(commands.GroupCog, name="test"):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        super().__init__()

    @app_commands.command(name="bandetection", description="Test ban detection without banning")
    @app_commands.checks.has_permissions(ban_members=True)
    async def test_ban(self, interaction: discord.Interaction, user_id: str = None):
        await interaction.response.defer(ephemeral=True)
        test_id = user_id or '123456789'
        guild_id = str(interaction.guild_id)
        config = self.config_manager.get_guild_config(guild_id)
        
        # Test ID ban first
        ban_handler = self.bot.get_cog('BanHandler')
        is_banned = False
        
        if ban_handler:
            is_banned = await ban_handler.check_id_ban(test_id)
            
        # Create test user info
        test_user = {
            'id': test_id,
            'name': 'TestUser',
            'nickname': 'spawnist_test',  # Contains banned keyword
            'global_name': 'Test Account'
        }

        embed = discord.Embed(
            title="🔍 Ban Detection Test",
            description=f"Testing user ID: `{test_id}`",
            color=discord.Color.yellow()
        )

        # Add ID check result
        if is_banned:
            if config['id_ban_behavior'] == 'auto':
                id_result = "✅ Would ban: User ID found in banlist"
            elif config['id_ban_behavior'] == 'notify':
                id_result = "🔔 Would notify: User ID found in banlist"
            else:
                id_result = "⏭️ Would ignore: User ID found but ignore is set"
        else:
            id_result = "❌ Would not ban: User ID not in banlist"

        embed.add_field(name="ID Check", value=id_result, inline=False)

        # Test keywords
        keyword_results = []
        for field, value in [
            ('Username', test_user['name']),
            ('Nickname', test_user['nickname']),
            ('Global Name', test_user['global_name'])
        ]:
            keyword = Utils.contains_banned_keyword(Utils, value)
            if keyword:
                if config['keyword_ban_behavior'] == 'auto':
                    result = f"✅ Would ban: Found '{keyword}' in {field}"
                elif config['keyword_ban_behavior'] == 'notify':
                    result = f"🔔 Would notify: Found '{keyword}' in {field}"
                else:
                    result = f"⏭️ Would ignore: Found '{keyword}' in {field}"
            else:
                result = f"❌ No banned keywords in {field}"
            keyword_results.append(result)

        embed.add_field(
            name="Keyword Checks",
            value="\n".join(keyword_results),
            inline=False
        )

        # Show current config
        embed.add_field(
            name="Current Configuration",
            value=(
                f"ID Ban Behavior: `{config['id_ban_behavior']}`\n"
                f"Keyword Ban Behavior: `{config['keyword_ban_behavior']}`\n"
                f"DM on Ban: `{config['dm_on_ban']}`\n"
                f"Log Bans: `{config['log_bans']}`\n"
                f"Notify Staff: `{config['notify_staff']}`"
            ),
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @test_ban.error
    async def test_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await ErrorHandler.send_error(
                interaction,
                "Permission Denied",
                "You need Ban Members permission to use this command.",
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
    await bot.add_cog(TestingCog(bot))