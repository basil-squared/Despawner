import discord
from discord import app_commands
from discord.ext import commands
from utils import Utils

class BanHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utils = Utils()

    @app_commands.command(name="firstrun", description="Bans all applicable users")
    @app_commands.checks.has_permissions(ban_members=True)
    async def firstrun(self, interaction: discord.Interaction):
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

async def setup(bot):
    await bot.add_cog(BanHandler(bot))