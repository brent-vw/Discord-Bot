import random
import re
import urllib
import json
import shelve
import asyncio
import discord
import sys
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
        await client.send_message(message.channel, emoji[random.randint(0, len(emoji) - 1)])
    elif mess.startswith('!drama'):
        await client.send_typing(message.channel)
        await client.send_message(message.channel, drama[random.randint(0, len(drama) - 1)])
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


def ball():
    answers = random.randint(1, 9)
    if answers == 1:
        return "🎱 It is certain 🎱"
    elif answers == 2:
        return "🎱 Outlook good 🎱"
    elif answers == 3:
        return "🎱 You may rely on it 🎱"
    elif answers == 4:
        return "🎱 Ask again later 🎱"
    elif answers == 5:
        return "🎱 Concentrate and ask again 🎱"
    elif answers == 6:
        return "🎱 Reply hazy, try again 🎱"
    elif answers == 7:
        return "🎱 My reply is no 🎱"
    elif answers == 8:
        return "🎱 My sources say no 🎱"
    elif answers == 9:
        return "🎱 Nigga... 🎱"


emoji = [
    '🔊🔊🚨🚨WARNING🔊🚨🚨WARNING🚨🚨🔊THIS IS A 🐸DANK 👽MEME❗❗ 🐸ALERT. INCOMING 🐸DANK 👽MEME🐸 👐👌HEADING STRAIGHT 🚀🚀YOUR WAY. 🔜👆👆👆PLEASE TAKE ANY PRECAUTIONS🚧🚧 NECESSARY TO PREPARE YOURSELF FOR THIS 🐸DANK 👽MEME❗❗ 🐸 🌋🌋🌋 .BUCKLE UP♿♿♿ THEM SEATBELTS👮👮,PUT THEM CELLPHONES ON SILENT📵📵 AND LOOSEN THAT ANUS👅👅🍑🍑🍑🍩🍩💩💩 CUZ THIS MEME JUST CAME STRAIGHT OUT OF THE 🚬🚬 🍁🏭🍁🏭🍁🚬🚬DANK FACTORY.',
    '✋✋✋✋✋hol\' up hol\' up ✋✋ looks 👀 like we got a master 🎓 memer 🐸🐸🐸 over here 👈👈👈👩🏼👩🏼hold on to your 👙panties👙ladies!💋💁fuccbois better back the hell ⬆️up⬆️ this absolute 🙀🙀🙀 maaaaaadman!!1! 👹 all you other aspiring 🌽🌽 memers👽👻💀 mmmight as wwwell give up! 👎👎👎👎cuse 👉this guy👈is as good 👌👌👌as it gets! 👏👏👏😹😹',
    '💀💀💀💀🎺🎺🎺NOW WATCH ME SPOOK💀💀💀NOW WATCH ME DOOT DOOT🎺🎺🎺🎺NOW WATCH ME SPOOK SPOOK💀💀💀💀💀🎺🎺🎺🎺WATCH ME DOOT DOOT💀🎺🎺💀🎺💀🎺🎺💀',
    'Get dunked, m8 💯💯 You jUSt goT🏀🏀🏀r👌👌oasted🏀🏀🏀💯💯💯Dunked👌👌gEt🏀💯💯👌👌👀👀👀🔥🔥sAvaGe✔✔👌👌👌💯💯💯🔥🔥🏀🏀🏀🏀✔✔✔👀👀👀ggeettttt dUNNKkeDdd oNnn!!👌👌gET it🏀🏀YouRe goNNa haVe a Bad👎👎👎👎👎tim🕐🕐e he✔✔Re🏀🏀👌👌👌🏀💯💯gEt dUNked❌👍👍so sa🔥🔥vaGe he rekt❌❌himself﻿',
    '💯💯hOHoHOHHHHMY GOFD 😂😂😂 DUDE 👌i AM 👉LITERALLY👈 iN 😂TEARS😂 RIGHT NOW BRo 👆👇👉👈 hHAHAHAHAHAHAHA ✌️👌👍 TAHT WA SOO FUNNY DUd 💧💧😅😂💦💧I cAN NOT BELIEV how 💯FUNny 👌👍💯thta shit wa s 👀👍😆😂😂😅 I 👦 CAN NOT ❌ bRATHE 👃👄👃👄❌❌ / HELP ❗️I NEEd 👉👉 AN a m b u l a n c e🚑🚑 SSSooOOoo00000oOOOOOøøøØØØØØ FUNY ✔️☑️💯💯1️⃣0️⃣0️⃣😆😆😂😂😅 shit man ❕💯💯🔥☝️👌damn',
    'OMG 😱😱😱 BRO👬 CALM 😴😴 DOWN BRO ⬇️⬇️ SIMMER ☕️☕️ DOWN⬇️⬇️ U WANNA KNOW Y⁉️ BC 💁💁 IT WAS JUST A PRANK 😂😂😂 😛😜 HAHAHA GOT U 👌👌 U FUKIN RETARD 😂😁😁THERE\'S A CAMERA 📹📷 RIGHT OVER 👈👇👆☝️ THERE 📍U FAGOT 👨‍❤️‍💋‍👨👨‍❤️‍💋‍👨👐WE 👨‍👨‍👦 GOT U BRO👬. I BET U DIDNT 🙅🙅NOE 💆HOW 2⃣ REACT WHEN MY 🙋 BRO DESMOND 😎😎 CAME UP ⬆️ TO U AND 💦💦😫😫 JIZZED ALL OVER UR 👖👖 SWEET JEANS 😂😂 IT WAS SO FUNNY 😂😛😀😀😅 NOW U HAVE 🙋👅👅 SUM BABY👶👶 GRAVY 💦🍲 ALL OVER THEM SHITS😵😵IT\'S JUST A PRANK BRUH',
    '👌👀👌👀👌👀👌👀👌👀 good shit go౦ԁ sHit👌 thats ✔ some good👌👌shit right👌👌th 👌 ere👌👌👌 right✔there ✔✔if i do ƽaү so my selｆ 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 👌👌 👌НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👌 👌👌 👌 💯 👌 👀 👀 👀 👌👌Good shit',
    '👎👀👎👀👎👀👎👀👎👀  bad shit ba̷̶ ԁ sHit 👎 thats ❌ some bad 👎👎shit right 👎👎 th   👎 ere 👎👎👎 right ❌ there ❌ ❌ if i do ƽaү so my selｆ🚫 i say so 🚫 thats not what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ 🚫 👎 👎👎НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ 👎 👎👎 👎 🚫 👎 👀 👀 👀 👎👎Bad shit',
    '👌👽👌👽👌👽 ayy lmao ayyy lmao lmao👌 thats ✔ some ayyy👌👌lamayo right👌👌there👌👌👌 right✔there ✔✔if i do LMAO so my self 💯 i ayyy so 💯 thats what im probing about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 👌👌 👌AAAYYYYyyyyYYYYYyyyyyyʸʸʸʸʸʸʸʸ👌 👌👌 👌 💯 👌 👽👽👽👌👌ayy lmao',
    '💣🕛💣🕜💣🕝💣🕞💣👀🕙🕑 bomb clock boMb cLock💣 thats ⏰ a🕛 bomb ass 🕑💣⏰clock right💣💣there🕞💣🕙 right⏰there 💣💣i built it my self 👳 i built it 👳 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ👳 💣🕞 💣НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🕑💣⏰⏰ 💣 👳 💣 👀⏰🕙🕐 💣💣Bomb clock',
    '💩🐃💩🐃💩🐃💩🐃💩🐃 bull shit bull sHit💩 thats ✖️ some bull💩💩shit right💩💩th 💩 ere💩💩💩 right✖️there ✖️✖️if i do ƽaү so my selｆ ‼️ i say so ‼️ thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ‼️ 💩💩 💩HO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ💩 💩💩 💩 ‼️ 💩 🐃 🐃 🐃 💩💩Bull shit',
    '✈🏢✈🏢✈🏢✈🏢✈🏢 bush did 9/11✈ bush ✔ did it✈🏢blew up✈🏢the towers✈🏢🏢🌏 the✔towers ✔✔if i do ƽaү so my self 👀 watch loose change 👀 how did tower seven collapse tower seven tower seven (chorus: ᵗᵒʷᵉʳ ˢᵉᵛᵉᶰ) mMMMMᎷМ🌏 👌👌 👌НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👌 👌👌 👌 🌏 ✈ 🏢 🏢 👀 👌👌bush did it',
    '🍕🍅🍕🍅🍕🍅🍕🍅🍕🍅 cheesy shit cheesy sHit🍕 thats ✔ some cheesy🍕🍕shit right🍕🍕th 🍕 ere🍕🍕🍕 right✔there ✔✔if i do ƽaү so my selｆ 🍴 i say so 🍴 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🍴 🍕🍕 🍕НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🍕 🍕🍕 🍕 🍴 🍕 🍅🍅🍅 🍕🍕Cheesy shit',
    '🎃👻🎃👻🎃👻👻👻🎃👻 spooky shit spooky sHit🎃 thats ✔ some spooky🎃🎃shit right🎃🎃th 🎃 ere🎃🎃🎃 right✔there ✔✔if i do ƽaү so my selｆ 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 🎃🎃 🎃BO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🎃 🎃 🎃 🎃 💯 🎃 👻👻 👻 🎃🎃spooky shit',
    '❤️😍❤️😍❤️😍❤️😍❤️ m\'lady shit m\'lady sHit❤️ thats ✔ some m\'lady 😍😍shit right❤️❤️there😍😍😍 right✔there ✔✔if i do ƽaү so my self 🙇 i say so 🙇 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🙇 😍😍😍НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ😍😍😍😍 🙇 😍 ❤️ ❤️ ❤️ 😍 ❤️ M\'lady shit',
    '💉🔪 💉🔪💉🔪edgy shit edgY sHit 🔪thats 🔫some edgy💉💉 shit right 🔪th🔪 ere💉💉💉 right there 🚬🚬if i do ƽaү so my selｆ 🔫i say so 🔫 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🔫 🔪🔪🔪НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🔪🔪🔪 🔫 💉💉 🔪🔪 Edgy shit',
    '👴📅👴📅👴📅👴📅👴📅 old shit 0ld sHit👴 thats 💾 some old👴👴shit right👴👴th 👴 ere👴👴👴 right💾there 💾💾if i do ƽaү so my selｆ 🕙 i say so 🕥 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🕔 👴👴 👴НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👴 👴👴 👴 🕣 👴 📅 📅 📅 👴👴Old shit',
    '🐸♊️🐸♊️🐸♊️🐸♊️🐸♊️ good memes go౦ԁ mEmes🐸 thats 🔫🔫some good🐸🐸memes right🐸🐸th 🐸 ere🐸🐸🐸 right🔫there 🔫🔫if i do ƽaү so my selｆ ❓❗️👟👟❓❗️ i say so ❓❗️👟👟❓❗️ thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ❓❗️👟👟❓❗️ 🐸🐸 🐸НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🐸 🐸🐸 🐸 ❓❗️👟👟❓❗️ 🐸 ♊️ ♊️ ♊️🐸🐸Good memes',
    '💀🎺💀🎺💀🎺💀🎺💀🎺 gooD boNes n calcium💀 thank 🎺 mr skeltal g💀💀ood bones💀💀and calc💀 ium💀💀💀 good bones🎺and calcium 🎺🎺if i dootƽaү thank skeltal man 🎶 doot doot doot doot🎶 good bones n calcium good bones (chorus: ᵈᵒᵒᵗ ᵈᵒᵒᵗ) mMMMMᎷМ🎶 💀💀💀DO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒT💀 💀 💀💀 🎶 💀 🎺 🎺 🎺 💀💀thank mr skeltal',
    '✌🔪✌🔪✌🔪✌🔪✌🔪 cheeky shyte cheEky sHyte✌ thats ✖ sum cheeky✌✌shyte rite✌✌there✌✌✌ rite✖there ✖✖if i do ƽay so meself 🔨 i say so 🔨 ill bring me cru shag ur nans rusty cunt (chorus: ᶰ ᵘʳ ˢᶦˢ) mMMMMᎷМ🔨 ✌✌✌HO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ✌ ✌ ✌ ✌ 🔨 ✌ 🔪 🔪 🔪 ✌✌Cheeky shyte',
    '🍝👀🍝👀🍝👀🍝👀 good pasta gOod pASTA 🍝 thats 🍴 some good 🍝 🍝 pasta right 🍝 🍝 there 🍝 🍝 🍝 right🍴there 🍴 🍴If I do say so myself 💯 I say so 💯 that\'s what I\'m talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMMM 💯 🍝 🍝 🍝 HO0OoOOOOOOoOoooooooooooo 🍝 🍝 🍝 🍝 💯 🍝 👀 👀 👀 🍝 🍝 good pasta',
    '😩💦😩💦😩💦😩💦😩💦 sexy shit sexy sHit😩 thats 🐔 some sexy😩👅shit right😩th 😩 ere😩👅😩 right🐔there 🐔🐔if i do ƽaү so my selｆ ✊ i say so ✊ thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ✊ 😩👅😩НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ😩 😩👅 😩 ✊ 😩 💦💦 💦 😩👅Sexy shit',
    '🚫🚫🚫🚫🚫💰💰💰socialist shit socialist sHit thats ✔ some socialist🚫🚫shit right💰💰th 🚫 ere💰💰💰 right✔there ✔✔if i do ƽaү so my selｆ 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯☭☭☭НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🚫🚫🚫🚫🚫 💯 💰💰💰💰socialist shit',
    '🍗🍷🍗🍷🍗🍷🍗🍷🍗🍷thankful shit thAnkFul sHit🍛 🍛thats ✔ some ThaNkful👨‍👨‍👦🍁shit right📺👩‍👩‍👦th 🌽 ere👪🏈📺 right✔there ✔✔if i do gobble so my selｆ 💯 i say so 💯 🍗🌽thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 🏈🍷🍷НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👪📺🍗🍗💯 👩‍👩‍👦🏈🍂🍷🍷 🌽 👨‍👨‍👦Tha nkful shit',
    '👌🐶👌🐶👌🐶👌🐶 good dog go౦ԁ dOg👌 thats ✔ a gOOd 🐶 🐶 dog right 🐕 🐕 there👌👌👌 right🐶there ✔✔if i do ƽaү so my self 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 👌👌 👌НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👌 🐕 🐕 👌 💯 👌 🐶 🐶 🐶 👌👌Good dog',
    '🍤🍤👀🍤👀🍤👀🍤👀🍤👀 good shrimp go౦ԁ shrimp🍤 thats 🍤 some good🍤🍤 shirmp right🍤🍤there 🍤🍤🍤 right✔there ✔✔if i do ƽaү so my self 💯 i say so 💯 thats what im talking about right there red lobster quality shrimp (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 🍤🍤🍤НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🍤 🍤 🍤 🍤 💯 🍤 👀 👀 👀 🍤🍤Good shrimp',
    '🙏👀🙏👀🙏👀🙏👀 holy shit hoLy sHit 🙏 thats 😇 some holy 🙏 🙏 shit right 🙏 🙏 th 🙏 ere 🙏 🙏 🙏right 😇 there 😇 😇 if i do say so my sel f 👼 i say so 👼 thats what im praying about right there right (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMMM 👼 🙏 🙏 🙏 HOOOO0OOO OO O OOooooooooooo 🙏 🙏🙏 🙏 👼 🙏 👀👀👀👀 🙏 🙏 Holy shit',
    '🐱👌 🐱👌🐱👌🐱👌🐱👌 good cats go౦ԁ cAts👌 thats 🐈 some good👌👌cats right👌👌th 🐈 ere 🐱 🐱 🐱 right 🐈 there 🐈 🐈 if i do ƽaү so my selｆ 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 🐱 🐱 🐱 НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👌 👌👌 👌 💯 👌 🐈 🐈 🐈 👌👌Good cat',
    '🎁🎄🎅🎁🎄🎅🎁🎄🎅Christmas shit Christmas sHit🎅thats 🎊some Christmas🎊🎊shit right🎅🎁🎄th 🎅ere🎁🎄🎅 right🎊there 🎅🎁if i do ƽaү so my selｆ 🎊 i say so 🎊thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🎊 🎁🎅🎄НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ 🎅🎁🎄🎅🎊 🎅 🎁🎄🎊🎅Christmas shit',
    '👠👡👠👡👠👡👠👡👠👡 nice shoes niCe sHoes👠 thats 👢 some nice👠👠shoes right👠👠there👠👠👠 right👢there 👢👢if i ƽaү so my self 👟 i say so 👟 thats what im texting about right now right now (chorus: ʳᶦᵍʰᵗ ᶰᵒʷ) oOOOOᎷO👟 👠👠 👠OO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👠 👠👠 👠 💯 👠 👡👡👡 👠👠Nice shoes',
    '💀🌞💀🌞💀🌞💀🌞💀🌞 dark souls daRk sOUls💀 thats 🔥 some dark💀💀souls right💀💀there💀💀💀 right🔥there 🔥🔥if i do ƽaү so my self 🔥 i say so 🔥 thats what im talking about right there right there (chorus: ᵍʷʸᶰ ᶫᵒʳᵈ ᵒᶠ ᶜᶦᶰᵈᵉʳ) mMMMMᎷМ🔥 💀💀💀💀 🌞🌞🌞💀💀Dark souls',
    '🚹 🏀 🚹 🏀 🚹🏀 🚹 🏀 🚹 🏀 bro shit br౦ sHit 🚹thats 🎮 some bro🚹 🚹shit right 🚹th 🚹 ere 🚹 🚹 🚹 right🎮there 🎮🎮if i do ƽaү so my selｆ 🏆 i say so 🏆thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🏆🚹 🚹 🚹НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ 🚹 🚹 🚹 🚹🏆 🚹 🏀 🏀 🏀 🚹 🚹Bro shit',
    '😴💤😴💤😴💤😴💤😴💤 tired shit tiręd sHit😴 thats ✔ some tired 😴😴shit right😴😴th 😴 ere😴😴😴 right✔there ✔✔if i do ƽaү so my selｆ 🌑 i say so 🌑 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🌑 😴😴 😴YaaaaAAAaaWWWwWWwwwnnNNnnNnn😴😴😴😴 🌑 😴 💤💤💤 😴😴Tired shit',
    '💥🔫💥🔫💥🔫💥🔫💥🔫gun shit gun sHit🔫 thats 🔫some gun🔫🔫shit right🔫🔫th 💥 ere🔫🔫🔫right💥there 🔫🔫if i do ƽaү so my selｆ 🔪 i say so 🔪thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🔪 🔫🔫НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🔫🔫🔫🔫 🔪💥💥🔫🔫Gun shit',
    '🎀👀🎀👀💞👀🎀👀✨👀 kawaii shit kawaii sHit👌 thats ✔ some sugoi👌💕shit right🌟👌th 💓 ere👌✨👌 right✔there ✔✔if watashi do ƽaү so my selｆ 💯 watashi say so 💯 thats what boku wa talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 👌👌 🐱НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👌 👌🎀👌 💯 👌 👀 👀 👀 🎀👌moe shit',
    '🐺🐯🐯🐯🐺🐯 🐺🐯🐺🐯 furry shit furry sHit🐺 thats 🐲some furry🐺 🐺shit right🐺 🐺th🐺 ere🐺🐺🐺 right🐲there 🐲🐲if i do ƽaү so my selｆ 🐾 i say so 🐾 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🐾 🐺🐺🐺🐺НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🐺 🐺🐺🐺 🐾 🐺 🐯 🐯 🐯 🐺🐺Furry shit',
    '🌌🌙🌌🌙🌌🌙🌌🌙🌌🌙 space shit spACe sHit🌌 thats ✔ some space🌌🌌shit right🌌🌌th 🌌 ere🌌🌌🌌 right✔there ✔✔if i do ƽaү so my selｆ 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 🌌🌌 🌌НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🌌 🌌🌌 🌌 💯 🌌 🌙 🌙 🌙 🌌🌌Space shit',
    '🐣💕🐣💕🐣💕🐣💕🐣💕 cute shit cute sHit💕 thats 💖some cute💕💕shit right💕💕th 💕 ere💕💕💕right💖there 💖💖if i do ƽaү so my selｆ 💋 i say so 💋 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💋 💕💕💕НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒ💕💕💕 💋 💕 🐣🐣🐣💕💕Cute shit',
    '🔍 👀🔍 👀🔍 👀🔍 👀🔍 👀 dramatic shit dramati© sHit👌 thats 😒 some dramatic🔍🔍shit right🔍🔍th 🔍 ere🔍🔍🔍 right😒 there 😒 😒 if i do ƽaү so my selｆ 😓 i say so 😓 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ😓 🔍🔍 🔍НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🔍 🔍🔍 🔍😓 🔍 👀 👀 👀 🔍🔍Dramatic shit',
    '🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿dank shit dank sHit🌿thats ✔ some dank🌿🌿shit right🌿🌿th 🌿ere🌿🌿🌿right✔there ✔✔if i do ƽaү so my selｆ 🚬i say so 🚬thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🚬🌿🌿🌿НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🌿🌿🌿🌿 🚬 🌿👀 👀 👀 🌿🌿Dank shit',
    '📟💾📟💾📟💾📟💾📟💾 90s shit 90s sHit📟 thats ✔ some 90s📟📟shit right📟📟there📟📟📟 right✔there ✔✔if i do ƽaү so my self 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 📟📟 📟НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ📟 📟📟 📟 💯 📟 💾💾💾 📟📟90s shit',
    '⛵👭⛵👬⛵👫⛵👭⛵👬 good ship ba̷̶ ԁ sHit ⛵ thats 💖 some good ⛵⛵ship right ⛵⛵ th ⛵ ere ⛵⛵⛵ right 💖 there 💖 💖 if i do ƽaү so my selｆ👫 i say so 💖 thats not what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ 👭 ⛵ ⛵⛵НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ ⛵ ⛵⛵ ⛵ 👬 ⛵ 👀 👀 👀 ⛵⛵Good ship',
    '🍔🍟🍔🍟🍔🍟🍔 yummy shit yummy sHit🍔 thats 🍟 some yummy🍔🍔shit right🍔🍟th 🍟 ere🍟🍔🍟 right🍟there 🍟🍔if i do ƽaү so my selｆ 🍟 i say so 🍔 thats what im talking about right there right there (chorus : ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🍟🍔 🍟🍟🍔НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🍟🍔🍟🍔🍔🍟🍔🍟yummy shit',
    '💧⚡️💧⚡️💧⚡️💧⚡️💧stormy shit stOrmy sHit⚡️thats ☁️ some stormy⚡️⚡️shit right⚡️⚡️th ⚡️ ere⚡️⚡️⚡️ right☁️there ☁️☁️if i do ƽaү so my selｆ ☔️ i say so ☔️ thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ☔️ ⚡️⚡️ ⚡️НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ⚡️ ⚡️⚡️ ⚡️ ☔️ ⚡️ 💧💧💧 ⚡️⚡️Stormy shit',
    '🎂👀🎂👀🎂👀🎂👀 birthday shit bday shit 🎂 thats 🎁 some birth🎂🎂 shit right 🎂🎂 th🎂here🎂🎂🎂 right 🎁 there 🎁🎁 if i do ƽaү so my selｆ🏫 i say so 🏫 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ 🏫 🎂🎂🎂НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ 🎂🎂🎂🎂🏫🎂👀👀🎂🎂 birthday shit',
    '👼🙏👼🙏👼🙏👼🙏👀👼👼 pope shit poPe shit 👼 thats 🙏 some ⛪ pope ass 🙏👼💒 shit right ⛪⛪ there 👼💒🙏 right 🙏 there 👼👼 if i do preach so myƽelf ⛪ i say so 👌 thats what my sermon is about right there right there (choir: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ 🙏👼💒 НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ ⛪⛪⛪⛪⛪👼👼👀🙏🙏💒💒💒💒 Pope shit',
    '🎥👀🎥👀🎥👀🎥👀🎥👀 good shot go౦ԁ sHot🎬 thats 🎬 a good🎥🎥shot right🎬📼 th 📷 ere🎥🎥 right 🎬 there 📼🎥 if i do ƽaү so my selｆ 📼 i say so 🎬 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🎬 📷📹📼НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ 🎥🎥🎥 🎬 🎬 👀👀Good shot',
    '💦😫💦😫💦😫💦😫💦😫 desperate shit desperate sHit💦 thats 🙏 some desperate💦💦shit right💦💦there💦💦💦 right🙏there 🙏🙏if i do ƽaү so my self 🏊 i say so 🏃 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🏊 💦💦 💦НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ💦💦💦💦 🙏 💦 😩😫😩 💦💦desperate shit',
    '🚪🚫🚪🚫🚪🚫🚪🚫🚪🚫 door stuck door sTuck🚪 please 🔪 i beg you🚪🚪we’re dead🚪🚪door stuck🚪🚪🚪 door🔪stuck 🔪🔪i tried to sneak through the door man 🔫 can’t make it 🔫 outta my way son you’re a genuine door stuck (chorus: ᵈººʳ ˢᵗᵘᶜᴷ) mMMMMᎷМ🔫 🚪🚪 🚪НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🚪 🚪🚪 🚪🔫 🚪 🚫 🚫 🚫 🚪🚪Door stuck',
    '👌🍞👌🍞👌🍞👌🍞👌🍞 garlic bread gaRlic bRead👌 thats ✔ some garlic👌👌bread right👌👌there👌👌👌 right✔there ✔✔if i do ƽaү so my self 💯🍞 i say so 🍞 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ 🍞 👌👌 👌НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👌 👌👌 👌 🍞 👌 🍞 🍞 🍞 👌👌Garlic bread',
    '⚓️🐳⚓️🐳⚓️🐳⚓️🐳⚓️🐳navy seal navy sEal ⚓️ thats⛵️ a navy ⚓️⚓️ seal right ⚓️⚓️ right ⛵️ there 🚤🚤 if I do ƽaү so myself 🚢 I say so 🚢 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ ⚓️⚓️⚓⛵️️НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒ ⚓️⚓️⚓️⚓️⛵️⚓️🐳🐳🐳⚓️⚓️ good shit',
    '🔪💀🔪💀🔪💀🔪💀🔪💀 gore shit go౦re sHit🔪thats ✔ some gore🔪🔪shit right🔪🔪there🔪🔪🔪 right✔there ✔✔if i do ƽsaү so my self 💉 i say so 💉 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💉🔪🔪 🔪НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒoo🔪🔪🔪 💉 🔪 💀💀 💀 🔪Gore shit',
    '🔥🌋🔥🌋🔥🌋🌋🔥🌋 pyromancer shit pyromancer sHit🔥 thats 🌋 some pyromancer 🔥🔥shit right🔥🔥th 🔥 ere🔥🔥🔥 right🌋 there 🌋🌋if i do ƽaү so my selｆ 🌋 i say so 🌋 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🌋 🔥🔥 🔥НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🔥🔥🔥🔥 🌋🔥 🌋🌋🌋 🔥🔥pyromancer shit',
    '📚📖 📖 📚📖 📚📖calculus shit tHat’s sum cAlcuLUς $#!t📚 thats∰some good∰∭integration right∳∰there 📚 📚 📚right⨌there⨍find the limit📖find the📖limit📖that’s not showing your work right tᴴᵉᴿe 📖📖 show w0rk(chorus: ᵍᴵᵛᴱn f⁽ˣ⁾ax)mMMMMMM📖∰∯∰ НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ📚📚📚📚∰📖☕☕☕☕☕☕☕☕GOnnA FaIL',
    '😬😳🙊😥😬🙊🙊🙊😬😥 awkward shit awkward sHit😬 thats 🙊some awkward😬😬shit right😬😬th 😬 ere😬😬😬 right💬there 💬💬if i do ƽaү so my selｆ 😳 i say so 😳 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🙊 😬😬😬НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ😬😬 😬 🙊 😬😥🙊🙊😬😬awkward shit',
    '🌲👀🌲👀🌲👀🌲👀🌲👀 happy tree happy tRee🌲 thats ✔ some happy🌲🌲tree right🌲🌲there🌲🌲🌲 right✔there ✔✔if i do ƽaү so my self 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 🌲🌲 🌲НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🌲 🌲🌲 🌲 💯 🌲 👀 👀 👀 🌲🌲happy tree',
    '💩🐕💩🐕💩🐕💩🐕💩🐕 shitty shit dog sHit💩 thats ✖️ some dodgy doggy💩💩shit right💩💩th 💩 ere💩💩💩 right✖️there ✖️✖️if i do ƽaү so my selｆ ‼️ i say so ‼️ thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ‼️ 💩💩 💩HO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ💩 💩💩 💩 ‼️ 💩🐕🐕🐕 💩💩 shitty 5hit',
    '👊💪👊💪👊💪👊💪👊 Ez shit Ez sHit👊 thats 💪 some Ez 💪👍shit right👊👊there👈💪👊 rightthere if i do ƽaү so my self 💪👊 i say so👈👈 thats what im talking about right there right there 👈👈(chorus: ᴱᶻ) Ez 💪💪💪ᴱᴱᴱᴱᴱᴱᴱᴱᴱᴱᴱᴱᶻᶻᶻᶻᶻᶻᶻᶻᶻ👊👊👊👊👊 👈👈👈👊👊EZ shit👆',
    '💰🎆💰🎆💰🎆💰🎆💰🎆 good deals go౦ԁ dEals💰 there’s ✔ some good💰💰deals right💰💰there💰💰💰 right✔there ✔✔if i do ƽaү so my self 💯 i say so 💯 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💯 💰💰 💰НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ💰 💰💰 💰 💯 💰 🎆 🎆 🎆 💰💰Good deals',
    '👿😱👿😱👿😱👿😱👿😱 scary shit scãry sHit👿 thats 💀 some scary👿👿shit right👿👿there👿👿👿 right💀there 💀💀if i do ƽaү so my self 💣 i say so 💣 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ💣 👿👿 👌НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👿 👿👿 👿  💣 👿 😱 😱 😱 👿👿Scary shit',
    '🎆🎉🎆🎉🎆🎉🎆🎉 new year new year 🎉 thats 🎆 a new 🎉🎉 year right 🎉🎉 there 🎉🎉🎉 right🎆there 🎆🎆if I do say ƽo myself 🎊 I say so 🎊 thats the new year im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🎆 🎉🎉 🎉O0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🎉 🎉🎉🎉🎊 🎉 🎆🎆🎆 🎉🎉Happy New Year🎆',
    '⛄🎄⛄🎄⛄🎄⛄🎄 merry christmas mErry cHristmas⛄ thats ❄ some merry⛄⛄ christmas right⛄⛄there⛄⛄⛄ right❄there ❄❄if i do ƽaү so my self 🎁 i say so 🎁 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🎁 ⛄⛄ ⛄НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ⛄ ⛄⛄⛄🎁 ⛄ 🎄🎄🎄 ⛄⛄Merry christmas',
    '😈🔥😈🔥😈🔥😈🔥😈🔥going to hell gOing to hEll 👇 goin👇👇 to hell 👇👇go⬇⬇ing to he🔥ll 🎻🎻 if i do say so myself 😈i say so 🔥 prayin cannot help me now (chorus: ʲᵉᵉᵇᵘˢ ʰᵃᶫᶫᵉᶫᵘʲᵃʰ) mMMMM MM ⛪ 🎻🔥HØOOoooOOoooOOO ⬇⬇⬇👇👇😈🔥😈🔥 goin to helL',
    '🐝👀🐝👀🐝👀🐝👀🐝👀🐝 bee shit bEe sHit👌 thats ✔ some good🐝🐝bee shit right🐝🐝th🐝 ere🐝🐝🐝 right✔there ✔✔if i do ƽaү so my selｆ 💯🐝 i say so 💯🐝 thats what im talking about right 🐝 there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) bBBBb💯🍯🍯🍯🐝BzzzZzzZZzzzᶻᶻᶻᶻᶻᶻᶻᶻᶻ💯🍯🍯🍯BZZzZ 🐝 💯 🐝 👀 👀 👀 💯🐝🐝Good bee shit',
    '🔯💵🔯💵🔯💵🔯💵🔯💵 oy vey Oy vEy🔯 thats 👃 some jewish🔯🔯 shit right🔯🔯 there🔯🔯🔯 right👃 there 👃👃 if i do ƽaү so my self 👴 i say so 👴 thats what im talking about right there right there (chorus: ᵐᵃᶻᵃᶫ ᵗᵒᵛ) mMMMMᎷМ👴🔯🔯🔯 НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🔯🔯🔯🔯👴🔯💵💵💵🔯🔯 Oy vey',
    '💪( ͡° ͜ʖ ͡°)💪( ͡° ͜ʖ ͡°)💪( ͡° ͜ʖ ͡°)💪( ͡° ͜ʖ ͡°) Kinky shit kinkY sHIt 💪 thatS 👉👌 Some kinky ( ͡° ͜ʖ ͡°) shit 👉👌 right ☺️ There ☺️☺️ if I do ƽaү so myself 👯 I say so 👯 if you know what im talking about 🍑🍌 right there 🍑🍌 right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMM 👯 ( ͡° ͜ʖ ͡°) НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ ( ͡° ͜ʖ ͡°) ( ͡° ͜ʖ ͡°) 👉👌 😍☺️💪👅 kinky shit',
    '🍭🍬🍭🍬🍭🍬🍭🍬 sweet shit swEet sHit 🍭 thats 🍰 some sweet 🍭🍭 shit right 🍭🍭 th🍭ere 🍭🍭🍭 right🍰there🍰🍰 if i do  ƽaү so my selｆ 🍩i say so🍩thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🍩 🍭🍭 🍭НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🍭 🍭🍭 🍭 🍩🍭 🍬🍬🍬 🍭🍭 Sweet shit',
    '📝📎📝📎📝📎📝📎📝📎 good paper go౦ԁ paPer📝 thats 💻 a good📝📝paper right📝📝th 📝 ere📝📝📝 right💻there 💻💻if i do ƽaү so my selｆ 💯 i say so 💯 thats what im talking about right there perfect grammar (chorus: ᵖᵉʳᶠᵉᶜᵗ ᵍʳᵃᵐᵐᵃʳ) mMMMMᎷМ💯 📝📝 📝НO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ📝 📝📝 📝 💯 📝 📎 📎📎 📎 📝📝Good paper',
    '👌🎩👓🎩👍🎩👓🎩👍🎩 euphoric logic !euphoric loGic👌 thats ✔ some euphoric👌💻 logic right👌💻there👌👍👌 Carl 🔭 Sagan🌌💫if i do ƽaү so gentlemen 💯 i say so 💯 thats euPhoric logic right there Richard 📒 Dawkins🎩 (chorus: ˢᵒᶜʳᵃᵗᵉˢ ᵈᶦᵉᵈ ᶠᵒʳ ᵗʰᶦˢ ˢʰᶦᵗ) mMMMMᎷМ💯 👌👓👌НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ👌 👌🎩 👌 💯 👌 👓🎩🎩🎩 👍👌euphoric logic',
    '💻📊💻📊💻📊💻📊💻📊  thats 📒 some Excel-lent💻💻shit right💻💻th 💻 ere💻💻💻 right📒there 📒📒if i do 📊 ƽaү so my selｆ📒 i say so my 💻💻se 💻💻lf 📊 ledger en trie 📊 s 📊 📒 thats some verti📒 c a l 💻 shit right there 📊 right there (chorus: table_array) mMMMMᎷМ 📒 💻💻 💻 mmMmicr o sO0ОଠＯOOＯOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒft 💻 💻💻 💻 📒 💻 📊 📊 📊 📒 💻💻Vertical shit',
    '🍟 🍔 🍕 🍔 🍕 🍔 🍕 🍔 🍕🍟 fat shit fAT sHit 🍖 thats🍪 some fat 🍰🎂 shit right🍫🍩there 🍧🍨🍮 right 🍪 there 🍖🍟 if I do say so my self 🍩 i say so 🍩 thats what im talking about right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷm🍕🍟🍟🍟НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🍕🍟🍧🍨🍪🍖🍮🍰🍩🍫🍪🍧🍮🍨🍪 fat shit',
    '🔑🙏🔑🙏🔑🙏🔑🙏🔑🙏🔑success shit success sHit ✔ that some🔑🔑to success shit right🔑🔑there🔑🔑🔑right✔there ✔✔if i do bless up my self 🍏 i do bless up 🍏 thats another one right there right there (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) mMMMMᎷМ🍏🔑🔑🔑НO0ОଠOOOOOОଠଠOoooᵒᵒᵒᵒᵒᵒᵒᵒᵒ🔑🔑🔑🔑🍏🔑🙏🙏🙏🔑🔑success shit',
    '🐜🙋🏼🌐🐜 🌐SpIder WeBs 🙋🏼🏡📞 🚫💤🏡📞 ⁽ʸᵉᵃʰ⁾ Sorry I’m not home right now🏡 📞🚫💤🏡 🚫💤I’m walking into spiderwebs 🙋🏼👠🐜🌐 👠📞So leave a message📥📞📥📞 and I’ll call you back  (ᶜᵃᶫᶫ ʸᵒᵘ ᵇᵃᶜᵏ) 📥 🐜🌐🐜🌐Leave a message and I’ll call you back ⁽ᶜᵃᶫᶫ ʸᵒᵒᵒᵒᵒᵘ ᵇᵃᵃᵃᵃᶜᵏ⁾🚫💤🏡🙋🏼🌐🐜',
    '🚨🚨🚨 WEE WOO WEE WOO WEE WOO 🚨🚨🚨 YOU ARE BEING DETAINED 💀💀🎺💀 FOR BEING AWAKE DURING REAL SPO0KY HOURS 🕐💀 PLEASE SHOW ME YOUR REAL SPO0KY REGISTRATION 🙉🎺💀 NO FUCCBOIS REAL SKELTONS ONLY!! IT DONT MATTER IF YOU DOOTING OR WHAT 💯💯💯',
    '📅This Sunday📆 We Set Our Clocks🕛🕑🕓🕕🕗🕙🕛 An Hour Forward ⏩ But Im Here To Tell You 💬 👆That Im 🚫 N O T 🚫Leaving Your Ass 🍑 Behind 💯💯 We Move On Together 👫 So When The Sun Goes Down 🌃 We Wake Up ✔️ Together ✔️ This Is Our Future 🌇🌅 This Is Our Time⌚️ Happy Daylight Savings 🎉🎊',
    '2015 was tuff 😓😰, challenqinq ‼️🙇, i learned wut love<3💕 💏 iz, wut pain 😩🔫 iz, i made new freinds 👫👫 <3 i lost some old freinds 🙅🙅 </3 i learned who i am 💁🏼👸 nd who i am not 😷. but no matter wut, i am who i am 😈. liv lyff w/ no reqretzz 👌. i am stronqer now 💪. cant wait 4 new year, new me 💁💁 <3; xoxo 😉',
    'You can\'t 〽 💲🀄ÜⓂ🅿 the Trump 📈💪🔥🔥 (liberal tears 😭😭💧💦🌊) BUILD 🔧👷🔨 WALL 🚪🚪🚪 BUILD A BIG ➕➕ BEAUTIFUL 💓💓💓 WALL 🚪🚪🚪🚪🚪 right there 👉🌎 (chorus: ʳᶦᵍʰᵗ ᵗʰᵉʳᵉ) Make America 🗽🗽 Great Again 💃👉 🚪 Trump 2016 📈☑☑☑',
    '😠😠😡😡🆘LIKE OH MY GOD👻👻❕❕ 😴WAKE UP😴 SHEEPLE CANT YOU 👀SEE 👀WHATS GOING ON😷😷?!? FIRST OFF IT IS 💯💯% 👍PROVEN👍 FACT THAT 🔯🔯JET✈✈ FUEL💦💦 🚫🚫CANT🚫🚫 MELT 🔥🔥STEEL BEAMS💥❕❕ LIKE JESUS CHRIST, THOSE WERE 👯💀CRISIS ACTORS💀👯 AT 🔪SANDY HOOK🔫❕❕ LIKE 😈LUCIFER😈 ALL MIGHTY, I CAN NAME OVER 💯 👮👮BLACK OPS 👮👮FALSE 🚩🚩FLAG OPERATIONS🚩🚩 OFF THE TOP OF MY HEAD!!! SERIOUSLY 😨WAKE😨 🆙!😭😭',
    'Water... 💧💦🌊 Earth... 🌎⚰⛰ Fire... 🔥☀️💥 Air. 🌪💨🌬 Long ago, 🕐🕜🕠 the 4️⃣ nationslived 2️⃣gether in harmony. 😊❤️ Then everything changed 😨😰 when the Fire 🔥💥 Nation attacked. ⚔💣😱 Only the Avatar, master of all 4️⃣ elements 💦🔥🌎🌪 could stop🚦them. But when the world 🌎🌍🌏 needed him most, he vanished. 😵 A hundred 💯 years 📅 passed and my brother 👦 and I 👸 discovered the🆕 Avatar 😊😌, an airbender 🌪🌬 named Aang. 😎🆒 And although his airbending🌪🌬 skills are great, 👍👌 he still has a lot to learn ✏️📝 before he\'s ready to save any1️⃣. 😀😀😀But I believe Aang can save the world. 😇🌎🌏',
    'OO mY, 😏 OH MY, i LOoOVE💘❤️💚 MY SEnpAI😏🙊✌️ KaAWAAII 🐠dESU DESU HEntai🐙 CHAN😜 how i want u TO nOtice 👀👌👀👌ME sEN PIE🍰 i WANT ur sQUIshy WASABI🎾😈 on my Sushi✊🍣🍤SPICY 🔥🔥🔥🔥leT’S mAKE sOME ORIGAMI😩😏🇯🇵 MY mASTER sENSEI 😯😑 DOKI DOkI tofU 😳🙀 '
    ]

drama = [
    'http://i.imgur.com/IwJnS7s.gif',
    'http://i.imgur.com/2QBVNEy.gif',
    'http://i.imgur.com/Vflx6FT.gif',
    'http://i.imgur.com/GbIaoT0.gif',
    'http://i.imgur.com/H3NmH9A.gif',
    'http://i.imgur.com/mF0tsPR.gif',
    'http://i.imgur.com/lSsR6sD.gif',
    'http://i.imgur.com/PSi8gtA.gif',
    'http://i.imgur.com/iMJOWmk.gif',
    'http://i.imgur.com/tx0RTpO.gif',
    'http://i.imgur.com/7qQ1WXA.gif',
    'http://i.imgur.com/373kW4w.gif',
    'http://i.imgur.com/hIFLJlG.gif',
    'http://i.imgur.com/80bF923.gif',
    'http://i.imgur.com/0nBAsqC.gif',
    'http://i.imgur.com/KKVHZTt.gif',
    'http://i.imgur.com/DdnIFi2.gif',
    'http://i.imgur.com/OX2r7f3.gif',
    'http://i.imgur.com/NdyVfGj.gif',
    'http://i.imgur.com/5eJXar4.gif',
    'http://i.imgur.com/qP9Mbm2.gif',
    'http://i.imgur.com/E6Fkk97.gif',
    'http://i.imgur.com/BIJdWtz.gif',
    'http://i.imgur.com/rRAKiSv.gif',
    'http://i.imgur.com/lj1UGpj.gif',
    'http://i.imgur.com/jqr2gUM.gif'
]

client.run(dev_token)
