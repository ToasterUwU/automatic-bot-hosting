import os
import subprocess
import sys

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
            await ctx.message.attachments[0].save(self.BOT_ROOT_PATH + "/temp.zip")
        except:
            return await ctx.reply("Error while saving zip file")

        try:
            os.mkdir(f"{self.BOT_ROOT_PATH}/{name}")
        except FileExistsError:
            pass
        except:
            return await ctx.reply("Error while making directory")

        try:
            subprocess.Popen(
                f"unzip -o -q {self.BOT_ROOT_PATH}/temp.zip -d {self.BOT_ROOT_PATH}/{name}",
                shell=True,
            ).communicate()
        except:
            return await ctx.reply("Error while extracting zip file")

        try:
            service = self.SERVICE_TEMPLATE.format(
                name=name, BOT_ROOT_PATH=self.BOT_ROOT_PATH
            )
            with open(f"{self.SERVICE_PATH}/discord-bot-{name}.service", "w+") as f:
                f.write(service)
        except:
            return await ctx.reply("Error while saving service file")

        try:
            subprocess.Popen(
                f"python3 -m venv {self.BOT_ROOT_PATH}/{name}/.venv",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return await ctx.reply("Error while making venv.")

        try:
            subprocess.Popen(
                f"{self.BOT_ROOT_PATH}/{name}/.venv/bin/pip3 install -U -r {self.BOT_ROOT_PATH}/{name}/requirements.txt",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return await ctx.reply("Error while getting dependencies.")

        try:
            subprocess.Popen(
                f"systemctl enable discord-bot-{name}.service",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return await ctx.reply("Error while enabling service file")

        try:
            subprocess.Popen(
                f"systemctl restart discord-bot-{name}.service",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return await ctx.reply("Error while starting service")

        await ctx.reply("Bot set up and running.")


def setup(bot):
    bot.add_cog(Example(bot))
