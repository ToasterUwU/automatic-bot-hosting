import json
import os
from collections import UserDict

import nextcord
from config import *


class Config(UserDict):
    def __init__(self, name:str, __dict = ..., **kwargs) -> None:
        super().__init__(__dict=__dict, **kwargs)
        self.filename = f"{name}.json"
        if not os.path.exists(self.filename):
            with open(self.filename, "w+") as f:
                f.write("{}")

        with open(self.filename, "r") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.data, f)

    def __del__(self):
        self.save()

def fancy_embed(title="", description="", fields={}, color=EMBED_COLOR, inline=False):
    embed = nextcord.Embed(title=title, description=description, color=color)
    for name, val in fields.items():
        embed.add_field(name=name, value=val, inline=inline)
    embed.set_footer(text="Made by: Aki ToasterUwU#0001")

    return embed
