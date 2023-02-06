import os
import subprocess
import sys

import nextcord
from nextcord.ext import commands

from config import *
from internal_tools.configuration import CONFIG
from internal_tools.discord import *


class BotSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.SERVICE_PATH = "/lib/systemd/system"
        self.BOT_ROOT_PATH = "/home/aki"

        with open("SERVICE_TEMPLATE.service") as f:
            self.SERVICE_TEMPLATE = f.read()

    async def cog_application_command_check(self, interaction: nextcord.Interaction):
        """
        You need to be the Owner of the Bot to use this.
        """
        if interaction.user:
            if isinstance(interaction.user, nextcord.Member):
                user = interaction.user._user
            else:
                user = interaction.user

            return await self.bot.is_owner(user)
        else:
            return False

    def setup_new_bot(self, name: str):
        try:
            service = self.SERVICE_TEMPLATE.format(
                name=name, BOT_ROOT_PATH=self.BOT_ROOT_PATH
            )
            with open(f"{self.SERVICE_PATH}/discord-bot-{name}.service", "w+") as f:
                f.write(service)
        except:
            return "Error while saving service file"

        try:
            subprocess.Popen(
                f"python3 -m venv {self.BOT_ROOT_PATH}/{name}/.venv",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return "Error while making venv."

        try:
            subprocess.Popen(
                f"{self.BOT_ROOT_PATH}/{name}/.venv/bin/pip3 install -U -r {self.BOT_ROOT_PATH}/{name}/requirements.txt",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return "Error while getting dependencies."

        try:
            subprocess.Popen(
                f"systemctl enable discord-bot-{name}.service",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return "Error while enabling service file"

        try:
            subprocess.Popen(
                f"systemctl restart discord-bot-{name}.service",
                shell=True,
                stderr=sys.stderr,
            ).communicate()
        except:
            return "Error while starting service"

        return "Bot set up and running."

    @nextcord.slash_command(
        name="manual-setup",
        description="Uses a source_code.zip to setup Bot. This requires manual updates.",
        guild_ids=CONFIG["GENERAL"]["OWNER_COG_GUILD_IDS"],
    )
    async def manual_setup(
        self,
        interaction: nextcord.Interaction,
        name: str,
        source_code: nextcord.Attachment,
    ):
        await interaction.response.defer()

        try:
            await source_code.save(self.BOT_ROOT_PATH + "/temp.zip")
        except:
            await interaction.send("Error while saving zip file")
            return

        try:
            os.mkdir(f"{self.BOT_ROOT_PATH}/{name}")
        except FileExistsError:
            pass
        except:
            await interaction.send("Error while making directory")
            return

        try:
            subprocess.Popen(
                f"unzip -o -q {self.BOT_ROOT_PATH}/temp.zip -d {self.BOT_ROOT_PATH}/{name}",
                shell=True,
            ).communicate()
        except:
            await interaction.send("Error while extracting zip file")
            return

        await interaction.send(self.setup_new_bot(name))

    @nextcord.slash_command(
        name="github-setup",
        description="Uses a GitHub repo to setup Bot. This will automatically update from main branch.",
        guild_ids=CONFIG["GENERAL"]["OWNER_COG_GUILD_IDS"],
    )
    async def github_setup(
        self, interaction: nextcord.Interaction, github_repo_name: str
    ):
        pass


def setup(bot):
    bot.add_cog(BotSetup(bot))
