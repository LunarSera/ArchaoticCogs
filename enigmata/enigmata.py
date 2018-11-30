import os
import discord
from random import choice as randchoice
from .utils import checks
from discord.ext import commands
from .utils.dataIO import dataIO
from __main__ import send_cmd_help
import string
from .utils.chat_formatting import escape_mass_mentions, italics, pagify
from .utils.chat_formatting import *
import datetime
import time
from urllib.parse import quote_plus
import asyncio
import aiohttp
import random
from datetime import datetime
DB_VERSION = 2
try:
    from bs4 import BeautifulSoup
    soupAvailable = True
except:
    soupAvailable = False

class Enigmata:
    """These commands give you insight into the lore of Enigmata: Stellar War."""

    def __init__(self, bot):
        self.bot = bot
        self.lore = dataIO.load_json("data/enigmata/lore.json")
        self.images = dataIO.load_json("data/enigmata/image.index.json")
        self.session = aiohttp.ClientSession(loop=self.bot.loop)
        self.seen = dataIO.load_json('data/enigmata/seen.json')
        self.new_data = False

    async def data_writer(self):
        while self == self.bot.get_cog('Seen'):
            if self.new_data:
                dataIO.save_json('data/enigmata/seen.json', self.seen)
                self.new_data = False
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(30)

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
    @commands.group(no_pm=True, pass_context=True)
    async def fun(self, ctx):
        """A collection of fun commands to use."""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
			
    @fun.command(aliases=['nekofacts','catfact','catfacts'])
    async def nekofact(self):
        """Source of the infamous DynoBotTM Catfacts"""
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

    @fun.command(aliases=['lovecalc'])
    async def lovecalculator(self, lover: discord.Member, loved: discord.Member):
        """Calculate the love percentage!"""

        x = lover.display_name
        y = loved.display_name
        url = 'https://www.lovecalculator.com/love.php?name1={}&name2={}'.format(x.replace(" ", "+"),
                                                                                 y.replace(" ", "+"))
        async with aiohttp.get(url) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
            try:
                description = soupObject.find('div', attrs={'class': 'result score'}).get_text().strip()
            except:
                description = 'Dr. Love is busy right now'
        try:
            z = description[:2]
            z = int(z)
            if z > 50:
                emoji = '❤'
            else:
                emoji = '💔'
            title = 'Dr. Love says that the love percentage for {} and {} is:'.format(x, y)
        except:
            emoji = ''
            title = 'Dr. Love has left a note for you.'
        description = emoji + ' ' + description + ' ' + emoji
        em = discord.Embed(title=title, description=description, color=discord.Color.red())
        await self.bot.say(embed=em)

    @fun.command(hidden=True)
    async def lmgtfy(self, *, search_terms : str):
        """Creates a lmgtfy link"""
        search_terms = escape_mass_mentions(search_terms.replace("+","%2B").replace(" ", "+"))
        await self.bot.say("https://lmgtfy.com/?q={}".format(search_terms))

    @fun.command(no_pm=True, hidden=False)
    async def hug(self, user : discord.Member, intensity : int=1):
        """Because everyone likes hugs

        Up to 10 intensity levels."""
        name = italics(user.display_name)
        if intensity <= 0:
            msg = "(っ˘̩╭╮˘̩)っ" + name
        elif intensity <= 3:
            msg = "(っ´▽｀)っ" + name
        elif intensity <= 6:
            msg = "╰(*´︶`*)╯" + name
        elif intensity <= 9:
            msg = "(つ≧▽≦)つ" + name
        elif intensity >= 10:
            msg = "(づ￣ ³￣)づ{} ⊂(´・ω・｀⊂)".format(name)
        await self.bot.say(msg)

    @fun.command()
    async def urban(self, *, search_terms : str, definition_number : int=1):
        """Urban Dictionary search

        Definition number must be between 1 and 10"""
        def encode(s):
            return quote_plus(s, encoding='utf-8', errors='replace')

        # definition_number is just there to show up in the help
        # all this mess is to avoid forcing double quotes on the user

        search_terms = search_terms.split(" ")
        try:
            if len(search_terms) > 1:
                pos = int(search_terms[-1]) - 1
                search_terms = search_terms[:-1]
            else:
                pos = 0
            if pos not in range(0, 11): # API only provides the
                pos = 0                 # top 10 definitions
        except ValueError:
            pos = 0

        search_terms = "+".join([encode(s) for s in search_terms])
        url = "http://api.urbandictionary.com/v0/define?term=" + search_terms
        try:
            async with aiohttp.get(url) as r:
                result = await r.json()
            if result["list"]:
                definition = result['list'][pos]['definition']
                example = result['list'][pos]['example']
                defs = len(result['list'])
                msg = ("**Definition #{} out of {}:\n**{}\n\n"
                       "**Example:\n**{}".format(pos+1, defs, definition,
                                                 example))
                msg = pagify(msg, ["\n"])
                for page in msg:
                    await self.bot.say(page)
            else:
                await self.bot.say("Your search terms gave no results.")
        except IndexError:
            await self.bot.say("There is no definition #{}".format(pos+1))
        except:
            await self.bot.say("Error.")

    @commands.group(no_pm=True, pass_context=True)
    async def utility(self, ctx):
        """A collection of utility commands."""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @utility.command(pass_context=True)
    async def ping(self,ctx):
        """Latency from Bot to Server."""
        channel = ctx.message.channel
        t1 = time.perf_counter()
        await self.bot.send_typing(channel)
        t2 = time.perf_counter()
        await self.bot.say("Ping: {}ms".format(round((t2-t1)*1000)))

    @utility.command(pass_context=True, no_pm=True, name='seen')
    async def _seen(self, context, username: discord.Member):
        '''seen <@username>'''
        server = context.message.server
        author = username
        timestamp_now = context.message.timestamp
        if server.id in self.seen:
            if author.id in self.seen[server.id]:
                data = self.seen[server.id][author.id]
                timestamp_then = datetime.fromtimestamp(data['TIMESTAMP'])
                timestamp = timestamp_now - timestamp_then
                days = timestamp.days
                seconds = timestamp.seconds
                hours = seconds // 3600
                seconds = seconds - (hours * 3600)
                minutes = seconds // 60
                if sum([days, hours, minutes]) < 1:
                    ts = 'just now'
                else:
                    ts = ''
                    if days == 1:
                        ts += '{} day, '.format(days)
                    elif days > 1:
                        ts += '{} days, '.format(days)
                    if hours == 1:
                        ts += '{} hour, '.format(hours)
                    elif hours > 1:
                        ts += '{} hours, '.format(hours)
                    if minutes == 1:
                        ts += '{} minute ago'.format(minutes)
                    elif minutes > 1:
                        ts += '{} minutes ago'.format(minutes)
                em = discord.Embed(color=discord.Color.green())
                avatar = author.avatar_url if author.avatar else author.default_avatar_url
                em.set_author(name='{} was seen {}'.format(author.display_name, ts), icon_url=avatar)
                await self.bot.say(embed=em)
            else:
                message = 'I haven\'t seen {} yet.'.format(author.display_name)
                await self.bot.say('{}'.format(message))
        else:
            message = 'I haven\'t seen {} yet.'.format(author.display_name)
            await self.bot.say('{}'.format(message))

    async def on_message(self, message):
        if not message.channel.is_private and self.bot.user.id != message.author.id:
            if not any(message.content.startswith(n) for n in self.bot.settings.prefixes):
                server = message.server
                author = message.author
                ts = message.timestamp.timestamp()
                data = {}
                data['TIMESTAMP'] = ts
                if server.id not in self.seen:
                    self.seen[server.id] = {}
                self.seen[server.id][author.id] = data
                self.new_data = True

    @utility.command(pass_context=True, no_pm=True, aliases=['uinfo'])
    async def userinfo(self, ctx, *, user: discord.Member=None):
        """Shows users's informations"""
        author = ctx.message.author
        server = ctx.message.server

        if not user:
            user = author

        roles = [x.name for x in user.roles if x.name != "@everyone"]

        joined_at = self.fetch_joined_at(user, server)
        since_created = (ctx.message.timestamp - user.created_at).days
        since_joined = (ctx.message.timestamp - joined_at).days
        user_joined = joined_at.strftime("%d %b %Y %H:%M")
        user_created = user.created_at.strftime("%d %b %Y %H:%M")
        member_number = sorted(server.members,
                               key=lambda m: m.joined_at).index(user) + 1

        created_on = "{}\n({} days ago)".format(user_created, since_created)
        joined_on = "{}\n({} days ago)".format(user_joined, since_joined)

        game = "Chilling in {} status".format(user.status)

        if user.game is None:
            pass
        elif user.game.url is None:
            game = "Playing {}".format(user.game)
        else:
            game = "Streaming: [{}]({})".format(user.game, user.game.url)

        if roles:
            roles = sorted(roles, key=[x.name for x in server.role_hierarchy
                                       if x.name != "@everyone"].index)
            roles = ", ".join(roles)
        else:
            roles = "None"

        data = discord.Embed(description=game, colour=user.colour)
        data.add_field(name="Joined Discord on", value=created_on)
        data.add_field(name="Joined this server on", value=joined_on)
        data.add_field(name="Roles", value=roles, inline=False)
        data.set_footer(text="Member #{} | User ID:{}"
                             "".format(member_number, user.id))

        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name

        if user.avatar_url:
            data.set_author(name=name, url=user.avatar_url)
            data.set_thumbnail(url=user.avatar_url)
        else:
            data.set_author(name=name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @utility.command(pass_context=True, no_pm=True, aliases=['sinfo'])
    async def serverinfo(self, ctx):
        """Shows server's informations"""
        server = ctx.message.server
        online = len([m.status for m in server.members
                      if m.status != discord.Status.offline])
        total_users = len(server.members)
        text_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.text])
        voice_channels = len([x for x in server.channels
                             if x.type == discord.ChannelType.voice])
        passed = (ctx.message.timestamp - server.created_at).days
        created_at = ("Since {}. That's over {} days ago!"
                      "".format(server.created_at.strftime("%d %b %Y %H:%M"),
                                passed))

        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        data = discord.Embed(
            description=created_at,
            colour=discord.Colour(value=colour))
        data.add_field(name="Region", value=str(server.region))
        data.add_field(name="Users", value="{}/{}".format(online, total_users))
        data.add_field(name="Text Channels", value=text_channels)
        data.add_field(name="Voice Channels", value=voice_channels)
        data.add_field(name="Roles", value=len(server.roles))
        data.add_field(name="Owner", value=str(server.owner))
        data.set_footer(text="Server ID: " + server.id)

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")
#-----------------------------------------------------------------------------------------------------------------
    @commands.group(no_pm=True, pass_context=True)
    async def enigmata(self, ctx):
        """Enigmata Lore."""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @enigmata.command(hidden=True)
    async def story(self):
        """Says a random piece of lore from Enigmata: Stellar War"""
        await self.bot.say(randchoice(self.lore))
		
    @enigmata.command(pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def select(self, ctx, file=None, *, comment=None):
        """Upload a file from the bot."""

        message = ctx.message
        server = message.server

        if file == None:
            if os.listdir("data/enigmata/453668709396119562") == []:
                await self.bot.say("There is nothing saved yet. Use the save command to begin.")
                return

            msg = "Send `n/enigmata select 'filename'` to reupload.\nSend `n/enigmata delete 'filename'` to remove file from this list.'(do not add file extension)'\nRequires *Manage Server Permission*\n\nList of available files to upload:\n"
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
    @checks.admin_or_permissions(manage_server=True)
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
        dataIO.save_json("data/enigmata/image.index.json", self.images)
        await self.bot.say("{} has been deleted from my directory.".format(cmd))

    @enigmata.command(pass_context=True, no_pm=True, invoke_without_command=True)
    async def save(self, ctx, cmd):
        """Add an image to direct upload.\n Where cmd = name of your choice."""
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
        await self.bot.say("Upload an image for me to use! You have 1 minute.")
        while msg is not None:
            msg = await self.bot.wait_for_message(author=author, timeout=60)
            if msg is None:
                await self.bot.say("No image uploaded then.")
                break

            if msg.attachments != []:
                filename = msg.attachments[0]["filename"][-4:]
                directory = "data/enigmata/{}{}".format(server.id, filename)
                if cmd is None:
                    cmd = filename.split(".")[0]
                cmd = cmd.lower()
                directory = "data/enigmata/{}/{}{}".format(server.id, cmd, filename)
                self.images["server"][server.id][cmd] = directory
                dataIO.save_json("data/enigmata/image.index.json", self.images)
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
    f = "data/enigmata/image.index.json"
    if not dataIO.is_valid_json(f):
        print("Creating default image.index.json...")
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

def check_folder():
    if not os.path.exists('data/enigmata'):
        print('Creating enigmata/seen folder...')
        os.makedirs('data/seen')


def check_file():
    data = {}
    data['db_version'] = DB_VERSION
    f = 'data/enigmata/seen.json'
    if not dataIO.is_valid_json(f):
        print('Creating seen.json...')
        dataIO.save_json(f, data)
    else:
        check = dataIO.load_json(f)
        if 'db_version' in check:
            if check['db_version'] < DB_VERSION:
                data = {}
                data['db_version'] = DB_VERSION
                dataIO.save_json(f, data)
                print('SEEN: Database version too old, resetting!')
        else:
            data = {}
            data['db_version'] = DB_VERSION
            dataIO.save_json(f, data)
            print('SEEN: Database version too old, resetting!')


def setup(bot):
    check_folders()
    check_files()
    check_folder()
    check_file()
    n = Enigmata(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.data_writer())
    if soupAvailable:
        bot.add_cog(Enigmata(bot))
    else:
        raise RuntimeError("Required for LoveCalc. Run `pip3 install beautifulsoup4`")
