import os
import discord
from random import choice as randchoice
from .utils import checks
from discord.ext import commands
from .utils.dataIO import dataIO
from __main__ import send_cmd_help

class Enigmata:
    """These commands give you insight into the lore of Enigmata: Stellar War."""

    def __init__(self, bot):
        self.bot = bot
        self.lore = dataIO.load_json("data/enigmata/lore.json")

    @commands.group(no_pm=True, pass_context=True)
    async def enigmata(self, ctx):
        """Enigmata Lore."""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @enigmata.command()
    async def story(self):
        """Says a random piece of lore from Enigmata: Stellar War"""
        await self.bot.say(randchoice(self.lore))

def check_folders():
    if not os.path.exists("data/enigmata/"):
        print("Creating data/enigmata/ folder...")
        os.makedirs("data/enigmata/")


def check_files():
    """Makes sure the cog data exists"""
    if not os.path.isfile("data/enigmata/lore.json"):
        raise RuntimeError(
            "Required data is missing. Please reinstall this cog.")


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Enigmata(bot))
