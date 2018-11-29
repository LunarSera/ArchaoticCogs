import os
import discord
from random import choice as randchoice
from .utils import checks
from discord.ext import commands
from .utils.dataIO import dataIO
from __main__ import send_cmd_help
import string
from .utils.chat_formatting import *
import asyncio
import aiohttp
import random

class Enigmata:
    """These commands give you insight into the lore of Enigmata: Stellar War."""

    def __init__(self, bot):
        self.bot = bot
        self.lore = dataIO.load_json("data/enigmata/lore.json")
        self.catfacts = dataIO.load_json("data/enigmata/catfacts.json")
        self.images = dataIO.load_json("data/enigmata/settings.json")
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def __unload(self):
        self.session.close()

    async def first_word(self, msg):
        return msg.split(" ")[0].lower()

    async def get_prefix(self, server, msg):
        prefixes = self.bot.settings.get_prefixes(server)
        for p in prefixes:
            if msg.startswith(p):
                return p
        return None
		
    async def part_of_existing_command(self, alias, server):
        '''Command or alias'''
        for command in self.bot.commands:
            if alias.lower() == command.lower():
                return True
        return False

    async def make_server_folder(self, server):
        if not os.path.exists("data/enigmata/{}".format(server.id)):
            print("Creating server folder")
            os.makedirs("data/enigmata/{}".format(server.id))

    async def on_message(self, message):
        if len(message.content) < 2 or message.channel.is_private:
            return

        msg = message.content
        server = message.server
        channel = message.channel
        prefix = await self.get_prefix(server, msg)
        if not prefix:
            return
        alias = await self.first_word(msg[len(prefix):])

        if alias in self.images["server"][server.id]:
            image = self.images["server"][server.id][alias]
            await self.bot.send_typing(channel)
            await self.bot.send_file(channel, image)

    async def check_command_exists(self, command, server):
        if command in self.images["server"][server.id]:
            return True
        elif await self.part_of_existing_command(command, server):
            return True
        else:
            return False
			
#    def __unload(self):
#    if self.__session:
#      asyncio.get_event_loop().create_task(self.__session.close())

    @commands.command(aliases=['nekofacts'])
    async def nekofact(self):
        try:
            url = 'https://catfact.ninja/fact'
            conn = aiohttp.TCPConnector(verify_ssl=False)
            session = aiohttp.ClientSession(connector=conn)
            async with session.get(url) as response:
                fact = (await response.json())['fact']
                await self.bot.say(fact)
                session.close()
        except:
            await self.bot.say("I was unable to get a cat fact.")

    @commands.group(no_pm=True, pass_context=True)
    async def enigmata(self, ctx):
        """Enigmata Lore."""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @enigmata.command()
    async def story(self):
        """Says a random piece of lore from Enigmata: Stellar War"""
        await self.bot.say(randchoice(self.lore))
		
    @enigmata.command(pass_context=True)
    async def upload(self, ctx, file=None, *, comment=None):
        """Upload a file from your local folder"""

        message = ctx.message
        server = message.server

        if file == None:
            if os.listdir("data/enigmata/453668709396119562") == []:
                await self.bot.say("No files to upload. Put them in `data/enigmata/453668709396119562`")
                return

            msg = "Send `n/enigmata upload 'filename'` to reupload.\nList of available files to upload:\n"
            for file in os.listdir("data/enigmata/453668709396119562"):
                msg += "`{}`\n".format(file)
            await self.bot.say(msg)
            return

        if "." not in file:
            for fname in os.listdir("data/enigmata/453668709396119562"):
                if fname.startswith(file):
                    file += "." + fname.partition(".")[2]
                    break

        if os.path.isfile("data/enigmata/453668709396119562/{}".format(file)) is True:
                await self.bot.upload(fp="data/enigmata/453668709396119562/{}".format(file))
        else:
            await self.bot.say(
                "That file doesn't seem to exist. Make sure it is the good name, try to add the extention (especially if two files have the same name)"
            )


    @enigmata.command(pass_context=True, no_pm=True, invoke_without_command=True)
    @checks.admin_or_permissions(manage_messages=True)
    async def delete(self, ctx, cmd):
        """Removes selected image."""
        author = ctx.message.author
        server = ctx.message.server
        channel = ctx.message.channel
        cmd = cmd.lower()
        if server.id not in self.images["server"]:
            await self.bot.say("I have no images on this server!")
            return
        if cmd not in self.images["server"][server.id]:
            await self.bot.say("{} is not an image for this server!".format(cmd))
            return
        os.remove(self.images["server"][server.id][cmd])
        del self.images["server"][server.id][cmd]
        dataIO.save_json("data/enigmata/settings.json", self.images)
        await self.bot.say("{} has been deleted from this server!".format(cmd))

    @enigmata.command(pass_context=True, no_pm=True, invoke_without_command=True)
    async def save(self, ctx, cmd):
        """Add an image to direct upload."""
        author = ctx.message.author
        server = ctx.message.server
        channel = ctx.message.channel
        prefix = await self.get_prefix(server, ctx.message.content)
        msg = ctx.message
        if server.id not in self.images["server"]:
            await self.make_server_folder(server)
            self.images["server"][server.id] = {}
        if cmd is not "":
            if await self.check_command_exists(cmd, server):
                await self.bot.say("{} is already in the list, try another!".format(cmd))
                return
            else:
                await self.bot.say("{} added as the command!".format(cmd))
        await self.bot.say("Upload an image for me to use!")
        while msg is not None:
            msg = await self.bot.wait_for_message(author=author, timeout=60)
            if msg is None:
                await self.bot.say("No image uploaded then.")
                break

            if msg.attachments != []:
                filename = msg.attachments[0]["filename"][-5:]
                
                directory = "data/enigmata/{}/{}".format(server.id, filename)
                if cmd is None:
                    cmd = filename.split(".")[0]
                cmd = cmd.lower()
                seed = ''.join(random.sample(string.ascii_uppercase + string.digits, k=5))
                directory = "data/enigmata/{}/{}-{}".format(server.id, seed, filename)
                self.images["server"][server.id][cmd] = directory
                dataIO.save_json("data/enigmata/settings.json", self.images)
                async with self.session.get(msg.attachments[0]["url"]) as resp:
                    test = await resp.read()
                    with open(self.images["server"][server.id][cmd], "wb") as f:
                        f.write(test)
                await self.bot.send_message(channel, "{} has been added to my files!"
                                            .format(cmd))
                break
            if msg.content.lower().strip() == "exit":
                await self.bot.say("Your changes have been saved.")
                break

def check_folder():
    if not os.path.exists("data/enigmata"):
        print("Creating data/enigmata folder")
        os.makedirs("data/enigmata")

def check_file():
    data = {"server":{}}
    f = "data/enigmata/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating default settings.json...")
        dataIO.save_json(f, data)

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
    check_folder()
    check_file()
    bot.add_cog(Enigmata(bot))
