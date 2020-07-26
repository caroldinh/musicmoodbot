# bot.py
import os
import discord
from dotenv import load_dotenv
import json
from ibm_watson import ToneAnalyzerV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import ApiException
import youtube_dl
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from discord.ext.commands import Bot
# import pynacl



authenticator = IAMAuthenticator(os.environ['IBM_KEY'])
tone_analyzer = ToneAnalyzerV3(
    version='2020-04-07', authenticator=authenticator)

tone_analyzer.set_service_url(
        os.environ['SERVICE_URL']
)

load_dotenv()
TOKEN = os.environ['DISCORD_TOKEN']
GUILD = 'hobbyhacks bot test'

allMessages = ""


# client = discord.Client()
bot = commands.Bot(command_prefix='!')

@bot.command()
async def yt(ctx, url):

    await ctx.send("Playing song...")

    print("Hello")

    author = ctx.message.author
    voice_channel = ctx.message.author.voice.channel
    vc = await voice_channel.connect()
    ydl_opts = {'format': 'bestaudio'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
    vc.play(discord.FFmpegPCMAudio(URL))


@bot.command()
async def mood(ctx):
    # print("test Called")
    # await ctx.send('test')

    f = open("messagelog.txt", "r")
    messagelog = f.read()
    f.close()

    try:
        tone_analysis = tone_analyzer.tone({'text': messagelog}, content_type='application/json').get_result()
        result = json.dumps(tone_analysis)
        tones = []
        primary_mood = "neutral"
        max_score = 0
        for tone in tone_analysis["document_tone"]["tones"]:
            if(tone["score"] > max_score):
                primary_mood = tone["tone_id"]
                max_score = tone["score"]
        send = "The primary mood of the channel is: " + primary_mood
        embedVar = discord.Embed(title="Music Sentiment Bot", description=send, color=0x03f8fc)
        await ctx.message.channel.send(embed=embedVar)
            # await message.channel.send(send)
    except ApiException as ex:
        print("Method failed with status code " + str(ex.code) + ": " + ex.message)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.event
async def on_message(message):
    print(str(message.author) + ": " + str(message.content))
    # print(str(message.channel))


    f = open("messagelog.txt", "r")
    messagelog = f.read()
    f.close()
    messagelog = messagelog.split("\n")
    if '' in messagelog:
        messagelog.remove('')

    if len(messagelog) > 200:
        messagelog.pop(0)

    messagelog.append(message.content)
    messagelog = "\n".join(messagelog)

    f = open("messagelog.txt", "w")
    f.write(messagelog)
    f.close()

    if str(message.author) != "hobbyhacks-music-bot#2347" and str(message.channel) == "tone-analyzer-test":
        print("Test")
    await bot.process_commands(message)

# client.run(TOKEN)
bot.run(TOKEN)
