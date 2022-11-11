import logging
import os

import nextcord
from nextcord.ext.commands import Bot

from config import *

logging.basicConfig(filename="bot.log", filemode="w+", level=logging.INFO)

intents = nextcord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

bot = Bot(PREFIX, case_insensitivity=True, intents=intents)
bot.remove_command("help")

if TOKEN == "":
    TOKEN = input(
        "Token is not set in config.py, please enter the token there to surpress this input.\n\nToken: "
    )


@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.Game(f"{PREFIX}help"))
    usable_cogs = [
        "cogs." + x.name.replace(".py", "")
        for x in os.scandir("cogs")
        if not x.name.startswith("_")
    ]
    for cog in usable_cogs:
        bot.load_extension(cog)
        print(f"Loaded: {cog}")

    print(f"Online and Ready\nLogged in as {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Error in '{ctx.guild.name}' -> {error}")


@bot.command(name="reload_all", aliases=["reload-all", "reloadall"], hidden=True)
async def reload_all_cogs(ctx):
    if await bot.is_owner(ctx.author):
        usable_cogs = [
            "cogs." + x.name.replace(".py", "")
            for x in os.scandir("cogs")
            if not x.name.startswith("_")
        ]
        for cog in usable_cogs:
            try:
                bot.unload_extension(cog)
            except:
                pass

            bot.load_extension(cog)

        await ctx.message.add_reaction("✅")


bot.run(TOKEN)
