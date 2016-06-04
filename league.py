import urllib
import json
import shelve
import time
from datetime import date, timedelta
from bans import create_image

with open('.apikeys') as keys:
    data = json.load(keys)
api_token = data['open_league_token']
riot_token = data['league_token']
header = {'User-Agent': 'Mozilla/5.0',
          'Accept': 'text/html,application/json'}
positions = {
    'top': 'Top',
    'mid': 'Middle',
    'middle': 'Middle',
    'jungle': 'Jungle',
    'jg': 'Jungle',
    'bot': 'ADC',
    'adc': 'ADC',
    'support': 'Support',
    'sup': 'Support',
    'supp': 'Support',
    'Top': 'Top',
    'Mid': 'Middle',
    'Middle': 'Middle',
    'Jungle': 'Jungle',
    'Adc': 'ADC',
    'Support': 'Support'
}
regions = ['euw', 'na', 'br', 'eune', 'kr', 'lan', 'las', 'oce', 'ru', 'tr']


class LolGame:
    def __init__(self, response, owner_id, owner_name):
        get_champions()
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.blue_side = []
        self.red_side = []
        self.owner_side = ''
        self.match = response
        for participant in self.match['participants']:
            summid = participant['summonerId']
            name = participant['summonerName']
            side = participant['teamId']
            champ = participant['championId']
            stats = get_champions_stats(summid)
            champ_stat = list(filter(lambda champion: champion['id'] == champ, stats['champions']))
            if not champ_stat:
                win_rate = 0
                games = 0
            else:
                wins = champ_stat[0]['stats']['totalSessionsWon']
                losses = champ_stat[0]['stats']['totalSessionsLost']
                games = wins + losses
                win_rate = round((wins / games) * 100, 2)
            champ_name = get_champ_by_id(champ)
            rank = get_ranked_info(summid)
            entry = {'name': name, 'rank': rank, 'champ': get_champ_by_id(champ), 'rate': str(win_rate),
                     'games': str(games)}
            if side == 100:
                self.blue_side.append(entry)
            else:
                self.red_side.append(entry)
            if str(summid) == str(owner_id):
                if side == 100:
                    self.owner_side = 'Blue'
                else:
                    self.owner_side = 'Red'
            time.sleep(2)

    def get_formated_string(self):
        line1 = 'You got this! You can find **' + self.owner_name.replace('%20',' ') + '** on __' + self.owner_side + '__ side. \n\n'
        blue_side = '__Blue side:__\n'
        for pers in self.blue_side:
            blue_side += '**' + pers['name'] + '** - ' + pers['rank'] + ' - **' + pers['champ'] + '**, __' + \
                         pers['rate'] + '%__ winrate over __' + pers['games'] + 'games__\n'
        red_side = '\n__Red side:__'
        for pers in self.red_side:
            red_side += '\n**' + pers['name'] + '** - ' + pers['rank'] + ' - **' + pers['champ'] + '**, __' + \
                        pers['rate'] + '%__ winrate over __' + pers['games'] + 'games__'
        return line1 + blue_side + red_side


def get_response(url):
    request = urllib.request.Request(url, headers=header)
    with urllib.request.urlopen(request) as f:
      response = f.read().decode('UTF-8')
    response_dict = json.JSONDecoder().decode(response)
    return response_dict


def get_champions_stats(summid):
    return get_response('https://euw.api.pvp.net/api/lol/euw/v1.3/stats/by-summoner/' + str(
        summid) + '/ranked?season=SEASON2016&api_key=' + riot_token)


def get_ranked_info(summid):
    leagues = get_response(
        'https://euw.api.pvp.net/api/lol/euw/v2.5/league/by-summoner/' + str(summid) + '?api_key=' + riot_token)
    sum_div = list(filter(lambda summ: summ['playerOrTeamId'] == str(summid), leagues[str(summid)][0]['entries']))[0]
    division = sum_div['division']
    tier = leagues[str(summid)][0]['tier'].lower().capitalize()
    return tier + ' ' + division


def get_champ_by_id(id):
    try:
        champs = shelve.open('champions')
        return champs[str(id)]
    finally:
        champs.close()


def format_list(list, init_statement):
    response = [init_statement]
    for i in range(len(list)):
        delim = '  '
        if i == 9:
            delim = ' '
        response.append(str(i + 1) + ':' + delim + list[i])
    return '\n'.join(response)


def get_bans(args):
    list = get_response('http://api.champion.gg/stats/champs/mostBanned?api_key='+api_token+'&limit=25')['data']
    message = 'Here\'s the list of the top 10 most common bans:\n'
    messages = []
    champs = []
    for x in list:
        champ = x['name']
        if champ not in champs:
            champs.append(champ)
            messages.append('**' + champ + '**')
        if len(champs) == 10:
            break
    return format_list(messages, message)


def get_roles(lane):
    try:
        position = positions[lane]
    except KeyError:
        return 'Role: **' + lane + '**, could not be found.'
    list = get_response('http://api.champion.gg/stats/role/' + position + '/bestperformance?api_key=' + api_token)[
        'data']
    message = 'Here\'s the top 10 of role: **' + position + '**'
    messages = []
    for x in list:
        champ = x['name']
        winrate = x['general']['winPercent']
        messages.append('**' + champ + '** with a ' + str(winrate) + '% winrate.')
    return format_list(messages, message)


def get_champions(keys=False):
    try:
        champions = shelve.open('champions')
        if 'date' not in champions:
            champions['date'] = date.today() - timedelta(days=2)
        if champions['date'] != date.today():
            champions.clear()
            champions['date'] = date.today()
            resp = get_response(
                'https://global.api.pvp.net/api/lol/static-data/euw/v1.2/champion?champData=image&api_key=' + riot_token)
            champions['list'] = []
            champions['keys'] = []
            for x in resp['data'].values():
                name = x['name']
                id = x['id']
                img = x['image']['full']
                title = x['title']
                key = x['key']
                tmp = champions['list']
                tmp.append(name)
                champions['list'] = tmp
                tmp2 = champions['keys']
                tmp2.append(key)
                champions['keys'] = tmp2
                champions[name] = {'name': name, 'id': id, 'img': img, 'title': title, 'key': key}
                champions[str(id)] = name
        if 'img' not in champions:
            champions['image'] = 'http://ddragon.leagueoflegends.com/cdn/6.11.1/img/champion/'
        if keys:
            ret = champions['keys']
            return ret, champions['list']
        return champions['list']
    finally:
        champions.close()


def get_image(champion):
    try:
        champions = shelve.open('champions')
        return champions[champion]['img']
    finally:
        champions.close()


def find_champion_name_by_key(name):
    keys, champs = get_champions(keys=True)
    if name not in keys:
        raise Exception('Name not found')
    return champs[keys.index(name)]


def get_champion_details(champ):
    if champ not in get_champions():
        raise KeyError('Champion not found')
    else:
        try:
            champions = shelve.open('champions')
            return champions[champ]
        finally:
            champions.close()


def get_matchup(args):
    chmplst = get_champions()
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
        position = positions[lane]
    except KeyError:
        return 'Role: **' + lane + '**, could not be found.'
    req = get_response('http://api.champion.gg/champion/' + champion + '/matchup?api_key=' + api_token)
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
        name = find_champion_name_by_key(matchups_sorted[i]['key'])
        image = get_image(name)
        name_im.append({'image': image, 'name': name})
    return create_image(champion, get_image(champion), position, matchups_sorted, name_im)


def find_match(args):
    region = ''
    name = ''
    for reg in regions:
        if args.replace(reg, '') != args:
            region = reg
            name = args.replace(reg, '').strip()
            break
    if region == '':
        return '**' + args + '** was not recognized.'
    name = name.replace(' ', '%20')
    summid = get_response(
        'https://' + region + '.api.pvp.net/api/lol/' + region + '/v1.4/summoner/by-name/' + name + '?api_key=' + riot_token)
    for x in summid:
        id = summid[x]['id']
    try:
        match = get_response(
            'https://' + region + '.api.pvp.net/observer-mode/rest/consumer/getSpectatorGameInfo/' + region.upper() + '1/' + str(
                id) + '?api_key=' + riot_token)
    except urllib.error.HTTPError:
        return 'Match for: ' + name.replace('%20', ' ') + ' on ' + region + ' could not be found.'
    game = LolGame(match, str(id), name)
    return game.get_formated_string()


def status(args):
    info = ''
    for reg in regions:
        info += reg.upper() + ':\n'
        stat = get_response('http://status.leagueoflegends.com/shards/' + reg)
        info += '-Game: **' + stat['services'][0]['status'] + '**\n'
        info += '-Client: **' + stat['services'][3]['status'] + '**\n'
    info = info[:-1]
    return info


def info():
    return 'Ganja plays lol too! Here are the comands she recognizes:\n\r' + \
           '**!lol** status\n  Get the LoL Game and Client server status for all regions\n' + \
           '**!lol** match region summoner-name\n Get match information for the __current__ match (might take a few seconds)\n' + \
           '**!lol** counters champ-name position\n Get the top 10 counters for a champion and position\n' + \
           '**!lol** bans\n Get the top 10 most common bans\n' + \
           '**!lol** best position\n Get the 10 best champions for a given position\n' + \
           '**!lol** help\n Display this message'


dispatch = {'status': status,
            'match': find_match,
            'counters': get_matchup,
            'bans': get_bans,
            'best': get_roles,
            'help': info}


def run_command(command, args):
    try:
        return dispatch[command](args)
    except KeyError:
        return dispatch['help']()
