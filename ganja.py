import random
import re
import shelve

import discord

client = discord.Client()
commands = shelve.open('commands')
quotes = shelve.open('quotes')
users = shelve.open('users')


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
    if mess.startswith('!ganja add'):
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
        cmds = '```'
        for command in commands:
            cmds = cmds + command + ' \r\n'
        cmds += '```'
        response = ['Ganjabot feels very attacked but wants to learn, you can add images or messages with:',
                    '```!ganja add gif \"commandname\" \"site or text\"```',
                    'Ganjabot finds your quotes offensive, add quotes with:',
                    '```!ganja add quote @person what you want to quote```',
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


client.run('MTg2NDE5OTMyNzEwNDM2ODY0.CjB_dQ.b9TY42kE7rybHz_TRRRNeKQePAc')
