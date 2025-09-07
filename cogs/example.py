from discord.ext import commands
import discord

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded")

    @discord.app_commands.command(name="ping", description="Check if bot is alive")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))