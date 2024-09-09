from random import randint


def create_env_template():
  """Creates a template .env file with placeholder comments."""
  template_content = """
# This is a template .env file. Please replace the placeholders with your actual values.

# Production API key
PROD_KEY=""

# Development API key
DEV_KEY=""

# Current environment (prod or dev)
ENVIRONMENT=""

# Prefix for commands
PREFIX="!"

# Waiting time between polls
DEFAULT_INTERVAL="300"

# How much time in advance you want to be notified in seconds
NOTIFY_BEFORE="300"

# Notification channel ID (where notifications will be sent)
NOTIFICATION_CHANNEL=""

# Filter list. Only alerts when these teams play. Use empty for all teams. Seperate by commas.
# ex. FILTER_LIST = "HOGGY,TAAPZ,LANES"
FILTER_LIST=""

# Manually override timezone
TZ="America/Vancouver"
"""

  with open(".env", "w") as f:
    f.write(template_content)


def get_tf_quote():


    data = """
"I reckon."
"Charmed, I'm sure."
"Doin' it."
"I'm one of a kind."
"It's my lucky day."
"Deal 'em."
"Just the luck of the draw."
"Don't mind if I do."
"It's all in the cards."
"Always on the run."
"Lookin' good."
"Only a fool plays the hand he's dealt."
"Nothin' better than a fool playin' tough."
"Only two Jokers in the deck, and I get dealt you."
"Cheater's just a fancy word for winner."
"Never lost a fair game... or played one."
"Giddy up! Hmhmhm... haha! Haa.. haha!"
"Ándale, hehehehehe... ma-haha! Whoop! Haha!"
"I never bluff."
"Let's raise the stakes."
"All or nothin'."
"Let it ride."
"Looks like trouble."
"Nobody touches the hat."
"Pick a card."
"I got this."
"Clear as day."
"Feelin' blue."
"Eyes open."
"Thorned rose."
"Blood red."
"Seein' red."
"Lucky them."
"Hold it, partner."
"Shinin' gold."
"It ain't luck, it's destiny."
"No fightin' destiny."
"I'm already gone."
"I'm gone."
"Gotta hit the trail."
"Dead in his tracks."
"Tough luck, Malcolm."
"Simmer down, hotshot."
"""
    data = data.split("\n")
    return data[randint(0,len(data) - 1)]

def filter_events(events, filter):
    if not filter:
      return events
    
    output = []

    for f in filter:
       output.extend([x for x in events if f in x["title"]])

    return output