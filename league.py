import urllib
import json
import shelve
import grequests
import traceback
from datetime import date, timedelta
from bans import create_image
__docformat__ = 'reStructuredText'


class League:
    """
    Helper class for handling **lol** related requests received by the GanjaClient.
    """
    def __init__(self, open_token, riot_token, header):
        """
        Initializes the helper class
      :param open_token: the api token for use with the **champion.gg** open api.
      :param riot_token: the api token for use with the **riot** api.
      :param header: http header used by api requests.
        """
        with open('league/info') as f:
            data = json.load(f)
            self.regions = data['regions']
            self.positions = data['positions']
            self.platforms = data['platforms']
        self.header = header
        self.riot_token = riot_token
        self.open_token = open_token
        self.dispatch = {
            'status': self.status,
            'match': self.find_match,
            'counters': self.get_matchup,
            'bans': self.get_bans,
            'best': self.get_roles,
            'help': self.info
        }

    @staticmethod
    def format_list(lst, init_statement):
        """
        Turns a list into a GanjaClient formatted response message.
      :param lst: list of responses
      :type lst: list
      :param init_statement: statement the message should begin with
      :type init_statement: str
      :returns: str
        """
        response = [init_statement]
        for i in range(len(lst)):
            delim = '  '
            if i == 9:
                delim = ' '
            response.append(str(i + 1) + ':' + delim + lst[i])
        return '\n'.join(response)

    @staticmethod
    def get_image(champion):
        """
        Retrieves the id to get the image of a certain champion from the local storage.
      :param champion: name of the champion
      :type champion: str
      :returns: str -- name of the img resource
        """
        champions = None
        try:
            champions = shelve.open('champions')
            return champions[champion]['img']
        finally:
            if champions:
                champions.close()

    @staticmethod
    def info(args=None):
        """
        Returns a list of commands which GanjaClient can send to the discord server.
      :param args: empty, used so for dynamic method invocation
      :type args: None
      :returns: str -- list of commands
        """
        return 'Ganja plays lol too! Here are the comands she recognizes:\n\r' + \
               '**!lol** status\n  Get the LoL Game and Client server status for all regions\n' + \
               '**!lol** match region summoner-name\n ' \
               'Get match information for the __current__ match (might take a few seconds)\n' + \
               '**!lol** counters champ-name position\n Get the top 10 counters for a champion and position\n' + \
               '**!lol** bans\n Get the top 10 most common bans\n' + \
               '**!lol** best position\n Get the 10 best champions for a given position\n' + \
               '**!lol** help\n Display this message'

    def get_champions(self, keys=False):
        """
        Populates the local storage with the latest static champion information from the riot servers,
        if it hasn't updated for more than 2 days.
      :param keys: whether to return a list of champion_keys and names or only names
      :type keys: bool
      :returns: list, list or list -- list of champions by keys and/or by names
        """
        champions = None
        try:
            champions = shelve.open('champions')
            if 'date' not in champions:
                champions['date'] = date.today() - timedelta(days=2)
            if champions['date'] != date.today():
                champions.clear()
                champions['date'] = date.today()
                resp = self.get_response(
                    'https://global.api.pvp.net/api/lol/static-data/euw/v1.2/champion?champData=image&api_key=' +
                    self.riot_token)
                champions['list'] = []
                champions['keys'] = []
                for x in resp['data'].values():
                    name = x['name']
                    c_id = x['id']
                    img = x['image']['full']
                    title = x['title']
                    key = x['key']
                    tmp = champions['list']
                    tmp.append(name)
                    champions['list'] = tmp
                    tmp2 = champions['keys']
                    tmp2.append(key)
                    champions['keys'] = tmp2
                    champions[name] = {'name': name, 'id': c_id, 'img': img, 'title': title, 'key': key}
                    champions[str(id)] = name
            if 'img' not in champions:
                champions['image'] = 'http://ddragon.leagueoflegends.com/cdn/6.11.1/img/champion/'
            if keys:
                ret = champions['keys']
                return ret, champions['list']
            return champions['list']
        finally:
            if champions:
                champions.close()

    def get_response(self, url):
        """
        Opens a connection with the api server sending the request and returning the response formatted to a dictionary.
      :param url: the request encoded url
      :type url: str
      :returns: dict -- response of the server
        """
        request = urllib.request.Request(url, headers=self.header)
        with urllib.request.urlopen(request) as f:
            response = f.read().decode('UTF-8')
        response_dict = json.JSONDecoder().decode(response)
        return response_dict

    def get_bans(self, args):
        """
        Requests the most banned champions from the champion.gg api and reformats it to an unique top 10
      :param args: empty, used so for dynamic method invocation
      :type args: None
      :returns: str -- formatted response to be send to the discord server
        """
        lst = self.get_response('http://api.champion.gg/stats/champs/mostBanned?api_key=' + self.open_token +
                                '&limit=25')['data']
        message = 'Here\'s the list of the top 10 most common bans:\n'
        messages = []
        champs = []
        for x in lst:
            champ = x['name']
            if champ not in champs:
                champs.append(champ)
                messages.append('**' + champ + '**')
            if len(champs) == 10:
                break
        return self.format_list(messages, message)

    def get_roles(self, lane):
        """
        Requests the champion.gg api which champions are the best for a given role.
      :param lane: the given role
      :type lane: str
      :returns: str -- formatted response to be send to the discord server
        """
        try:
            position = self.positions[lane]
        except KeyError:
            return 'Role: **' + lane + '**, could not be found.'
        lst = self.get_response('http://api.champion.gg/stats/role/' + position +
                                '/bestperformance?api_key=' + self.open_token)['data']
        message = 'Here\'s the top 10 of role: **' + position + '**'
        messages = []
        for x in lst:
            champ = x['name']
            win_rate = x['general']['winPercent']
            messages.append('**' + champ + '** with a ' + str(win_rate) + '% win rate.')
        return self.format_list(messages, message)

    def find_champion_name_by_key(self, name):
        """
        Looks up the champion name give the ChampionKey
      :param name: name of the champion
      :type name: str
      :returns: str -- ChampionKey
        """
        keys, champs = self.get_champions(keys=True)
        if name not in keys:
            raise Exception('Name not found')
        return champs[keys.index(name)]

    def get_champion_details(self, champ):
        """
        Returns a detailed look at the given champion including name, key, image, id and title.
      :param champ: champion name
      :type champ: str
      :returns: dict -- detailed champion info
        """
        if champ not in self.get_champions():
            raise KeyError('Champion not found')
        else:
            try:
                champions = shelve.open('champions')
                return champions[champ]
            finally:
                champions.close()

    def get_matchup(self, args):
        """
        Requests the 10 best matchups against a given champion with a given role from the champion.gg api
        and generates an image overview.
      :param args: request string coming from the discord server
      :type args: str
      :returns: str -- formatted response to be send to the discord server either containing the filename
                         or an error message
        """
        chmplst = self.get_champions()
        champion = ''
        lane = ''
        args = args.lower()
        for chmp in chmplst:
            test = chmp.lower()
            if args.replace(test, '') != args:
                champion = chmp
                lane = args.replace(test, '').strip()
                break
        if lane == '':
            return '**' + args + '** was not recognized.'
        try:
            position = self.positions[lane]
        except KeyError:
            return 'Role: **' + lane + '**, could not be found.'
        req = self.get_response('http://api.champion.gg/champion/' + champion + '/matchup?api_key=' + self.open_token)
        index = -1
        for i in range(len(req)):
            if req[i]['role'] == position:
                index = i
                break
        if index == -1:
            return 'No matchup information for: **' + champion + ' ' + position + '** could be found.'
        matchups = req[index]['matchups']
        matchups_sorted = sorted(matchups, key=lambda k: k['statScore'])
        name_im = list()
        for i in range(10):
            name = self.find_champion_name_by_key(matchups_sorted[i]['key'])
            image = self.get_image(name)
            name_im.append({'image': image, 'name': name})
        return create_image(champion, self.get_image(champion), position, matchups_sorted, name_im)

    def find_match(self, args):
        """
        Requests the riot api if there's an active game for a given summoner and generates a LolGame helper object to
        return a the details of the current game.
      :param args: request string coming from the discord server containing the summoner name and region
      :type args: str
      :returns: str -- formatted response to be send to the discord server being either the response from LolGame
                         or an error message
        """
        self.get_champions()
        name = ''
        region = args.split(' ')[0].lower()
        if region not in self.regions:
            region = ''
        if region == '':
            return '**' + args + '** was not recognized.'
        name = args.replace(region+' ', '').replace(' ', '%20')
        try:
            summid = self.get_response('https://' + region + '.api.pvp.net/api/lol/' + region +
                                       '/v1.4/summoner/by-name/' + name + '?api_key=' + self.riot_token)
        except urllib.error.HTTPError:
            return 'Summoner: **' + name + '** could not be found.'
        for x in summid:
            s_id = summid[x]['id']
        try:
            url = 'https://' + \
                  region + '.api.pvp.net/observer-mode/rest/consumer/getSpectatorGameInfo/' + \
                self.platforms[region] + '/' + str(s_id) + '?api_key='+self.riot_token
            match = self.get_response(url)
            game = LolGame(match, str(s_id), name, region, self)
            return game.get_formatted_string()
        except urllib.error.HTTPError:
            return 'Match for: ' + name.replace('%20', ' ') + ' on ' + region + ' could not be found.'

    def status(self, args):
        """
        Requests the riot api lol status information and returns which servers are up.
      :param args: empty, used so for dynamic method invocation
      :returns: str -- formatted response to be send to the discord server
        """
        info = ''
        for reg in self.regions:
            info += reg.upper() + ':\n'
            stat = self.get_response('http://status.leagueoflegends.com/shards/' + reg)
            info += '-Game: **' + stat['services'][0]['status'] + '**\n'
            info += '-Client: **' + stat['services'][3]['status'] + '**\n'
        info = info[:-1]
        return info

    def run_command(self, command, args):
        # try:
        return self.dispatch[command](args)
        # except KeyError:
        #    return self.dispatch['help']()


class LolGame:
    """
    Helper class for loading detailed information about an active game.
    """
    def __init__(self, response, owner_id, owner_name, region, league):
        """
        Helper class for loading detailed information about an active game.
      :param response: spectator info of match requested earlier from the riot api
      :type response: dict
      :param owner_id: summoner id of the person whom the match information is requested from
      :type owner_id: str
      :param owner_name: summoner name of the person whom the match information is requested from
      :type owner_name: str
      :param region: region match information is being requested for
      :type region: str
      :param league: league helper class reference
      :type league: League
        """
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.blue_side = []
        self.red_side = []
        self.owner_side = ''
        self.match = response
        self.region = region
        self.league = league
        self.league.get_champions()
        self.sums = []
        self.champs = {}
        self.entries = {}
        for part in self.match['participants']:
            name = part['summonerName']
            side = part['teamId']
            champ = part['championId']
            self.sums.append(str(part['summonerId']))
            try:
                self.champs[str(part['championId'])].append(str(part['summonerId']))
            except KeyError:
                self.champs[str(part['championId'])] = [str(part['summonerId'])]
            self.entries[str(part['summonerId'])] = {'name': name, 'rank': None, 'champ': None,
                                                'rate': 0, 'games': 0, 'side': side}
            if str(part['summonerId']) == str(owner_id):
                if side == 100:
                    self.owner_side = 'Blue'
                else:
                    self.owner_side = 'Red'
        self.get_champs_by_id()
        self.get_ranked_info()
        self.get_champions_stats()
        for entry in self.entries:
            side = self.entries[entry]['side']
            if side == 100:
                self.blue_side.append(self.entries[entry])
            else:
                self.red_side.append(self.entries[entry])

    def get_champs_by_id(self):
        """
        Requests the champion name from the static riot api server given an id
      :param champ_id: champion id
      :type champ_id: int
      :returns: str -- name of the champion
        """
        urls = []
        for champ in self.champs.keys():
            urls.append('https://global.api.pvp.net/api/lol/static-data/' + self.region +
                        '/v1.2/champion/' + str(champ) + '?api_key=' + self.league.riot_token)
        rs = (grequests.get(u) for u in urls)
        names = [json.loads(response.content.decode('utf-8')) for response in grequests.map(rs)]
        for name in names:
            for summ in self.champs[str(name['id'])]:
                self.entries[str(summ)]['champ'] = name['name']
        return True

    def get_formatted_string(self):
        """
        Formats all the requested information in a string which will be sent to the discord server.
      :returns: str -- formatted response to be send to the discord server
        """
        line1 = 'You got this! You can find **' + self.owner_name.replace('%20', ' ') + '** on __' + self.owner_side + \
                '__ side. \n\n'
        blue_side = '__Blue side:__\n'
        for pers in self.blue_side:
            rank = pers['rank'] if pers['rank'] else 'Unranked'
            blue_side += '**' + pers['name'] + '** - ' + rank + ' - **' + pers['champ'] + '**, __' + \
                         str(pers['rate']) + '%__ win rate over __' + str(pers['games']) + 'games__\n'
        red_side = '\n__Red side:__'
        for pers in self.red_side:
            rank = pers['rank'] if pers['rank'] else 'Unranked'
            red_side += '\n**' + pers['name'] + '** - ' + rank + ' - **' + pers['champ'] + '**, __' + \
                        str(pers['rate']) + '%__ win rate over __' + str(pers['games']) + 'games__'
        return line1 + blue_side + red_side

    def get_ranked_info(self):
        """
        Requests the riot api server the tier and division of a given summoner.
      :param summ_id: summoner id
      :type summ_id: int
      :returns: str -- formatted to contain the tier and division of the summoner
        """
        urls = ['https://' + self.region + '.api.pvp.net/api/lol/' + self.region + '/v2.5/league/by-summoner/' +
                str(self.sums).replace(' ', '').replace(']', '').replace('[', '').replace('\'', '') +
                '?api_key=' + self.league.riot_token]
        rs = (grequests.get(u) for u in urls)
        info = [json.loads(response.content.decode('utf-8')) for response in grequests.map(rs)]
        for inf in info:
            for summ_id in inf.keys():
                leagues = inf[summ_id]
                sum_div = list(filter(lambda summ: summ['playerOrTeamId'] == str(summ_id),
                                      leagues[0]['entries']))[0]
                division = sum_div['division']
                tier = (leagues[0])['tier'].lower().capitalize()
                self.entries[str(summ_id)]['rank'] = tier + ' ' + division

    def get_champions_stats(self):
        """
        Requests the ranked stats with all champions for a given summoner to the riot server.
      :param summ_id: summoner id
      :type summ_id: int
      :param region: region of the summoner
      :type region: str
      :returns: dict -- the json response mapped to a dict containing stats for all champions played in ranked S2016
        """
        urls = []
        for summ in self.sums:
            urls.append('https://' + self.region +
                        '.api.pvp.net/api/lol/' + self.region +
                        '/v1.3/stats/by-summoner/' + str(summ) +
                        '/ranked?season=SEASON2016&api_key=' + self.league.riot_token)
        rs = (grequests.get(u) for u in urls)
        info = [json.loads(response.content.decode('utf-8')) for response in grequests.map(rs)]
        for stats in info:
            try:
                x = stats['status']
                champ_stat = None
            except KeyError:
                summid = str(stats['summonerId'])
                champ = None
                for cham in self.champs.keys():
                    if champ:
                        break
                    for x in self.champs[cham]:
                        if x == summid:
                            champ = cham
                champ_stat = list(filter(lambda champion: str(champion['id']) == str(champ), stats['champions']))
            # Look for ranked stats for the champion used in the current game.
            if not champ_stat:
                win_rate = 0
                games = 0
            else:
                wins = champ_stat[0]['stats']['totalSessionsWon']
                losses = champ_stat[0]['stats']['totalSessionsLost']
                games = wins + losses
                win_rate = round((wins / games) * 100, 2)
            self.entries[summid]['rate'] = win_rate
            self.entries[summid]['games'] = games
        return True
