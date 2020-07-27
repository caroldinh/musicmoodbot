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

logChannel = None


# client = discord.Client()
bot = commands.Bot(command_prefix='!')

@bot.command()
async def daybreakhelp(ctx):
  print("Hello World")


  descrip = "A Discord bot that plays music based on the server's mood." #Write a description of the bot here

  embedVar = discord.Embed(title="Daybreak", description=descrip, color=0x03f8fc)

  print("test")
  
  embedVar.add_field(name="!daybreakhelp", value=" - Shows help menu", inline=False) # Copy and paste this but change "Title" to the name of a command and "Descripton" to what it does

  embedVar.add_field(name="!start", value=" - Connects to voice channel", inline=False) 
  embedVar.add_field(name="!mood", value=" - Returns primary mood of the server", inline=False) 
  embedVar.add_field(name="!skip", value=" - Skips the currently-playing song", inline=False) 
  embedVar.add_field(name="Listen to music", value="Make sure you join the voice channel 'music' to listen! If no music is playing, just say something in any channel and music will automatically start playing.", inline=False) 


  await ctx.message.channel.send(embed=embedVar)

# @bot.command()
async def yt(ctx, url):

    for c in ctx.message.guild.channels:
        if c.type == ChannelType.text and c.name == "daybreak-logs":
            logChannel = c

    embedVar = discord.Embed(title="Daybreak", description="Retrieving song...", color=0x03f8fc)
    # embedVar.add_field(name="SongName", value=url, inline=False)
    await logChannel.send(embed=embedVar)

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
            embedVar = discord.Embed(title="Daybreak", color=0x03f8fc)
            embedVar.add_field(name="Playing Song:", value=str(file), inline=False)
            await logChannel.send(embed=embedVar)
            os.rename(file, 'song.mp3')
    vc.play(discord.FFmpegPCMAudio("song.mp3"))

@bot.command()
async def skip(ctx):
    
    message = ctx.message
    messagelog = logMessage(ctx.message)
    embedVar = discord.Embed(title="Daybreak", description="Skipping song...", color=0x03f8fc)
    await message.channel.send(embed=embedVar)
    await grabSong(message, messagelog, True)

@bot.command()
async def start(ctx):

    id = str(ctx.message.guild.id)
    message_file_exists = os.path.isfile(id + "_messagelog.txt")

    if(not message_file_exists):
        f = open(id + "_messagelog.txt", "x")
        f.close()

    found = False
    for c in ctx.message.guild.channels:
        if c.type == ChannelType.voice and c.name == "daybreak-stream":
            found = True
            vc = await c.connect()
            embedVar = discord.Embed(title="Daybreak", description="Connected to channel 'daybreak-stream'", color=0x03f8fc)
            await ctx.message.channel.send(embed=embedVar)
        if c.type == ChannelType.text and c.name == "daybreak-logs":
            logChannel = c
    if not found:
        category = await ctx.message.guild.create_category('Daybreak')
        c = await ctx.message.guild.create_voice_channel('daybreak-stream', category=category)
        logChannel = await ctx.message.guild.create_text_channel('daybreak-logs', category=category)
        vc = await c.connect()
        embedVar = discord.Embed(title="Daybreak", description="Created channel 'daybreak-stream'", color=0x03f8fc)
        await ctx.message.channel.send(embed=embedVar)
            


@bot.command()
async def mood(ctx):
    # print("test Called")
    # await ctx.send('test')

    id = str(ctx.message.guild.id)
    message_file_exists = os.path.isfile(id + "_messagelog.txt")

    if(not message_file_exists):
        f = open(id + "_messagelog.txt", "x")
        f.close()

    f = open(id + "_messagelog.txt", "r")
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
        embedVar = discord.Embed(title="Daybreak", description=send, color=0x03f8fc)
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

    if str(message.author) != "Daybreak#2347" and message.content[0] != '!':

        messagelog = logMessage(message)
        await grabSong(message, messagelog, False)

    await bot.process_commands(message)

def logMessage(message):
    id = str(message.guild.id)
    message_file_exists = os.path.isfile(id + "_messagelog.txt")

    if(not message_file_exists):
        f = open(id + "_messagelog.txt", "x")
        f.close()

    id = str(message.guild.id)
    f = open(id + "_messagelog.txt", "r")
    messagelog = f.read()
    f.close()
    messagelog = messagelog.split("\n")
    if '' in messagelog:
        messagelog.remove('')

    if len(messagelog) > 50:
        messagelog.pop(0)

    if(message.content[0] != "!"):
        messagelog.append(message.content)

    messagelog = "\n".join(messagelog)

    f = open(id + "_messagelog.txt", "w")
    f.write(messagelog)
    f.close()

    return messagelog

async def grabSong(message, messagelog, skip):
    for c in message.guild.channels:
            ctx = await bot.get_context(message)
            if c.type == ChannelType.voice and c.name == "daybreak-stream":
                vc = get(bot.voice_clients, guild=ctx.guild)
                if (not vc.is_playing()) or skip:
                        if(skip):
                            vc.stop()
                        id = str(message.guild.id)
                        f = open(id + "_messagelog.txt", "r")
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
                            embedVar = discord.Embed(title="Daybreak", description=send, color=0x03f8fc)

                            for c in ctx.message.guild.channels:
                                if c.type == ChannelType.text and c.name == "daybreak-logs":
                                    logChannel = c
                            await logChannel.send(embed=embedVar)
                
                        except ApiException as ex:
                            print("Method failed with status code " + str(ex.code) + ": " + ex.message)

# client.run(TOKEN)
bot.run(TOKEN)
