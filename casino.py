# blackjackbot.py

# Import statements
# must install discord, dotenv, json if not there
import os
import discord
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
from random import shuffle
import random
from random import choice
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
"""
    Threading not implemented, currently not locking access to the 'sessions' dictionary.
    Default Python serialization is in effect.
"""

# ------------------------------------------------------------------#
# Load all environment variables from the .env file, which can be
#      created with setup.py
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATA_PATH = os.getenv('DATA_PATH') + "/database.txt"
CREATOR = os.getenv('CREATOR')

# ------------------------------------------------------------------#
# Global variable / Database setup
client = discord.Client(intents=discord.Intents.all())
data = {}

# Assumes there is a file in DATA_PATH called 'database.txt'
with open(DATA_PATH, 'r') as file:
    data = json.load(file)
print(data)

cards = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}
sessions = {}
deck = []
cf_but = [create_button(style=ButtonStyle.green, label="Ngửa"),]
action_row = create_actionrow(*cf_but)
# ------------------------------------------------------------------#
@client.event
async def on_ready():
    guild = discord.utils.find(lambda g: g.name == GUILD, client.guilds)




# ------------------------------------------------------------------#
# *****This function can be streamlined more... TODO For future build
def genEmbed(type, title, desc, msg="", color=discord.Color.blurple(), player=None):
    global sessions
    embed = discord.Embed(
        title=title,
        description=desc,
        color=color
    )
    if type == "create":
        embed.add_field(name='\U0001F4B0 Balance \U0001F4B0', value="2000", inline=False)
        embed.set_footer(text='thắc mắc gì thì bấm !help hoặc !assist nha')
    elif type == 'play' or type == "win" or type == "lose":
        field_name = {'play': 'Số tiền cược', 'win': 'Bạn thắng', 'lose': 'Bạn thua'}
        footer = {'play': '!hit để rút, !stand để dằn', 'win': 'C-cũng ghê', 'lose': 'Chúc bạn may mắn lần sau'}
        embed.add_field(name=field_name[type], value=f":coin: {sessions[player]['bet']} :coin:", inline=False)
        embed.add_field(name='Balance', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.add_field(name='Người chơi', value=f"{' - '.join([i for i in sessions[player]['Người_chơi']])}",
                        inline=True)
        embed.add_field(name=' :black_large_square:', value=' :black_large_square:', inline=True)
        Nhà_cái = f"{sessions[player]['Nhà_cái'][0]} - \U0001F0CF" if type == 'play' else f"{' - '.join([i for i in sessions[player]['Nhà_cái']])}"
        embed.add_field(name='Nhà cái', value=Nhà_cái, inline=True)
        embed.set_footer(text=footer[type])
    elif type == "tie":
        embed.add_field(name='Số dư hiện tại', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.add_field(name='Người chơi', value=f"{' - '.join([i for i in sessions[player]['Người_chơi']])}",
                        inline=True)
        embed.add_field(name=' :black_large_square:', value=' :black_large_square:', inline=True)
        embed.add_field(name='Nhà cái', value=f"{' - '.join([i for i in sessions[player]['Nhà_cái']])}",
                        inline=True)
        embed.set_footer(text='Làm ván nữa đê.')
    elif type == "stats":
        embed.add_field(name='Số dư', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.add_field(name='Game thắng', value=f"{data[player]['wins']}", inline=True)
        embed.add_field(name='Game thua', value=f"{data[player]['losses']}", inline=True)
        embed.add_field(name='Game hòa', value=f"{data[player]['ties']}", inline=True)
        embed.add_field(name='Rank', value=f"Not yet implemented", inline=False)
        embed.set_footer(text='Còn gì thắc mắc khum??')
    elif type == "leaderboard":
        leaderboard = sorted([(k, v['balance'], v['wins']) for k, v in data.items()], key=(lambda x: (x[1], x[2])),
                             reverse=True)
        if len(leaderboard) > 4:
            leaderboard = leaderboard[0:4]
        for i, v in enumerate(leaderboard):
            emoji = {0: ':first_place:', 1: ':second_place:', 2: ':third_place:'}
            i = emoji[i] if i in emoji else f"#{i + 1}"
            embed.add_field(name=f"{i} :  {v[0][:-5]}", value=f"{v[1]}", inline=False)
        embed.set_footer(text='Còn gì thắc mắc thì !help hoặc !assist nha')
    elif type == 'job':
        embed.add_field(name='Số dư hiện tại', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.set_footer(text='Chúc zui')
    return embed


# ------------------------------------------------------------------#
# Generates a standard blackjack deck. Consists of 6 packs of 52 ct cards, shuffled.
def genDeck():
    deck = []
    # Generate a deck of 6 packs
    for _ in range(6):
        pack = []
        # Generate each pack
        for i in range(4):
            pack += cards.keys()
            shuffle(pack)
        deck += pack
        shuffle(deck)
    return deck


# ------------------------------------------------------------------#\
# Calculates the value of a hand according to Blackjack rules
def sumHand(hand):
    hand_sum = 0
    aces = 0
    for i in hand:
        if i != 'A':
            hand_sum += cards[i]
        else:
            aces += 1
    # Handle aces
    for i in range(aces):
        if hand_sum + 11 <= 21:
            hand_sum += 11
        else:
            hand_sum += 1
    return hand_sum


# ------------------------------------------------------------------#
@client.event
async def on_message(message):
    # ------------------------------------------------------------------#
    global sessions
    global deck
    channel = message.channel
    player = message.author

    # ------------------------------------------------------------------#
    # Check if message was sent in the "blackjack" channel, or if the sender
    #    is the bot
    if "blackjack" not in channel.name or player == client.user:
        return
    # ------------------------------------------------------------------#
    # Player name and message parsing setup
    name = f'{player}'
    msg = message.content if message.content.startswith('!gift') or message.content.startswith(
        '!give') else message.content.lower()

    # ------------------------------------------------------------------#
    if msg == '!help':
        embed = discord.Embed(title='Các câu lệnh cần biết', color=discord.Color.gold())
        embed.add_field(name='!play | !bet', value='Để chơi thì bấm !play <tiền cược>', inline=False)
        embed.add_field(name='!hit | !stand', value='!hit - rút thêm lá nữa\n!stand - dằn bài',
                        inline=False)

        # Separate !bal and !stats eventually
        embed.add_field(name='!bal | !stats | !balance',
                        value='Xem lượng tài sản còn lại, số game thắng/thua/hòa', inline=False)

        embed.add_field(name='!top | !leaderboard', value='Hiện top 4 phú ông/bà hiện tại', inline=False)
        embed.add_field(name='!job | !collect',
                        value='Tặng 200 coin, mỗi giờ chỉ được xài 1 lần', inline=False)
        await channel.send(f"{player.mention}", embed=embed)
        return
    # ------------------------------------------------------------------#
    elif msg.startswith('!') and name not in data and msg != '!create':
        await channel.send('Chưa có tiền mà chơi cái gì, bấm !create để tạo tài khoản đi')

    # ------------------------------------------------------------------#
    elif msg == '!hit':
        if name in sessions:
            sessions[name]['Người_chơi'].append(deck.pop())
            Nhà_cái = sumHand(sessions[name]['Nhà_cái'])
            Người_chơi = sumHand(sessions[name]['Người_chơi'])
            if Người_chơi > 21:
                data[name]['balance'] -= sessions[name]['bet']
                data[name]['losses'] += 1
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}",
                                   embed=genEmbed("lose", 'QUẮC', 'RÚT CHO LẮM RỒI QUẮC :V', color=discord.Color.red(),
                                                  player=name))
                del sessions[name]

            elif Người_chơi == 21:
                while sumHand(sessions[name]['Nhà_cái']) < 17:
                    sessions[name]['Nhà_cái'].append(deck.pop())
                if sumHand(sessions[name]['Nhà_cái']) == 21:
                    data[name]['ties'] += 1
                    await channel.send(f"{player.mention}",
                                       embed=genEmbed("tie", 'HÒA!', 'Tưởng một mình chú có 21 à :)).', player=name))
                else:
                    data[name]['wins'] += 1
                    data[name]['balance'] += sessions[name]['bet']
                    json.dump(data, open(DATA_PATH, 'w'))
                    await channel.send(f"{player.mention}", embed=genEmbed("win", ':tada: THẮNG RỒI :tada:', 'VCL 21, CHƠI MÌNH ĐI MÁ',
                                                                           color=discord.Color.green(), player=name))
                del sessions[name]

            else:
                await channel.send(f"{player.mention}",
                                   embed=genEmbed("play", 'Blackjack', 'Round Continued!', color=discord.Color.blue(),
                                                  player=name))
        else:
            await channel.send(f"{player.mention} Rồi bấm !play chưa mà đòi rút bài???")

    # ------------------------------------------------------------------#
    elif msg == '!stand':
        if name in sessions:
            Người_chơi = sumHand(sessions[name]['Người_chơi'])
            while sumHand(sessions[name]['Nhà_cái']) < 17:
                sessions[name]['Nhà_cái'].append(deck.pop())
            Nhà_cái = sumHand(sessions[name]['Nhà_cái'])
            if (Người_chơi > Nhà_cái and Người_chơi <= 21) or Nhà_cái > 21:
                data[name]['wins'] += 1
                data[name]['balance'] += sessions[name]['bet']
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}", embed=genEmbed("win", ':tada: THẮNG RỒI!!! :tada:', 'KÊ, BỔN NƯƠNG NHẬN THUA',
                                                                       color=discord.Color.green(), player=name))
            elif Người_chơi < Nhà_cái and Nhà_cái <= 21:
                data[name]['losses'] += 1
                data[name]['balance'] -= sessions[name]['bet']
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}",
                                   embed=genEmbed("lose", 'THUAAA', 'NHÁT VẬY? RÚT CHO NGŨ LINH LUÔN CHỨ :))', color=discord.Color.red(),
                                                  player=name))
            else:
                data[name]['ties'] += 1
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}",
                                   embed=genEmbed("tie", 'HÒA', 'KÊ, GAME NÀY HÒA VẬY.', player=name))
            del sessions[name]
        else:
            await channel.send(f"{player.mention} not currently in a game!")

    elif msg in ('!bal', '!balance', '!stats'):
        await channel.send(f"{player.mention}", embed=genEmbed("stats", 'THÔNG TIN SỐ DƯ', 'CHECK SỐ DƯ ĐÊ.', player=name))

    # ------------------------------------------------------------------#
    elif msg.startswith('!bet') or msg.startswith('!play'):
        # Verify session does not already exist
        if name not in sessions:
            # Verify proper command format: !bet <integer amount>
            if len(msg.split(' ')) == 2 and msg.split(' ')[1].isdigit():
                bet = int(msg.split(' ')[1])
                # Verify bet amount is legal: bet <= player balance and > 0
                if bet <= data[name]['balance'] and bet > 0:
                    sessions[name] = {"bet": bet, "Người_chơi": [], "Nhà_cái": []}
                    if len(deck) < 75:
                        deck = genDeck()
                        print("Từ từ cho xào bài cái.")
                    for _ in range(2):
                        sessions[name]['Người_chơi'].append(deck.pop())
                        sessions[name]['Nhà_cái'].append(deck.pop())
                    Nhà_cái = sumHand(sessions[name]['Nhà_cái'])
                    Người_chơi = sumHand(sessions[name]['Người_chơi'])

                    if Người_chơi == 21 and Nhà_cái != 21:
                        # Payout player bet * 1.5 and add to balance. Increment Player win, Increment dealer loss.
                        data[name]['balance'] += int(sessions[name]['bet'] * 1.5)
                        sessions[name]['bet'] = int(sessions[name]['bet'] * 1.5)
                        data[name]['wins'] += 1
                        json.dump(data, open(DATA_PATH, 'w'))
                        await channel.send(f"{player.mention}",
                                           embed=genEmbed("win", ':tada: :tada: THẮNG!!! :tada: :tada:',
                                                          'QUẢI ĐẠN XÌ DÁCH???', color=discord.Color.green(),
                                                          player=name))
                        del sessions[name]

                    # Return player bet and do not change balance. Increment Player tie, Increment Dealer tie.
                    elif Nhà_cái == 21 and Nhà_cái == Người_chơi:
                        data[name]['ties'] += 1
                        json.dump(data, open(DATA_PATH, 'w'))
                        await channel.send(f"{player.mention}",
                                           embed=genEmbed("tie", 'HÒA!', 'HAI XÌ DÁCH, HOY CHƠI LẠI.',
                                                          player=name))
                        del sessions[name]

                    else:
                        await channel.send(f"{player.mention}", embed=genEmbed("play", 'Blackjack', 'Round Started!',
                                                                               color=discord.Color.blue(), player=name))
                else:
                    await channel.send(f"{player.mention}",
                                       embed=genEmbed("error", 'Error!', f"Có đủ {bet} đâu mà cược má???",
                                                      color=discord.Color.orange()))
            else:
                await channel.send(f"{player.mention}",
                                   embed=genEmbed("error", 'Error!', 'bấm\n!bet <số tiền>  OR !play <số tiền> mới đúng',
                                                  color=discord.Color.orange()))
        else:
            await channel.send(f"{player.mention}",
                               embed=genEmbed("error", 'Error!', 'Đang chơi mà trốn chơi ván khác à??!', color=discord.Color.orange()))

    # ------------------------------------------------------------------#
    elif msg.startswith('!job') or msg.startswith('!collect'):
        lastjob = datetime.strptime(data[name]['lastjob'], "%Y-%m-%d %H:%M:%S")
        if lastjob <= datetime.utcnow() - timedelta(hours=1):
            # modify user
            data[name]['lastjob'] = f'{datetime.utcnow()}'.split('.')[0]
            data[name]['balance'] += 200
            json.dump(data, open(DATA_PATH, 'w'))
            await channel.send(f"{player.mention}", embed=genEmbed("job", 'Tiền chà bồn cầu nè', 'Bố thí 200 cho chơi game đó',
                                                                   color=discord.Color.green(), player=name))
        else:
            # error
            time_to_next_job = str(
                (lastjob + timedelta(hours=1)) - datetime.strptime(f'{datetime.utcnow()}'.split('.')[0],
                                                                   "%Y-%m-%d %H:%M:%S")).split(':')
            await channel.send(f"{player.mention}", embed=genEmbed("error", 'Error!',
                                                                   f'Đã kêu là mỗi giờ chỉ nhận một lần mà?\nđợi khoảng \n{time_to_next_job[-2]} min {time_to_next_job[-1]} sec nữa đi',
                                                                   color=discord.Color.orange()))

    # ------------------------------------------------------------------#
    elif msg == '!leaderboard' or msg == '!top':
        if len(data.keys()) == 0:
            await channel.send(f"{player.mention}\nKhông một ai có tiền :)).")
        line = '----------------------------------'
        await channel.send(f"{player.mention}", embed=genEmbed("leaderboard",
                                                               ":chart_with_upwards_trend: :medal: Leaderboard :medal: :chart_with_upwards_trend:",
                                                               f'{line}', color=discord.Color.purple()))

    # ------------------------------------------------------------------#
    elif msg.startswith('!give') or msg.startswith('!gift'):
        """ 
        Gift/Give command. Usage: !give <tag tên người muốn tặng> <bao nhiêu tiền> or !gift <tag tên người muốn tặng> <bao nhiêu tiền>
        """
        if name in sessions.keys():
            await channel.send(f"{player.mention}",
                               embed=genEmbed('error', 'Error!', "Chơi game xong đã rồi tặng gì tặng ku",
                                              color=discord.Color.orange()))
            return
        split_msg = msg.split(' ')
        amount = int(split_msg[2]) if len(split_msg) == 3 and split_msg[2].isdigit() else 0
        if len(split_msg) == 3 and split_msg[1] in data.keys() and (amount > 0 and data[name]['balance'] - amount >= 0):
            data[name]['balance'] -= amount
            data[split_msg[1]]['balance'] += amount
            embed = discord.Embed(title=':confetti_ball::gift: Gift! :gift::confetti_ball:',
                                  description=f"{name[:-5]} gave {split_msg[1][:-5]} {amount} tokens!",
                                  color=discord.Color.dark_grey())
            await channel.send(f"{player.mention} gifts {split_msg[1][:-5]}", embed=embed)
        else:
            await channel.send(f"{player.mention}",
                               embed=genEmbed('error', 'Error!', 'typo kìa, !gift <user#tag> <valid amount> mới đúng',
                                              color=discord.Color.orange()))

    elif msg == '!create':
        if name in data:
            await channel.send(f"{player.mention}", embed=genEmbed("error", 'Error!', 'Account already created!',
                                                                   color=discord.Color.orange()))
        else:
            data[name] = {'balance': 2000, 'lastjob': f'{datetime.utcnow()}'.split('.')[0], 'wins': 0, 'losses': 0,
                          'ties': 0}
            json.dump(data, open(DATA_PATH, 'w'))
            await channel.send(f"{player.mention}",
                               embed=genEmbed("create", '\U00002660 Blackjack \U00002660', 'Account creation success!'))

    elif msg.startswith('!rigged'):
        await channel.send('Sue me.')

    elif msg == '!cf':
        determine_flip = [1,0]
        cf_embed = discord.Embed(title="Sấp ngứa, chọn mặt nào??",color=discord.Color.orange())
        await channel.send(f"{player.mention}",embed=cf_embed, components=[action_row])

    # ==== DEBUGGING / CREATOR CONTROLS ==== #
    elif (msg == '!cheats' or msg == '!hacks') and name == CREATOR:
        if len(msg.split(' ')) == 2 and msg.split(' ')[1].isdigit():
            bet = int(msg.split(' ')[1])
            if bet <= 100000:
                data[name]['balance'] += bet
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}",
                                   embed=genEmbed("job", 'Here you go creator!', f'You received {bet} tokens',
                                                  color=discord.Color.green(), player=name))

    elif msg == '!quit' and name == CREATOR:
        del sessions[name]

    elif msg == '!next' and name == CREATOR:
        await channel.send(f"{player.mention} The next 2 cards are {deck[-1]} and {deck[-2]}")

    elif msg.startswith('!disconnect') and name == CREATOR:
        sessions.clear()
        json.dump(data, open(DATA_PATH, 'w'))
        await client.close()

    elif msg.startswith('!deleteacc') and name == CREATOR:
        await channel.send('f"{player.mention}, your account has been deleted."')
        data.pop(name)
    return




client.run(TOKEN)