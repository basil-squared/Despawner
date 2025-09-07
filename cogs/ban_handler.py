import discord
from discord import app_commands
from discord.ext import commands
from utils.utils import Utils
from utils.config import ConfigManager
from utils.error_handler import ErrorHandler
from utils.action_logger import ActionLogger

class BanHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.logger = ActionLogger()
        self.reload_banned_ids()

    def reload_banned_ids(self):
        """Reload the banned IDs set from CSV"""
        self.banned_ids = set()
        try:
            with open("thelist.csv", 'r') as f:
                for line in f:
                    # Strip whitespace and get first column if comma-separated
                    user_id = line.strip().split(',')[0]
                    if user_id and user_id.isdigit():
                        self.banned_ids.add(str(user_id))
            print(f"Loaded {len(self.banned_ids)} banned IDs")
        except Exception as e:
            print(f"Error loading banned IDs: {e}")

    async def check_id_ban(self, member_id: str) -> bool:
        """Check if a member ID is in the banned list"""
        return str(member_id).strip() in self.banned_ids

    ban_group = app_commands.Group(name="ban", description="Ban related commands")

    @ban_group.command(name="firstrun", description="Scan and ban all matching users")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_firstrun(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            guild = interaction.guild
            guild_id = str(guild.id)
            checked_users = len(guild.members)
            id_list = [str(row.get('id', '')).strip() for row in Utils.read_csv_as_list_of_dicts(Utils, "thelist.csv")]
            matches = []
            banned_count = 0
            keyword_matches = []

            for member in guild.members:
                if member.id == self.bot.user.id:
                    continue
                banned = False
                if str(member.id) in id_list:
                    matches.append(member)
                    await self.utils.ban_with_appeal(member, f"Despawner banned {member.id}", guild_id=guild_id)
                    await interaction.followup.send(f'{member.mention} has been banned from the server.')
                    banned_count += 1
                    banned = True

                if not banned:
                    username = str(member.name)
                    nickname = str(member.nick) if member.nick else ""
                    bio = str(member.global_name) if member.global_name else ""
                    for field in [username, nickname, bio]:
                        keyword = Utils.contains_banned_keyword(Utils, field)
                        if keyword:
                            keyword_matches.append(member)
                            await self.utils.ban_with_appeal(member, 
                                f"Banned for forbidden keyword in username/nickname/bio.", 
                                keyword=keyword, 
                                guild_id=guild_id
                            )
                            await interaction.followup.send(
                                f'{member.mention} has been banned for forbidden keyword "{keyword}"'
                            )
                            banned_count += 1
                            break

            # Create embed with results
            embed = discord.Embed(
                title="Firstrun Summary",
                description="Ban operation summary",
                color=discord.Color.red()
            )
            embed.add_field(name="Users Checked", value=str(checked_users), inline=False)
            embed.add_field(name="IDs in List", value=str(len(id_list)), inline=False)
            embed.add_field(name="Matches Found (ID)", value=str(len(matches)), inline=False)
            embed.add_field(
                name="Matched Users (ID)",
                value="\n".join([f"{m.name} ({m.id})" for m in matches]) if matches else "None",
                inline=False
            )
            embed.add_field(name="Keyword Matches", value=str(len(keyword_matches)), inline=False)
            embed.add_field(
                name="Matched Users (Keyword)",
                value="\n".join([f"{m.name} ({m.id})" for m in keyword_matches]) if keyword_matches else "None",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ErrorHandler.send_error(
                interaction,
                "First Run Failed",
                f"An error occurred while running first run scan.",
                error_type=e.__class__.__name__,
                show_help=True
            )

    async def handle_ban_action(self, member, reason, guild_id, is_keyword=False):
        config = self.config_manager.get_guild_config(guild_id)
        behavior = config['keyword_ban_behavior'] if is_keyword else config['id_ban_behavior']

        if behavior == "auto":
            await member.ban(reason=reason)
            if config['dm_on_ban']:
                # Your existing DM logic
                pass
            if config['log_bans']:
                # Your existing logging logic
                pass
        elif behavior == "notify" and config['notify_staff']:
            # Notify staff instead of banning
            channel_id = Utils.load_channels(Utils).get(guild_id)
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                await channel.send(f"⚠️ Found match for {member.mention}: {reason}")

    async def ban_with_appeal(self, member: discord.Member, reason: str, keyword: str = None, guild_id: str = None):
        """Ban a member and send them an appeal link if configured"""
        try:
            # Get guild config
            config = self.config_manager.get_guild_config(str(guild_id or member.guild.id))
            
            # Check ban behavior based on type
            behavior = config['keyword_ban_behavior'] if keyword else config['id_ban_behavior']
            if behavior == 'ignore':
                return
                
            # Handle notify-only mode
            if behavior == 'notify':
                channel_id = Utils.load_channels(Utils).get(str(member.guild.id))
                if channel_id and config['notify_staff']:
                    channel = self.bot.get_channel(channel_id)
                    await channel.send(f"⚠️ Found match for {member.mention}: {reason}")
                return

            # Proceed with ban
            await member.ban(reason=reason)
            Utils.increment_ban_count(Utils)

            log_details = f"Banned {member} ({member.id})"
            if keyword:
                log_details += f"\nTrigger: Keyword '{keyword}'"
            log_details += f"\nReason: {reason}"

            # Log the action
            if config['log_bans']:
                channel_id = Utils.load_channels(Utils).get(str(member.guild.id))
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    await self.logger.send_log_embed(
                        channel=channel,
                        action_type="Member Banned",
                        details=log_details,
                        target_id=str(member.id)
                    )

            # Handle DM if enabled
            if config['dm_on_ban']:
                dm_message = "You have been banned due to your alleged connection with Spawnism or forbidden content."
                if keyword:
                    dm_message += f"\nBan triggered by keyword: **{keyword}**."
                
                appeal_link = Utils.load_appeal_link(Utils, str(member.guild.id))
                if appeal_link:
                    dm_message += f"\nIf you believe this is a mistake, you may appeal here: {appeal_link}"
                    
                try:
                    await member.send(dm_message)
                except discord.HTTPException:
                    pass  # Failed to DM user

            # Log ban if enabled
            if config['log_bans']:
                channel_id = Utils.load_channels(Utils).get(str(member.guild.id))
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    await channel.send(f"🔨 Banned {member.mention}: {reason}")

        except discord.Forbidden:
            error_details = f"Failed to ban {member} ({member.id}): Missing permissions"
            await self.logger.send_log_embed(
                channel=channel,
                action_type="Ban Failed",
                details=error_details,
                target_id=str(member.id)
            )
            channel_id = Utils.load_channels(Utils).get(str(member.guild.id))
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="❌ Ban Failed",
                        description=f"Unable to ban {member.mention}: Missing permissions",
                        color=discord.Color.red()
                    )
                    await channel.send(embed=embed)
        except discord.HTTPException as e:
            error_details = f"Failed to ban {member} ({member.id}): {str(e)}"
            await self.logger.send_log_embed(
                channel=channel,
                action_type="Ban Failed",
                details=error_details,
                target_id=str(member.id)
            )
            channel_id = Utils.load_channels(Utils).get(str(member.guild.id))
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="❌ Ban Failed",
                        description=f"Unable to ban {member.mention}: {str(e)}",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Error Type",
                        value=f"`{e.__class__.__name__}`",
                        inline=False
                    )
                    await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        channel_id = Utils.load_channels(Utils).get(guild_id)
        channel = self.bot.get_channel(channel_id) if channel_id else None

        if member.id == self.bot.user.id:
            return

        banned = False
        for row in Utils.read_csv_as_list_of_dicts(Utils, "thelist.csv"):
            user_id = str(row.get('id', '')).strip()
            if user_id and str(member.id) == user_id:
                await self.utils.ban_with_appeal(member, 
                    f"Despawner banned {member.id}", 
                    guild_id=guild_id
                )
                if channel:
                    await channel.send(f'{member.mention} has been banned from the server.')
                banned = True
                break

        if not banned:
            username = str(member.name)
            nickname = str(member.nick) if member.nick else ""
            bio = str(member.global_name) if member.global_name else ""
            for field in [username, nickname, bio]:
                keyword = Utils.contains_banned_keyword(Utils, field)
                if keyword:
                    await self.utils.ban_with_appeal(member, 
                        f"Banned for forbidden keyword", 
                        keyword=keyword,
                        guild_id=guild_id
                    )
                    if channel:
                        await channel.send(
                            f'{member.mention} has been banned for forbidden keyword "{keyword}"'
                        )
                    break

    @ban_firstrun.error
    async def ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await ErrorHandler.send_error(
                interaction,
                "Permission Denied",
                "You need appropriate permissions to use this command.",
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

    @ban_group.command(name="reload", description="Reload banned IDs from CSV")
    @app_commands.checks.has_permissions(administrator=True)
    async def reload_bans(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        old_count = len(self.banned_ids)
        self.reload_banned_ids()
        new_count = len(self.banned_ids)
        
        await interaction.followup.send(
            f"✅ Banned IDs reloaded\nPrevious entries: {old_count}\nNew entries: {new_count}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(BanHandler(bot))