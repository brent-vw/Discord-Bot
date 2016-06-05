import random
import re
import urllib
import json
import shelve
import asyncio
import discord
import atexit
import giphypop
import wolframalpha
from league import run_command

client = discord.Client()
commands = shelve.open('commands')
quotes = shelve.open('quotes')
users = shelve.open('users')
with open('.apikeys') as keys:
    data = json.load(keys)
token = data['token']
dev_token = data['dev_token']
wolfram = data['wolfram_token']
header = {'User-Agent': 'Mozilla/5.0',
          'Accept': 'text/html,application/json'}


def find_id(member):
    uid = -1
    added = False
    for key in users:
        val = users[key]
        if val == member:
            uid = key
    if uid == -1:
        uid = len(list(users.keys()))
        users[str(uid)] = member
        added = True
    return str(uid), added


@client.event
async def on_message(message):
    mess = message.content
    if mess.startswith('!lol'):
        await client.send_typing(message.channel)
        args = mess.replace('!lol ', '').replace(' ', '-', 1).split('-')
        if len(args) == 1:
            args.append('None')
        if args[0] != 'counters':
            await client.send_message(message.channel, run_command(args[0], args[1]))
        else:
            resp = run_command('counters', args[1])
            if resp.endswith('.png'):
                await client.send_file(message.channel, resp)
            else:
                await client.send_message(message.channel, resp)
    elif mess.startswith('!wolfram'):
      await client.send_typing(message.channel)
      wol = wolframalpha.Client(wolfram)
      res = wol.query('\'' + mess.replace('!wolfram ', '') + '\'')
      try:
        await client.send_message(message.channel, res.pods[1].img)
      except IndexError:
        await client.send_message(message.channel, mess.replace('!wolfram ','')+' was not found.')
    elif mess.startswith('!emoji'):
        await client.send_typing(message.channel)
        await client.send_message(message.channel, emoji())
    elif mess.startswith('!drama'):
        await client.send_typing(message.channel)
        await client.send_message(message.channel, drama())
    elif mess.startswith('!cat bomb'):
        await client.send_typing(message.channel)
        mess = mess.replace('!cat bomb ', '')
        try:
            count = int(mess)
            if count > 10:
                count = 10
        except ValueError:
            count = 1
        ans = ''
        for i in range(count):
            request = urllib.request.Request('http://random.cat/meow.php', headers=header)
            with urllib.request.urlopen(request) as f:
                response = f.read().decode('UTF-8')
            response_dict = json.JSONDecoder().decode(response)
            ans += response_dict['file'] + '\n'
        await client.send_message(message.channel, ans[:-1])
    elif mess.startswith('!deletecommand'):
        try:
            print(mess.replace('!deletecommand', '').strip())
            del commands['!' + mess.replace('!deletecommand ', '').strip()]
        except KeyError:
            await client.send_message(message.channel, 'Command could not be found.')
    elif mess.startswith('!decide'):
        await client.send_typing(message.channel)
        mess = mess.replace('!decide ', '')
        dec = mess.split('or')
        if len(dec) < 2:
            answer = 'Usage: !decide something **or** something...'
        else:
            answer = 'I\'d go with: **' + dec[random.randint(0, len(dec) - 1)] + '**'
        await client.send_message(message.channel, answer)
    elif mess.startswith('!8ball'):
        await client.send_typing(message.channel)
        await client.send_message(message.channel, ball())
    elif mess.startswith('!gif'):
        await client.send_typing(message.channel)
        mess = mess.replace('!gif ', '')
        g = giphypop.Giphy()
        results = [x for x in g.search(mess)]
        if not results:
            results.append('Gif could not be found for: ' + mess)
        result = results[random.randint(0, len(results) - 1)]
        await client.send_message(message.channel, result)
    elif mess.startswith('!ganja add'):
        await client.send_typing(message.channel)
        mess = mess.replace('!ganja add ', '')
        if mess.startswith('gif '):
            mess = mess.replace('gif ', '').replace(' \"', '---\"')
            key_val = mess.split('---')
            if len(key_val) < 2:
                await client.send_message(message.channel, 'usage: !ganja add gif \"commandname\" \"site or text\"')
            else:
                key = key_val[0].replace('!', '').replace('\"', '')
                key = '!'+key
                value = key_val[1].replace('\"', '')
                commands[key] = value
                await client.send_message(message.channel, key+' was added.')
        elif mess.startswith('quote'):
            mess = message.clean_content.replace('!ganja add quote ', '')
            mess = re.sub(r'@\S+\s', '', mess)
            if len(message.mentions) != 1:
                await client.send_message(message.channel, 'usage: !ganja add quote @person quote')
            else:
                quotee, added = find_id(message.mentions[0].mention)
                if quotee not in quotes:
                    quotes[quotee] = []
                tmp = quotes[quotee]
                tmp.append(mess)
                quotes[quotee] = tmp
                await client.send_message(message.channel, ''+users[quotee]+' \"'+mess+'\" was added.')
    elif message.content.startswith('!ganja quote'):
        await client.send_typing(message.channel)
        if len(message.mentions) != 1:
            await client.send_message(message.channel, 'usage: !ganja quote @person number (optional)')
        else:
            quotee, added = find_id(message.mentions[0].mention)
            if added:
                await client.send_message(message.channel, 'No quotes for '+users[quotee]+' :(')
            else:
                mess = message.content.replace('!quote ', '')
                mess = re.sub(r'@\S+\s', '', mess).strip().replace('<', '')
                quote_list = quotes[quotee]
                if mess == 'list':
                    quote_line = '\r\n'.join(quote_list)
                    response = '```' + quote_line + '```'
                    await client.send_message(message.channel, ''+users[quotee])
                    await client.send_message(message.channel, response)
                else:
                    try:
                        index = int(mess)
                    except ValueError:
                        index = -1
                    if index == -1 or index >= len(quote_list):
                        index = random.randint(0, len(quote_list)-1)
                    await client.send_message(message.channel, ''+users[quotee]+'\t'+str(index)+': '+quote_list[index])
    elif message.content.startswith('!ganja help'):
        await client.send_typing(message.channel)
        cmds = '```'
        cmds += '!gif search term\r\n'
        cmds += '!decide something or something...\r\n'
        cmds += '!wolfram something\r\n'
        cmds += '!8ball question \r\n'
        cmds += '!emoji \r\n'
        cmds += '!drama \r\n'
        for command in commands:
            cmds = cmds + command + ' \r\n'
        cmds += '```'
        response = ['Ganjabot feels very attacked but wants to learn, you can add images or messages with:',
                    '```!ganja add gif \"commandname\" \"site or text\"```',
                    'Ganjabot finds your quotes offensive, add quotes with:',
                    '```!ganja add quote @person what you want to quote```',
                    'View league commands with: ```!lol```',
                    'View quotes with:',
                    '```!ganja quote @person'
                    '\r\n!ganja quote @person number'
                    '\r\n!ganja quote @person list```',
                    'List of added commands:',
                    cmds
                    ]
        query = ''
        for res in response:
            query += res + '\r\n'
        await client.send_message(message.channel, query)
    elif message.content in commands:
        response = commands[message.content]
        await client.send_message(message.channel, response)


def load_file(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    return lines


ball_list = []


def ball():
    global ball_list
    if not ball_list:
        ball_list = load_file('data/8ball')
    return random.choice(ball_list)


emoji_list = []


def emoji():
    global emoji_list
    if not emoji_list:
        emoji_list = load_file('data/emoji')
    return random.choice(emoji_list)


drama_list = []


def drama():
    global drama_list
    if not drama_list:
        drama_list = load_file('data/drama')
    return random.choice(drama_list)


def close_all():
    print('Closing databases...')
    commands.close()
    quotes.close()
    users.close()
    print('All databases are closed. Goodbye.')


atexit.register(close_all)
client.run(dev_token)
