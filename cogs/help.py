import inspect
from inspect import Parameter

from config import *
from nextcord.ext import commands

from ._functions import *


class Help(commands.Cog):
    """
    Help Command
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def eval_cog_check(self, cog: commands.Cog, ctx: commands.Context):
        cog_check_async = inspect.iscoroutinefunction(cog.cog_check)
        if cog.cog_check != None:
            if cog_check_async:
                return await cog.cog_check(ctx)
            else:
                return cog.cog_check(ctx)

    async def generate_usage(
        self, ctx: commands.Context, command_name: str, show_hidden=False
    ):
        command = self.bot.get_command(command_name)
        if command == None:
            return

        if show_hidden == False and command.hidden:
            try:
                cog = self.bot.get_cog(command.cog_name)
            except:
                return

            if await self.eval_cog_check(cog, ctx):
                show_hidden = True
            else:
                return

        text = f"{PREFIX}"
        if len(command.aliases) == 0:
            text += command_name + " "

        elif len(command.aliases) == 1:
            text += f"[{command_name}/{command.aliases[0]}] "

        else:
            aliases = "|".join(command.aliases)
            text += f"[{command_name}/{aliases}] "

        param_prefixes = {
            nextcord.Role: "@",
            nextcord.Member: "@",
            nextcord.TextChannel: "#",
        }

        params = ""
        for name, param in command.clean_params.items():
            if param.annotation in param_prefixes:
                name = param_prefixes[param.annotation] + name

            if param.default == Parameter.empty:
                params += f"<{name}> "
            else:
                if param.default == "":
                    default = "empty"
                else:
                    default = param.default

                params += f"<{name}={default}>"

        text += params

        return text

    async def generate_command_list(self, cog: commands.Cog, show_hidden=False):
        text = ""

        for command in cog.get_commands():
            if show_hidden == False and command.hidden:
                continue

            if command.help == None:
                text += f"`{PREFIX}{command}`\n\n"

            else:
                text += f"`{PREFIX}{command}` {command.help}\n\n"
        return text

    @commands.command(name="help")
    async def show_help(self, ctx, command=None):
        """Shows this message"""
        if await self.bot.is_owner(ctx.author):
            show_hidden = True
        else:
            show_hidden = False

        if command == None:
            embed = fancy_embed(self.bot.user.name)
            for _, cog in self.bot.cogs.items():

                text = await self.generate_command_list(cog, show_hidden=show_hidden)
                if text == "":
                    continue
                embed.add_field(
                    name=f"**{cog.qualified_name}**",
                    value=text,
                    inline=False,
                )

        else:
            text = await self.generate_usage(ctx, command, show_hidden=show_hidden)
            if text == None:
                return await ctx.send(f"This command doesnt exist. Try: {PREFIX}help")

            else:
                embed = fancy_embed(f"Help for {PREFIX}{command}", text)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
