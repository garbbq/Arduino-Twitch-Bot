import random
import asyncio
import twitchio
import threading
import signal
import sqlite3
import serial
from queueClass import Queue
from functions import *
from authentication import TMI_TOKEN, NAME, BOT_PREFIX, CHANNEL, user_channel_id
from twitchio.ext import commands
from twitchio.ext import pubsub

client = twitchio.Client(token=TMI_TOKEN)
client.pubsub = pubsub.PubSubPool(client)
# change these based on machine
GLIZZ_TIME = 2.2  # :^)
RETRACT_TIME = 0.2  # time it takes for compressed air piston to return # time it takes for queue to run again
COOLDOWN = 0.11 + GLIZZ_TIME - 2.2
MACHINE = 'glizzy'  # glizzy, cream, shock, other
on = True  # threads are set to die if false
testing = False
q = Queue()


# Arduino functions
def write_read(x, machine):
    machine.write(bytes(x, 'utf-8'))
    time.sleep(0.05)


def run_machine():
    write_read('3', arduino)
    # time.sleep(COOLDOWN)
    time.sleep(GLIZZ_TIME)
    write_read('4', arduino)


# starting arduino
PORT = "COM3"
print(f'Opening port {PORT}...')
try:
    arduino = serial.Serial(port=PORT, baudrate=115200, timeout=.1)
    print (f'Success, {PORT} open')
except:
    print(f'Failed to open port {PORT}, exiting program...')
    if not testing:
        quit()

# connect to database for tracking usage
conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()

# Closes all threads properly
def handler(signum, frame):
    global on
    on = False
    conn.close()
    log("conn closed")
    time.sleep(2)
    exit(1)


signal.signal(signal.SIGINT, handler)  # close threads


# sql functions
def check_if_user_exists(user):
    cursor.execute('''SELECT username FROM users WHERE username=?''', (user,))
    exists = cursor.fetchall()
    if not exists:
        conn.commit()
        log(f'{user} has not activated before!')
        return False
    log(f'{user} has activated before')
    conn.commit()
    return True


machine_number = {'glizzy':0, 'cream':0, 'shock':0, 'other':0}


def increase_machine_use_count(user, machine):
    cursor.execute(f'''UPDATE users SET {machine} = {machine} + 1 WHERE username = '{user}' ''')
    log(f'modified entry for {user}.')
    conn.commit()


def new_user(user, machine):
    #machine_number = {'glizzy':0, 'cream':0, 'shock':0, 'other':0}
    machine_number[machine] = 1
    cursor.execute(f'''INSERT INTO users VALUES('{user}', {machine_number['glizzy']}, {machine_number['cream']}, {machine_number['shock']}, {machine_number['other']})''')
    machine_number[machine] = 0
    conn.commit()
    log(f'created entry for {user}.')

# cursor.execute("""CREATE TABLE users (
#             username text,
#             glizzy integer,
#             cream integer,
#             shock integer,
#             other integer
#     )""")
#
# conn.commit()

#   users
#       username text
#       glizzy integer
#       cream integer
#       shock integer
#       other integer

# !glizzy, @user glizzied x times!
# !cream, @user creamed x times!
# !other, @user used "other" x times!
# !all, @user activated x times!
class Bot(commands.Bot):  # Chat bot

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token=TMI_TOKEN, prefix='!', initial_channels=['#bunzo1'])
        log('bot is running... wassup')

    # Function for displaying machine counts
    async def display_machine_count(self, user, machine):
        if check_if_user_exists(user):
            cursor.execute(f"SELECT {machine} FROM users WHERE username='{user.lower()}'")  # i realise now there was no point in making it lowercase
            data = cursor.fetchall()
            await bot.connected_channels[0].send(f'@{user} has {machine}ed Bunzo {data[0][0]} times!')
        else:
            await bot.connected_channels[0].send(f'@{user} has {machine}ed Bunzo 0 times!')
    # Bot Commands
    @commands.command()
    async def help(self, ctx: commands.Context): # ~help~ displays what commands are available
        await ctx.send(f"How many times you've used a machine = !glizzy, !cream, !other, !all.")
    # Users ask the bot for machine counts then calls display_machine_count()
    @commands.command()
    async def glizzy(self, ctx: commands.Context):
        await self.display_machine_count(ctx.author.name, 'glizzy')

    @commands.command()
    async def cream(self, ctx: commands.Context):
        await self.display_machine_count(ctx.author.name, 'cream')

    @commands.command()
    async def shock(self, ctx: commands.Context):
        await self.display_machine_count(ctx.author.name, 'shock')

    @commands.command()
    async def other(self, ctx: commands.Context):
        await self.display_machine_count(ctx.author.name, 'other')

    @commands.command()
    async def all(self, ctx: commands.Context):
        if check_if_user_exists(ctx.author.name.lower()):
            cursor.execute(f"SELECT (glizzy + cream + shock + other) FROM users WHERE username='{ctx.author.name.lower()}'")
            data = cursor.fetchall()
            await ctx.send(f'@{ctx.author.name} has activated the machines altogether {data[0][0]} times!')
        else:
            await ctx.send(f'@{ctx.author.name} has activated the machines altogether 0 times!')

    # @commands.command() # started on a leaderboard command
    # async def leaderboard(self, ctx: commands.Context):
    #     cursor.execute(f"select * from users limit 5")
    #     data = cursor.fetchall()
    #     for i in data():
    #         await ctx.send(f'@{ctx.author.name} has activated the machines altogether 0 times!')


# Channel points redeemed
@client.event()
async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
    person = event.user.name.lower()
    log(f'{event.user.name} redeemed channel points.')
    q.add_to_queue(event.user.name)
    if check_if_user_exists(person):
        increase_machine_use_count(person, MACHINE)
    else:
        new_user(person, MACHINE)

# starts everything
async def main():
    topics = [
        pubsub.channel_points(TMI_TOKEN)[user_channel_id]
    ]
    await client.pubsub.subscribe_topics(topics)
    p1 = threading.Thread(target=queue_loop)  #start queue checking thread
    p1.start()
    # await client.start() ~ breaks the code, don`t listen to the documentation


def queue_loop():
    log("Queue loop has begun!")
    while on:
        log('checking queue')
        if q.display_queue_length() != 0:
            run_machine()
            q.remove_from_queue()
        time.sleep(COOLDOWN)
    log("Queue disabled.")
    log("Closing connection to arduino...")
    arduino.close()
    log("Closing queue loop thread...")
    time.sleep(0.05)
    quit()


bot = Bot()
client.loop.create_task(main())
client.loop.create_task(bot.run())
client.loop.run_forever()
