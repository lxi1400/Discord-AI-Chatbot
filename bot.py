import discord, os, requests, pymongo, asyncio
from keep_alive import keep_alive
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

# -------- Utils -------- #
class utils:
    def clear():
        os.system('cls')
    def rename(title):
        os.system("title {}".format(title))
class request:
    def get(message, apikey, bid, id):
        r = requests.get(url=f"http://api.brainshop.ai/get?bid={bid}&key={apikey}&uid={id}&msg={message}")
        return r.json()['cnt']


# -------- Set Variables -------- #

keep_alive()
database = pymongo.MongoClient(os.getenv('DATABASEURL'))
collection = database.get_database("chatbot").get_collection("settings")
apikey = os.getenv('APIKEY')
bid = os.getenv('BID')
token = os.getenv('TOKEN')
client = discord.Client()
client = commands.Bot(command_prefix="%", intents=discord.Intents.all())
client.remove_command('help')

async def status():
    while True:
        await client.change_presence(status=discord.Status.idle,activity=discord.Activity(type=discord.ActivityType.watching, name='for %help | github.com/lxi1400'))
        await asyncio.sleep(30)
        await client.change_presence(status=discord.Status.idle, activity=discord.Game('%ask | github.com/lxi1400'))
        await asyncio.sleep(5)

# -------- Database Checking -------- #

async def is_enabled(guild):
    if collection.find_one({"guild-id": guild})["enabled"] == True:
        return True
    else:
        return False


async def is_blacklisted(channel, guild):
    if channel in collection.find_one({"guild-id": guild})["blacklisted-channels"]:
        return True
    else:
        return False


async def is_existing_database(guild):
    if not collection.find_one({ "guild-id": guild.id}):
        collection.insert_one({"enabled": False, "blacklisted-channels": [],"guild-id": guild.id})
        print(f"{guild.name} was not in the database, but has been added!")

# -------- On Ready -------- #

@client.event
async def on_ready():
    utils.clear()
    utils.rename("Chat Bot [Logged into {}#{}]".format(str(client.user.name), str(client.user.discriminator)))
    print(f"Logged into => {client.user.name}#{client.user.discriminator}")
    for guild in client.guilds:
        await is_existing_database(guild)
    await status()

# -------- On Join/Leave -------- #

@client.event
async def on_guild_join(guild):
    collection.insert_one({"enabled": False, "blacklisted-channels": [], "guild-id": guild.id})


@client.event
async def on_guild_remove(guild):
    collection.delete_one({"guild-id": guild.id })  

# -------- On Message -------- #

@client.event
async def on_message(message):
    enabled = await is_enabled(message.guild.id)
    blacklisted = await is_blacklisted(message.channel.id, message.guild.id)
    await client.process_commands(message)
    if message.author.id == client.user.id:
        return
    if enabled == False:
        return
    if blacklisted == True:
        return
    if len(message.content) < 0:
        return
    await message.channel.send(f"{message.author.mention}, {request.get(message.content, apikey, bid, message.author.id)}")


# -------- Commands -------- #

@client.command()
@commands.has_permissions(manage_messages =True)
async def disable(ctx):
    enabled = await is_enabled(ctx.guild.id)
    if enabled == True:
        collection.update_one({"guild-id": ctx.guild.id }, { "$set": { "enabled": False}})
        await ctx.reply("The chatbot is now disabled")
    else:
        await ctx.reply("The chatbot is already disabled!")


@client.command()
@commands.has_permissions(manage_messages =True)
async def enable(ctx):
    enabled = await is_enabled(ctx.guild.id)
    if enabled == True:
        await ctx.reply("The chatbot is already enabled!")
    else:
        collection.update_one({"guild-id": ctx.guild.id }, { "$set": { "enabled": True}})
        await ctx.reply("The chatbot is now enabled!")




@client.command()
@commands.has_permissions(manage_channels=True)
async def blacklist(ctx, channel: discord.TextChannel=None):
    if channel == None:
        await ctx.reply("You must insert a channel! Example: `%blacklist #chat`")
        return
    blacklisted = await is_blacklisted(channel.id, ctx.guild.id)
    if blacklisted == True:
        await ctx.reply("That channel is already blacklisted")
    else:
        collection.update_one({"guild-id": ctx.guild.id }, { "$push": { "blacklisted-channels": channel.id}})
        await ctx.reply("That channel is now blacklisted!")




@client.command()
@commands.has_permissions(manage_channels=True)
async def unblacklist(ctx, channel: discord.TextChannel = None):
    if channel == None:
        await ctx.reply("You must insert a channel! Example: `%unblacklist #chat`")
        return
    blacklisted = await is_blacklisted(channel.id, ctx.guild.id)
    if blacklisted == False:
        await ctx.reply("That channel is not blacklisted")
    else:
        collection.update_one({"guild-id": ctx.guild.id }, { "$pull": { "blacklisted-channels": channel.id}})
        await ctx.reply("That channel is now un-blacklisted!")


@client.command()
async def help(ctx):
    embed=discord.Embed(title="Help", description="Below are the bot commands. Commands with [] are required arguments, while <> are optional arguments.", color=0x9ea1ff)
    embed.add_field(name="%enable", value="Enables the chatbot", inline=False)
    embed.add_field(name="%disable", value="Disables the chatbot", inline=False)
    embed.add_field(name="%blacklist [#channel]", value="Blacklists the bot from responding to messages in the mentioned channel", inline=False)
    embed.add_field(name="%unblacklist [#channel]", value="Unblacklists the bot from responding to messages in the mentioned channel", inline=False)
    embed.add_field(name="%ask [text]", value="Asks the chatbot the inserted question", inline=False)
    embed.set_footer(text="github.com/lxi1400")
    await ctx.reply(embed=embed)

@client.command()
async def ask(ctx, *, text=None):
    if text == None:
        await ctx.reply("You must insert text to ask! Example: `%ask What is my name?`")
        return
    msg = request.get(text, apikey, bid, ctx.author.id)
    await ctx.reply(msg)


# -------- Error Handler -------- #

@disable.error
async def disableerr(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to have `manage_messages` to use this command!")

@enable.error
async def enableerr(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to have `manage_messages` to use this command!")

@blacklist.error
async def blacklisterr(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to have `manage_channels` to use this command!")

@unblacklist.error
async def unblacklisterror(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to have `manage_channels` to use this command!")

# -------- Run Bot -------- #


client.run(token)
