import os
import subprocess
import zipfile

import nextcord
from config import *
from nextcord.ext import commands

from ._functions import *


class Example(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.SERVICE_PATH = "/lib/systemd/system"
        self.BOT_ROOT_PATH = "/home/aki"

        with open("SERVICE_TEMPLATE.service") as f:
            self.SERVICE_TEMPLATE = f.read()

    async def cog_check(self, ctx: commands.Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command("setup")
    async def setup_new_bot(self, ctx: commands.Context, name: str):
        if ctx.message.attachments == []:
            return await ctx.reply("No attachment found")

        try:
            with open(self.BOT_ROOT_PATH + "/temp.zip") as f:
                ctx.message.attachments[0].save(f)
        except:
            return await ctx.reply("Error while saving zip file")

        try:
            os.mkdir(f"{self.BOT_ROOT_PATH}/{name}")
        except:
            return await ctx.reply("Error while making directory")

        try:
            with zipfile.ZipFile(self.BOT_ROOT_PATH + "/temp.zip", "r") as zip_ref:
                zip_ref.extractall(f"{self.BOT_ROOT_PATH}/{name}")
        except:
            return await ctx.reply("Error while extracting zip file")

        try:
            service = self.SERVICE_PATH.format(name=name, BOT_ROOT_PATH=self.BOT_ROOT_PATH)
            with open(f"{self.SERVICE_PATH}/discord-bot-{name}.service", "w+") as f:
                f.write(service)
        except:
            return await ctx.reply("Error while saving service file")

        try:
            subprocess.Popen(f"systemctl enable discord-bot-{name}.service", shell=True)
        except:
            return await ctx.reply("Error while enabling service file")

        try:
            subprocess.Popen(f"systemctl start discord-bot-{name}.service", shell=True)
        except:
            return await ctx.reply("Error while starting service")

def setup(bot):
    bot.add_cog(Example(bot))
