import discord
from discord.ext import commands, tasks
from itertools import cycle
from utils.utils import Utils

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utils = Utils()
        self.change_status.start()

    def cog_unload(self):
        self.change_status.cancel()

    @tasks.loop(minutes=5)
    async def change_status(self):
        ban_count = self.utils.load_ban_count()
        statuses = cycle([
            discord.Activity(
                type=discord.ActivityType.playing,
                name=f"with the souls of {ban_count} banned spawnists"
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="to ban appeals"
            ),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="Respawn Protection"
            ),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="Escape From Banland"
            )
        ])
        await self.bot.change_presence(activity=next(statuses))

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded")

async def setup(bot):
    await bot.add_cog(BotStatus(bot))