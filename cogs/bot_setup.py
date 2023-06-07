import asyncio
import json
import os
import shutil
import subprocess
import sys
from typing import Optional

import aiohttp
import nextcord
from git.repo import Repo
from nextcord.ext import commands, tasks

from config import *
from internal_tools.configuration import CONFIG, JsonDictSaver
from internal_tools.discord import *


class BotSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.SERVICE_PATH = "/lib/systemd/system"
        self.BOT_ROOT_PATH = "/home/aki"

        with open("SERVICE_TEMPLATE.service", "r") as f:
            self.SERVICE_TEMPLATE = f.read()

        self.repodirs_to_update = JsonDictSaver("repodirs_to_update")

        self.update_repos.start()

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

    def get_comparison_link(self, repo: Repo, from_commit: str, to_commit: str):
        repo_name = repo.remotes.origin.url.replace(".git", "").rsplit(":", 1)[-1]
        repo_name = "/".join(repo_name.rsplit("/")[-2:])

        return f"https://github.com/{repo_name}/compare/{from_commit}..{to_commit}"

    async def log(self, title: str, message: str):
        if CONFIG["GENERAL"]["ERROR_WEBHOOK_URL"]:
            async with aiohttp.ClientSession() as session:
                webhook = nextcord.Webhook.from_url(
                    CONFIG["GENERAL"]["ERROR_WEBHOOK_URL"], session=session
                )
                await webhook.send(embed=fancy_embed(title, message))

    async def setup_bot(
        self, name: str, restart: bool = True, token: Optional[str] = None
    ):
        try:
            service = self.SERVICE_TEMPLATE.format(
                name=name, BOT_ROOT_PATH=self.BOT_ROOT_PATH
            )
            with open(f"{self.SERVICE_PATH}/discord-bot-{name}.service", "w+") as f:
                f.write(service)
        except:
            return "Error while saving service file"

        try:
            process = subprocess.Popen(
                f"python3 -m venv {self.BOT_ROOT_PATH}/{name}/.venv",
                shell=True,
                stderr=sys.stderr,
            )

            await asyncio.get_running_loop().run_in_executor(None, process.communicate)
        except:
            return "Error while making venv."

        try:
            process = subprocess.Popen(
                f"{self.BOT_ROOT_PATH}/{name}/.venv/bin/pip3 install -U -r {self.BOT_ROOT_PATH}/{name}/requirements.txt",
                shell=True,
                stderr=sys.stderr,
            )

            await asyncio.get_running_loop().run_in_executor(None, process.communicate)
        except:
            return "Error while getting dependencies."

        if token:
            try:
                if not os.path.exists(
                    f"{self.BOT_ROOT_PATH}/{name}/config/GENERAL.json"
                ):
                    shutil.copyfile(
                        f"{self.BOT_ROOT_PATH}/{name}/config/default/GENERAL.json",
                        f"{self.BOT_ROOT_PATH}/{name}/config/GENERAL.json",
                    )

                with open(f"{self.BOT_ROOT_PATH}/{name}/config/GENERAL.json", "r") as f:
                    general_config = json.load(f)

                general_config["TOKEN"] = token

                with open(f"{self.BOT_ROOT_PATH}/{name}/config/GENERAL.json", "w") as f:
                    json.dump(general_config, f, indent=2)

            except:
                return "Error while entering Token."

        try:
            process = subprocess.Popen(
                f"systemctl daemon-reload",
                shell=True,
                stderr=sys.stderr,
            )

            await asyncio.get_running_loop().run_in_executor(None, process.communicate)
        except:
            return "Error while reloading service files"

        try:
            process = subprocess.Popen(
                f"systemctl enable discord-bot-{name}.service",
                shell=True,
                stderr=sys.stderr,
            )

            await asyncio.get_running_loop().run_in_executor(None, process.communicate)
        except:
            return "Error while enabling service file"

        if restart:
            try:
                process = subprocess.Popen(
                    f"systemctl restart discord-bot-{name}.service",
                    shell=True,
                    stderr=sys.stderr,
                )

                await asyncio.get_running_loop().run_in_executor(
                    None, process.communicate
                )
            except:
                return "Error while starting service"

        return "Bot set up and running."

    @tasks.loop(minutes=10)
    async def update_repos(self):
        for repo_dir, should_update in self.repodirs_to_update.items():
            if should_update:
                repo = Repo(repo_dir)

                await asyncio.get_running_loop().run_in_executor(
                    None, repo.remotes.origin.fetch
                )

                local_branch = repo.head.ref
                remote_branch = local_branch.tracking_branch()
                if remote_branch:
                    missing_commits = list(
                        repo.iter_commits(f"{local_branch.name}..{remote_branch.name}")
                    )

                    if len(missing_commits) > 0:
                        before_update_commit = local_branch.commit.hexsha

                        commit_hashes = "\n".join([x.hexsha for x in missing_commits])

                        repo.remote().pull()

                        bot_name = repo_dir.rsplit("/", 1)[1]
                        end_message = await self.setup_bot(
                            bot_name, restart=repo_dir != os.getcwd()
                        )
                        if end_message == "Bot set up and running.":
                            await self.log(
                                "UPDATED",
                                f"{repo_dir} with {len(missing_commits)} commit(s)\n{commit_hashes}\n\n[See what changed]({self.get_comparison_link(repo, before_update_commit, missing_commits[0].hexsha)})",
                            )
                        else:
                            await self.log(
                                "ERROR", f"{repo_dir} Couldnt update.\n{end_message}"
                            )

                        if repo_dir == os.getcwd():
                            process = subprocess.Popen(
                                f"systemctl restart discord-bot-{bot_name}.service",
                                shell=True,
                                stderr=sys.stderr,
                            )

                            await asyncio.get_running_loop().run_in_executor(
                                None, process.communicate
                            )

                            break  # Bot will restart, so dont start anything new
                else:
                    await self.log("ERROR", f"{repo_dir} Couldnt reach GitHub")

    @update_repos.error
    async def update_repos_on_error(self, e: BaseException):
        self.update_repos.restart()

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
        token: Optional[str] = None,
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

        try:
            os.remove(f"{self.BOT_ROOT_PATH}/temp.zip")
        except:
            await interaction.send("Error while deleting temp zip file")
            return

        end_message = await self.setup_bot(name, token=token)
        await interaction.send(end_message)

        await self.log("SETUP", f"{self.BOT_ROOT_PATH}/{name} in `MANUAL` mode")

    @nextcord.slash_command(
        name="github-setup",
        description="Uses a GitHub repo to setup Bot. This will automatically update from main branch.",
        guild_ids=CONFIG["GENERAL"]["OWNER_COG_GUILD_IDS"],
    )
    async def github_setup(
        self,
        interaction: nextcord.Interaction,
        github_repo_name: str,
        token: Optional[str] = None,
    ):
        await interaction.response.defer()

        if "/" not in github_repo_name:
            github_repo_name = "ToasterUwU/" + github_repo_name

        if github_repo_name.count("/") > 1:
            await interaction.send(
                "More than one / found, something aint right with that repo name."
            )
            return

        name = github_repo_name.split("/")[1]

        try:
            Repo.clone_from(
                f"git@github.com:{github_repo_name}.git",
                f"{self.BOT_ROOT_PATH}/{name}",
            )
        except:
            await interaction.send(
                f"Error while cloning repo from git@github.com:{github_repo_name}.git"
            )
            return

        self.repodirs_to_update[f"{self.BOT_ROOT_PATH}/{name}"] = True
        self.repodirs_to_update.save()

        end_message = await self.setup_bot(name, token=token)
        await interaction.send(end_message)

        await self.log("SETUP", f"{self.BOT_ROOT_PATH}/{name} in `AUTOMATIC` mode")

    @nextcord.slash_command(
        name="toggle-auto-update",
        description="Toggles auto pull from master brach for a repo.",
        guild_ids=CONFIG["GENERAL"]["OWNER_COG_GUILD_IDS"],
    )
    async def toggle_auto_update(self, interaction: nextcord.Interaction, name: str):
        repo_dir = f"{self.BOT_ROOT_PATH}/" + name
        if repo_dir not in self.repodirs_to_update:
            await interaction.send("This repo isnt setup yet.")
            return

        self.repodirs_to_update[repo_dir] = not self.repodirs_to_update[repo_dir]
        self.repodirs_to_update.save()

        await interaction.send(
            f"Update status for {repo_dir} = {self.repodirs_to_update[repo_dir]}"
        )

    @toggle_auto_update.on_autocomplete("name")
    async def autocomplete_bot_name(
        self, interaction: nextcord.Interaction, name: Optional[str]
    ):
        if name == None:
            await interaction.response.send_autocomplete(
                [
                    x.replace(f"{self.BOT_ROOT_PATH}/", "")
                    for x in self.repodirs_to_update.keys()
                ][:20]
            )
        else:
            await interaction.response.send_autocomplete(
                [
                    x.replace(f"{self.BOT_ROOT_PATH}/", "")
                    for x in self.repodirs_to_update.keys()
                    if x.replace(f"{self.BOT_ROOT_PATH}/", "")
                    .casefold()
                    .startswith(name.casefold())
                ][:20]
            )


def setup(bot):
    bot.add_cog(BotSetup(bot))
