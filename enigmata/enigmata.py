import os
from random import choice
import discord
from discord.ext import commands
from .utils.dataIO import dataIO


class Enigmata:

    def __init__(self, bot):
        self.bot = bot
        self.lore = dataIO.load_json("data/enigmata/lore.json")

    @commands.command()
    async def lore(self):
        """Says a random piece of lore from Enigmata: Stellar War"""
        await self.bot.say(choice(self.lore))


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
