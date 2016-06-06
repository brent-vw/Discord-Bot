import random
import re
import json
import shelve
import asyncio
import discord
import os
import giphypop
import wolframalpha
import threading
from urllib import request
from league import run_command
from helpers import youtube_url_validation
from helpers import get_vid_title
from queue import Queue
from queue import Empty

class GanjaClient(discord.Client):
    def __init__(self, tokenfile, dev=False):
        super(GanjaClient, self).__init__()
        with open(tokenfile) as f:
            data = json.load(f)
            self.server_token = data['token']
            self.dev_token = data['dev_token']
            self.wolfram = data['wolfram_token']
            self.api_token = data['open_league_token']
            self.riot_token = data['league_token']
        self.database = '.databases/'
        self.http_header = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html,application/json'}
        self.list_commands = {}
        self.voice = None
        self.player = None
        self.last_channel = None
        self.queue = Queue()
        self.queue_name = Queue()
        for i in os.listdir('data'):
            with open('data/' + i) as f:
                lines = f.read().splitlines()
                self.list_commands[i] = lines
        if dev:
            self.token = self.dev_token
        else:
            self.token = self.server_token

    def run(self):
        super(GanjaClient, self).run(self.token)
        td = PlayThread(self)
        td.start()

    def get_from_shelve(self, name, item):
        with shelve.open(self.database + name) as db:
            return db[item]

    def add_to_shelve(self, name, key, value):
        with shelve.open(self.database + name) as db:
            db[key] = value

    def get_command(self, key):
        try:
            return self.get_from_shelve('commands', key)
        except:
            raise Exception('Entry not found.')

    def add_command(self, key, value):
        self.add_to_shelve('commands', key, value)

    def remove_command(self, key):
        try:
            with shelve.open(self.database + 'commands') as commands:
                del commands['!' + key]
                return 'Command: ' + key + ' was removed.'
        except KeyError:
            return 'Command: ' + key + ' could not be found.'

    def get_command_list(self):
        with shelve.open(self.database + 'commands') as db:
            ret = db
            return list(ret.keys())

    def is_command(self, arg):
        with shelve.open(self.database + 'commands') as db:
            return arg in db

    def get_quote(self, key, value):
        try:
            return self.get_from_shelve('quotes', key)
        except:
            raise Exception('Entry not found.')

    def add_quote(self, quotee, mess):
        with shelve.open(self.database + 'quotes') as quotes:
            if quotee not in quotes:
                quotes[quotee] = []
            tmp = quotes[quotee]
            tmp.append(mess)
            quotes[quotee] = tmp

    def get_user(self, quotee):
        try:
            return self.get_from_shelve('users', quotee)
        except KeyError:
            return 'Entry not found.'

    def find_id(self, member):
        with shelve.open(self.database + 'users') as users:
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

    @asyncio.coroutine
    def on_message(self, message):
        if str(message) == 'INTERNAL':
            mess = '!dj next'
        else:
            mess = message.content
            self.last_channel = message.channel
        if not mess.startswith('!'):
            return
        if mess.startswith('!lol'):
            yield from self.send_typing(message.channel)
            args = mess.replace('!lol ', '').replace(' ', '-', 1).split('-')
            if len(args) == 1:
                args.append('None')
            if args[0] != 'counters':
                yield from self.send_message(message.channel, run_command(args[0], args[1]))
            else:
                resp = run_command('counters', args[1])
                if resp.endswith('.png'):
                    yield from self.send_file(message.channel, resp)
                else:
                    yield from self.send_message(message.channel, resp)
        elif mess.startswith('!wolfram'):
            yield from self.send_typing(message.channel)
            wol = wolframalpha.Client(self.wolfram)
            res = wol.query('\'' + mess.replace('!wolfram ', '') + '\'')
            try:
                yield from self.send_message(message.channel, res.pods[1].img)
            except IndexError:
                yield from self.send_message(message.channel, mess.replace('!wolfram ', '') + ' was not found.')
        elif mess.replace('!', '').split()[0] in self.list_commands:
            yield from self.send_typing(message.channel)
            ls = mess.replace('!', '').split()[0]
            yield from self.send_message(message.channel, random.choice(self.list_commands[ls]))
        elif mess.startswith('!cat bomb'):
            yield from self.send_typing(message.channel)
            mess = mess.replace('!cat bomb ', '')
            try:
                count = int(mess)
                if count > 10:
                    count = 10
            except ValueError:
                count = 1
            ans = ''
            for i in range(count):
                req = request.Request('http://random.cat/meow.php', headers=self.http_header)
                with request.urlopen(req) as f:
                    response = f.read().decode('UTF-8')
                response_dict = json.JSONDecoder().decode(response)
                ans += response_dict['file'] + '\n'
            yield from self.send_message(message.channel, ans[:-1])
        elif mess.startswith('!deletecommand'):
            yield from self.send_typing(message.channel)
            command = mess.replace('!deletecommand ', '').replace('!', '').strip()
            yield from self.send_message(message.channel, self.remove_command(command))
        elif mess.startswith('!decide'):
            yield from self.send_typing(message.channel)
            mess = mess.replace('!decide ', '')
            dec = mess.split('or')
            if len(dec) < 2:
                answer = 'Usage: !decide something **or** something...'
            else:
                answer = 'I\'d go with: **' + dec[random.randint(0, len(dec) - 1)] + '**'
            yield from self.send_message(message.channel, answer)
        elif mess.startswith('!gif'):
            yield from self.send_typing(message.channel)
            mess = mess.replace('!gif ', '')
            g = giphypop.Giphy()
            results = [x for x in g.search(mess)]
            if not results:
                results.append('Gif could not be found for: ' + mess)
            result = results[random.randint(0, len(results) - 1)]
            yield from self.send_message(message.channel, result)
        elif mess.startswith('!add'):
            yield from self.send_typing(message.channel)
            mess = mess.replace('!add ', '')
            if mess.startswith('gif '):
                mess = mess.replace('gif ', '').replace(' \"', '---\"')
                key_val = mess.split('---')
                if len(key_val) < 2:
                    yield from self.send_message(message.channel, 'usage: !add gif \"command name\" \"site or text\"')
                else:
                    key = key_val[0].replace('!', '').replace('\"', '')
                    key = '!' + key
                    value = key_val[1].replace('\"', '')
                    self.add_command(key, value)
                    yield from self.send_message(message.channel, key + ' was added.')
            elif mess.startswith('quote'):
                mess = message.clean_content.replace('!add quote ', '')
                mess = re.sub(r'@\S+\s', '', mess)
                if len(message.mentions) != 1:
                    yield from self.send_message(message.channel, 'usage: !add quote @person quote')
                else:
                    quotee, added = self.find_id(message.mentions[0].mention)
                    self.add_quote(quotee, mess)
                    yield from self.send_message(message.channel,
                                                 '' + self.get_user(quotee) + ' \"' + mess + '\" was added.')
        elif mess.startswith('!quote'):
            yield from self.send_typing(message.channel)
            if len(message.mentions) != 1:
                yield from self.send_message(message.channel, 'usage: !quote @person number (optional)')
            else:
                quotee, added = self.find_id(message.mentions[0].mention)
                if added:
                    yield from self.send_message(message.channel, 'No quotes for ' + self.get_user(quotee) + ' :(')
                else:
                    mess = message.content.replace('!quote ', '')
                    mess = re.sub(r'@\S+\s', '', mess).strip().replace('<', '')
                    quote_list = self.get_from_shelve('quotes', quotee)
                    if mess == 'list':
                        quote_line = '\r\n'.join(quote_list)
                        response = '```' + quote_line + '```'
                        yield from self.send_message(message.channel, '' + self.get_user(quotee))
                        yield from self.send_message(message.channel, response)
                    else:
                        try:
                            index = int(mess) - 1
                        except ValueError:
                            index = -1
                        if index == -1 or index >= len(quote_list):
                            index = random.randint(0, len(quote_list) - 1)
                        yield from self.send_message(message.channel,
                                                     '' + self.get_user(quotee) + '\n' + str(index + 1) + ': ' +
                                                     quote_list[
                                                         index])
        elif mess.startswith('!help'):
            yield from self.send_typing(message.channel)
            if mess.startswith('!help list'):
                response = ['List of user added commands:', '```']
                for x in self.get_command_list():
                    response.append(x + '\n')
                response.append('```')
                yield from self.send_message(message.channel, ''.join(response))

            else:
                cmds = '```'
                cmds += '!gif search term\r\n'
                cmds += '!decide something or something...\r\n'
                cmds += '!wolfram something\r\n'
                for command in self.list_commands.keys():
                    cmds = cmds + '!' + command + ' \r\n'
                cmds += '```'
                response = ['Ganjabot feels very attacked but wants to learn, you can add images or messages with:',
                            '```!add gif \"command name\" \"site or text\"```',
                            'Ganjabot finds your quotes offensive, add quotes with:',
                            '```!add quote @person what you want to quote```',
                            'View league commands with: ```!lol```',
                            'View quotes with:',
                            '```!quote @person'
                            '\r\n!quote @person number'
                            '\r\n!quote @person list```',
                            'For a list of user added commands:',
                            '```!help list```',
                            'Miscellaneous commands:',
                            cmds
                            ]
                query = ''
                for res in response:
                    query += res + '\r\n'
                yield from self.send_message(message.channel, query)
        elif self.is_command(mess):
            response = self.get_command(mess)
            yield from self.send_message(message.channel, response)
        elif mess.startswith('!dj'):
            mess = mess.replace('!dj ', '')
            if mess.startswith('join'):
                self.voice = yield from self.join_voice_channel(message.author.voice_channel)
            elif mess.startswith('play'):
                if self.voice:
                    if self.player:
                        if self.player.is_playing():
                            self.player.stop()
                self.voice = yield from self.join_voice_channel(message.author.voice_channel)
                self.player = yield from self.voice.create_ytdl_player(self.queue.get())
                yield from self.send_message(message.channel, 'Now playing: **' + self.queue_name.get() + '**')
                self.player.volume = 0.05
                self.player.start()
            elif mess.startswith('add'):
                url = mess.replace('add', '').replace(' ', '') + '&'
                search = re.search('([^&]*)&.*$', url)
                url = search.group(1)
                match = youtube_url_validation(url)
                if match:
                    self.queue.put(url)
                    title = get_vid_title(url)
                    self.queue_name.put(title)
                    yield from self.send_message(message.channel, '**' + title + '** was added.')
                    yield from self.delete_message(message)
            elif mess.startswith('next'):
                if self.voice:
                    try:
                        self.player = yield from self.voice.create_ytdl_player(self.queue.get())
                        yield from self.send_message(message.channel, 'Now playing: **' + self.queue_name.get() + '**')
                        self.player.volume = 0.5
                        self.player.start()
                    except Empty:
                        if self.last_channel:
                            yield from self.send_message(self.last_channel, 'List empty, stopping')
                            self.voice.disconnect()
                else:
                    yield from self.send_message(message.channel,
                                                 'Not connected to voice_channel, please use !dj join or !dj play.')
            elif mess.startswith('stop'):
                if self.voice:
                    if self.player:
                        if self.player.is_playing():
                            self.player.stop()
                    yield from self.voice.disconnect()
            elif mess.startswith('list'):
                ret = 'Current songs in queue:'
                i = 0
                for elem in list(self.queue_name.queue):
                    i += 1
                    ret += '\n**[' + str(i) + '] ' + elem + '**'
                yield from self.send_message(message.channel, ret)
            elif mess.startswith('volup'):
                if self.player:
                    self.player.volume += 0.01
            elif mess.startswith('voldown'):
                if self.player:
                    self.player.volume -= 0.01


class PlayThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        try:
            while True:
                if self.client.voice:
                    if self.client.player:
                        if not self.client.is_playing():
                            yield from self.client.on_message('INTERNAL')
                    else:
                        yield from self.client.on_message('INTERNAL')
        except KeyboardInterrupt:
            return
