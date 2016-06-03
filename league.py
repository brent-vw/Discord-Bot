import urllib

api_token = 'fb9d4030900b9ee6d8ba4ebf00f1a032'
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
    'supp': 'Support'
}


def get_response(url):
    content = urllib.request.urlopen(url)
    print(content)


dispatch = {}


def run_command(command, args):
    try:
        return True, dispatch[command](args)
    except KeyError:
        return False, ""
