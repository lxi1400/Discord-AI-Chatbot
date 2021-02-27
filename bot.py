import discord, os, requests

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


# -------- Set Varibles -------- #
apikey = input("Insert API key > ")
bid = input("Insert Brain ID (BID) > ")
token = input("Insert Token > ")
intents = discord.Intents.all()
client = discord.Client(intents=intents)


# -------- On Ready -------- #

@client.event
async def on_ready():
    utils.clear()
    utils.rename("Chat Bot [Logged into {}#{}]".format(str(client.user.name), str(client.user.discriminator)))
    print(f"Logged into => {client.user.name}#{client.user.discriminator}")


# -------- On Message -------- #

@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return
    print("{} > {}".format(message.content, message.author.name))
    msg = request.get(message.content, apikey, bid, message.author.id)
    await message.channel.send(msg)
    print("Bot [To {}] > {}".format(message.author.name, msg))


# -------- Run Bot -------- #


client.run(token)
