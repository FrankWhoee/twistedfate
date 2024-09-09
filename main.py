import asyncio

import discord
from threading import Timer
from dotenv import load_dotenv, set_key
import os
import random
from scraper import fetch_events, get_events
from util import create_env_template, filter_events, get_tf_quote
from datetime import datetime,timedelta
from humanize import naturaltime


intents = discord.Intents.all()

client = discord.Client(intents=intents)

"""Checks for .env file and creates it if it doesn't exist."""
if not os.path.exists(".env"):
    print(".env file not found. Creating a template...")
    create_env_template()
else:
    print(".env file already exists.")

load_dotenv()

ENVIRONMENT = os.environ['ENVIRONMENT']
PROD_KEY = os.environ["PROD_KEY"]
DEV_KEY = os.environ["DEV_KEY"]
PREFIX = os.environ["PREFIX"]
DEFAULT_INTERVAL = int(os.environ["DEFAULT_INTERVAL"])
NOTIFY_BEFORE = int(os.environ["NOTIFY_BEFORE"])
NOTIFICATION_CHANNEL = os.environ["NOTIFICATION_CHANNEL"]
NOTIFICATION_CHANNEL = None if not NOTIFICATION_CHANNEL else NOTIFICATION_CHANNEL

FILTER_LIST = os.environ["FILTER_LIST"]
FILTER_LIST = None if not FILTER_LIST else FILTER_LIST.split(",")

# Contains list of events that have had notifications sent already
notification_sent = []

@client.event
async def on_ready():
    global channel
    print(f'We have logged in as {client.user}') 
    
    poll_and_wait_sync(None, asyncio.get_running_loop())

def event_notified_before(event):
    global notification_sent
    maybe_moved = False
    notified = False

    for e in notification_sent:
        if event["title"] == e["title"]:
            if event["time"] == e["time"]:
                notified = True
                return (notified, maybe_moved)
            elif abs(event["time"] - e["time"]) < timedelta(hours=1):
                maybe_moved = True
    
    return (notified, maybe_moved)


def clean_notification_sent():
    for i,e in enumerate(notification_sent):
        if datetime.now() - e["time"] > timedelta(days=1):
            notification_sent.pop(i)

async def poll_and_wait(next_event, loop):
    if next_event:
        await notify(next_event)
    clean_notification_sent()
    events = filter_events(fetch_events(), FILTER_LIST)
    interval = DEFAULT_INTERVAL
    arg = None
    if len(events) > 0:
        event = None
        for i in range(len(events)):
            time_until_next_event = time_until(events[i]) - NOTIFY_BEFORE
            if time_until_next_event <= 0:
                await notify(events[i])
            else:
                event = events[i]
                break
        if time_until_next_event < DEFAULT_INTERVAL:
            interval = time_until_next_event
            arg = event
    Timer(interval, poll_and_wait_sync, (arg,loop)).start()

def time_until(event):
    return (event["time"] - datetime.now()).total_seconds()

async def notify(event):
    notified, maybe_moved = event_notified_before(event)
    if notified:
        return
    embed = discord.Embed(title=event["title"], description=f"Happening in {naturaltime(event['time'])}.", color=0x00ff00 if not maybe_moved else 0xff9100)
    embed.set_footer(text=get_tf_quote())
    if maybe_moved:
        embed.add_field(name="Event may have been moved", value=str(event["time"]), inline=False)  
    else:
        embed.add_field(name="Event time", value=str(event["time"]), inline=False)  
    channel = await client.fetch_channel(NOTIFICATION_CHANNEL)
    await channel.send(embed=embed)

def poll_and_wait_sync(next_event, loop):
    asyncio.run_coroutine_threadsafe(poll_and_wait(next_event, loop), loop)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if len(message.content) > 0:
        message_content = message.content
        message_prefix = message_content[0]
        message_content = message_content[1:]

        if message_prefix == PREFIX:
            if message_content.startswith("games"):
                events = get_events()
                embed = discord.Embed(title="Upcoming Games", color=0x00ff00)

                for e in events[:10]:
                    embed.add_field(name=e["title"], value=e["time"], inline=False)    

                embed.set_footer(text=get_tf_quote())
                await message.channel.send(embed=embed)
            elif message_content.startswith("notify"):
                set_key(dotenv_path=".env", key_to_set="NOTIFICATION_CHANNEL", value_to_set=str(message.channel.id))
                embed = discord.Embed(title="Channel set to send notifications", color=0x00ff00)
                embed.set_footer(text=get_tf_quote())
                await message.channel.send(embed=embed)
                
            

if ENVIRONMENT == "prod":
    client.run(PROD_KEY)
elif ENVIRONMENT == "dev":
    client.run(DEV_KEY)
else:
    print("Invalid environment")