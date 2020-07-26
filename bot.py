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
from discord import ChannelType
import random


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
loading_music = False


# client = discord.Client()
bot = commands.Bot(command_prefix='!')

@bot.command()
async def daybreakhelp(ctx):
  print("Hello World")


  descrip = "A Discord bot that plays music based on the server's mood." #Write a description of the bot here

  embedVar = discord.Embed(title="Daybreak", description=descrip, color=0x03f8fc)

  print("test")
  
  embedVar.add_field(name="!daybreakhelp", value="'!daybreakhelp' shows help menu", inline=False) # Copy and paste this but change "Title" to the name of a command and "Descripton" to what it does

  embedVar.add_field(name="!start", value="'!start' connects bot to voice channel", inline=False) 
  embedVar.add_field(name="!mood", value=" '!mood' returns the mood of the sever. MAKE SURE YOU JOIN THE VOICE CHANNEL 'music' TO LISTEN MUSIC.", inline=False) 


  await ctx.message.channel.send(embed=embedVar)

@bot.command()
async def yt(ctx, url):

    embedVar = discord.Embed(title="Music Sentiment Bot", description="Retrieving song...", color=0x03f8fc)
    # embedVar.add_field(name="SongName", value=url, inline=False)
    await ctx.message.channel.send(embed=embedVar)

    # print("Hello")

    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("Wait for the current playing music end or use the 'stop' command")
        return

    vc = get(bot.voice_clients, guild=ctx.guild)
    ydl_opts = {'format': 'bestaudio'}
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            embedVar = discord.Embed(title="Music Sentiment Bot", color=0x03f8fc)
            embedVar.add_field(name="Playing Song:", value=str(file), inline=False)
            await ctx.message.channel.send(embed=embedVar)
            os.rename(file, 'song.mp3')
    vc.play(discord.FFmpegPCMAudio("song.mp3"))

@bot.command()
async def start(ctx):

    found = False
    for c in ctx.message.guild.channels:
        if c.type == ChannelType.voice and c.name == "music":
            found = True
            vc = await c.connect()
            embedVar = discord.Embed(title="Music Sentiment Bot", description="Connected to channel 'music'", color=0x03f8fc)
            await ctx.message.channel.send(embed=embedVar)
    if not found:
        category = await ctx.message.guild.create_category('Music Bot')
        c = await ctx.message.guild.create_voice_channel('music', category=category)
        vc = await c.connect()
        embedVar = discord.Embed(title="Music Sentiment Bot", description="Created channel 'music'", color=0x03f8fc)
        await ctx.message.channel.send(embed=embedVar)
            


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
        send = "The primary mood of the server is: " + primary_mood
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

    if len(messagelog) > 50:
        messagelog.pop(0)

    if str(message.author) != "hobbyhacks-music-bot#2347" and message.content[0] != '!':
        messagelog.append(message.content)
    
        messagelog = "\n".join(messagelog)

        f = open("messagelog.txt", "w")
        f.write(messagelog)
        f.close()

        for c in message.guild.channels:
            ctx = await bot.get_context(message)
            if c.type == ChannelType.voice and c.name == "music":
                vc = get(bot.voice_clients, guild=ctx.guild)
                if not vc.is_playing():
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
                            send = "The primary mood of the server is: " + primary_mood
                            if primary_mood == "tentative" or primary_mood == "neutral":
                                musicFile = "calm.txt"
                            elif primary_mood == "anger" or primary_mood == "confident":
                                musicFile = "intense.txt"
                            elif primary_mood == "joy" or primary_mood == "analytical" :
                                musicFile = "energetic.txt"
                            elif primary_mood == "sad":
                              musicFile = "sad.txt"
                            elif primary_mood == "fear":
                                musicFile = "soothing.txt"
                            print(musicFile)
                            f = open(musicFile, 'r')
                            musicList = f.read()
                            f.close()
                            musicList = musicList.split("\n")
                            url = musicList[random.randint(0, len(musicList)-1)]
                            await yt(ctx, url)
                            embedVar = discord.Embed(title="Music Sentiment Bot", description=send, color=0x03f8fc)
                            await ctx.message.channel.send(embed=embedVar)
                                # await message.channel.send(send)
                        except ApiException as ex:
                            print("Method failed with status code " + str(ex.code) + ": " + ex.message)

    await bot.process_commands(message)

# client.run(TOKEN)
bot.run(TOKEN)
