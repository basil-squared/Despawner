import discord
from discord.ext import commands
from discord import app_commands
from utils.config import ConfigManager
from utils.utils import Utils

class DryRun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()

    @app_commands.command(
        name="dryrun",
        description="Test ban behavior without actually banning anyone"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def dryrun(self, interaction: discord.Interaction, user_id: str = None):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild_id)
        config = self.config_manager.get_guild_config(guild_id)
        
        # Create mock user for testing
        mock_user = {
            'id': user_id or '123456789',
            'name': 'TestUser',
            'nickname': 'spawnist_test',  # Contains banned keyword
            'global_name': 'Test Account'
        }

        embed = discord.Embed(
            title="🔍 Dry Run Results",
            description="Testing ban behavior with mock user",
            color=discord.Color.yellow()
        )

        # Test ID ban
        embed.add_field(
            name="ID Check",
            value=self._test_id_ban(mock_user, config),
            inline=False
        )

        # Test keyword ban
        embed.add_field(
            name="Keyword Check",
            value=self._test_keyword_ban(mock_user, config),
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

    def _test_id_ban(self, mock_user, config):
        spawnists = Utils.read_csv_as_list_of_dicts(Utils, "thelist.csv")
        id_list = [str(row.get('id', '')).strip() for row in spawnists]
        
        if mock_user['id'] in id_list:
            if config['id_ban_behavior'] == 'auto':
                return "✅ Would ban: User ID found in banlist"
            elif config['id_ban_behavior'] == 'notify':
                return "🔔 Would notify: User ID found in banlist"
            else:
                return "⏭️ Would ignore: User ID found but ignore is set"
        return "❌ Would not ban: User ID not in banlist"

    def _test_keyword_ban(self, mock_user, config):
        results = []
        for field, value in [
            ('username', mock_user['name']),
            ('nickname', mock_user['nickname']),
            ('global name', mock_user['global_name'])
        ]:
            keyword = Utils.contains_banned_keyword(Utils, value)
            if keyword:
                if config['keyword_ban_behavior'] == 'auto':
                    results.append(f"✅ Would ban: Found '{keyword}' in {field}")
                elif config['keyword_ban_behavior'] == 'notify':
                    results.append(f"🔔 Would notify: Found '{keyword}' in {field}")
                else:
                    results.append(f"⏭️ Would ignore: Found '{keyword}' in {field}")
            else:
                results.append(f"❌ No banned keywords in {field}")
        
        return "\n".join(results)

async def setup(bot):
    await bot.add_cog(DryRun(bot))