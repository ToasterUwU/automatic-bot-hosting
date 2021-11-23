import nextcord
from config import *
from nextcord.ext import commands

from ._functions import *


class Example(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return await self.bot.is_owner(ctx.author)


def setup(bot):
    bot.add_cog(Example(bot))
