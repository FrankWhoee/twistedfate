import asyncio

import discord
from threading import Timer
from dotenv import load_dotenv, set_key
import os
from scraper import fetch_events, get_events
from util import create_env_template, filter_events, get_tf_quote
from datetime import datetime,timedelta
import time
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
FILTER_LIST = None if not FILTER_LIST else [x.strip() for x in FILTER_LIST.split(",")]

time.tzset()

# Contains list of events that have had notifications sent already
notification_sent = []

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await poll_and_wait(None, asyncio.get_running_loop())

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
    
    return notified, maybe_moved


def clean_notification_sent():
    for i,e in enumerate(notification_sent):
        if (datetime.now() - e["time"]) > timedelta(days=1):
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
            if events[i]["time"] < datetime.now():
                continue
            time_until_next_event = time_until(events[i]) - NOTIFY_BEFORE
            if time_until_next_event <= 0:
                print(f"Event has been notified before: {event_notified_before(events[i])}")
                if await notify(events[i]):
                    print(f"Set on-time timer for {events[i]}")
                    print(f"Waiting for {time_until(events[i])}")
                    Timer(time_until(events[i]), notify_event_on_time_sync, args=(events[i], loop)).start()
            else:
                event = events[i]
                break
        if time_until_next_event < DEFAULT_INTERVAL:
            interval = time_until_next_event
            arg = event
    print(f"Waiting for {interval} seconds.")
    Timer(interval, poll_and_wait_sync, (arg,loop)).start()

async def notify_event_on_time(event):
    embed = discord.Embed(title=event["title"], url=event["link"],
                          description=f"Happening now.",
                          color=0x00ff00)
    embed.set_footer(text=get_tf_quote())
    channel = await client.fetch_channel(NOTIFICATION_CHANNEL)
    await channel.send(embed=embed)
    
def notify_event_on_time_sync(event, loop):
    asyncio.run_coroutine_threadsafe(notify_event_on_time(event), loop)
def time_until(event):
    return (event["time"] - datetime.now()).total_seconds()

async def notify(event):
    notified, maybe_moved = event_notified_before(event)
    if notified:
        return False
    embed = discord.Embed(title=event["title"], url=event["link"], description=f"Happening in {naturaltime(event['time'])}.", color=0xff9100)
    embed.set_footer(text=get_tf_quote())
    if maybe_moved:
        embed.add_field(name="Event may have been moved", value=str(event["time"]), inline=False)  
    else:
        embed.add_field(name="Event time", value=str(event["time"]), inline=False)  
    channel = await client.fetch_channel(NOTIFICATION_CHANNEL)
    await channel.send(embed=embed)
    notification_sent.append(event)
    return True

def poll_and_wait_sync(next_event, loop):
    asyncio.run_coroutine_threadsafe(poll_and_wait(next_event, loop), loop)

def saveToEnv(key,val):
    set_key(dotenv_path=".env", key_to_set=key, value_to_set=val)

@client.event
async def on_message(message):
    global NOTIFICATION_CHANNEL
    global FILTER_LIST
    global NOTIFY_BEFORE
    if message.author == client.user:
        return

    if len(message.content) > 0:
        message_content = message.content
        message_prefix = message_content[0]
        message_content = message_content[1:]

        if message_prefix == PREFIX:
            if message_content.startswith("help"):
                embed = discord.Embed(title="Commands",
                                      description=f"Command prefix: {PREFIX}",
                                      color=0x000000)
                embed.add_field(name="games", value="Shows games with filtering.", inline=False)
                embed.add_field(name="notify", value="Sets the channel where notifications are sent.", inline=False)
                embed.add_field(name="filter", value="Show or set filters.", inline=False)
                embed.add_field(name="before", value="Show or set how much in advance notifications are sent.", inline=False)

                embed.set_footer(text=get_tf_quote())
                await message.channel.send(embed=embed)
            elif message_content.startswith("games"):
                events = filter_events(get_events(), FILTER_LIST)
                embed = discord.Embed(title="Upcoming Games", color=0x000000)

                for e in events[:10]:
                    embed.add_field(name=e["title"], value=e["time"], inline=False)    

                embed.set_footer(text=get_tf_quote())
                await message.channel.send(embed=embed)
            elif message_content.startswith("notify"):
                saveToEnv("NOTIFICATION_CHANNEL", str(message.channel.id))
                NOTIFICATION_CHANNEL = message.channel.id
                embed = discord.Embed(title="Channel set to send notifications", color=0x000000)
                embed.set_footer(text=get_tf_quote())
                await message.channel.send(embed=embed)
            elif message_content.startswith("filter"):
                args = message_content[6:].strip()
                if len(args) <= 0:
                    if FILTER_LIST:
                        await message.channel.send(f"Filtering for {','.join(FILTER_LIST)}. Type `!filter clear` to remove all filters.")
                    else:
                        await message.channel.send("No filtering")
                else:
                    args = args.split(",")
                    if len(args) == 1 and args[0] == "clear":
                        saveToEnv("FILTER_LIST", "")
                        FILTER_LIST = []
                    else:
                        args = [x.strip() for x in args]
                        saveToEnv("FILTER_LIST", ",".join(args))
                        FILTER_LIST = args
                    embed = discord.Embed(title="Filtering updated", description="Now filtering for " + ",".join(FILTER_LIST), color=0x000000)
                    embed.set_footer(text=get_tf_quote())
                    await message.channel.send(embed=embed)
            elif message_content.startswith("before"):
                args = message_content[6:].strip()
                if args:
                    saveToEnv("NOTIFY_BEFORE", args)
                    NOTIFY_BEFORE = int(args)
                    embed = discord.Embed(title="Timing set.", description=f"Notifications will now come in {NOTIFY_BEFORE} seconds in advance.", color=0x000000)
                    embed.set_footer(text=get_tf_quote())
                    await message.channel.send(embed=embed)
                else:
                    embed = discord.Embed(title="Advance timing",
                                          description=f"Sets how far in advance bot will notify you of a game. For example `!before 300` makes the bot notify you 300 seconds or 5 minutes before a game happens.",
                                          color=0x000000)
                    embed.add_field(name="Current Timing", value=str(NOTIFY_BEFORE))
                    embed.set_footer(text=get_tf_quote())
                    await message.channel.send(embed=embed)
            elif message_content.startswith("debug"):
                print(notification_sent)
                
            

if ENVIRONMENT == "prod":
    client.run(PROD_KEY)
elif ENVIRONMENT == "dev":
    client.run(DEV_KEY)
else:
    print("Invalid environment")