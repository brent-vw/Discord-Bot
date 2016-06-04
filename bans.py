from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont

WH = (830, 337)
WH_subimage = (204, 75)
mainwidth = 80
basewidth = 73
font_path = 'OpenSans-Regular.ttf'
base_url = 'http://ddragon.leagueoflegends.com/cdn/6.11.1/img/champion/'
widths_o = [5, 210, 415, 620, 5, 210, 415, 620, 5, 210]
heights_o = [107, 107, 107, 107, 183, 183, 183, 183, 259, 259]


def draw_top(hyper, img, name, lane):
    url = requests.get(hyper)
    portrait = Image.open(BytesIO(url.content))
    wpercent = (basewidth / float(portrait.size[0]))
    hsize = int((float(portrait.size[1]) * float(wpercent)))
    portrait = portrait.resize((basewidth, hsize), Image.ANTIALIAS)

    img.paste(portrait, (20, 1))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, 25)
    font2 = ImageFont.truetype(font_path, 20)
    draw.text((105, 10), name, font=font, fill='#AAABAE')
    draw.text((105, 35), lane, font=font2, fill='#AAABAE')
    return img


def draw_champ_window(link, WH, i, name, rate, games):
    url = requests.get(link)
    portrait = Image.open(BytesIO(url.content))
    wpercent = (basewidth / float(portrait.size[0]))
    hsize = int((float(portrait.size[1]) * float(wpercent)))
    portrait = portrait.resize((basewidth, hsize), Image.ANTIALIAS)

    background = Image.new("RGB", WH, "#2E3136")
    background.paste(portrait, (1, 1))
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, 20)
    font2 = ImageFont.truetype(font_path, 10)
    font3 = ImageFont.truetype(font_path, 15)
    draw.text((80, 2), name, font=font, fill='#AAABAE')
    draw.text((5, 1), str(i), font=font2, fill='#AAABAE')
    draw.text((80, 30), 'Winrate: ' + str(rate) + '%', font=font3, fill='#AAABAE')
    draw.text((80, 50), 'Games: ' + str(games), font=font3, fill='#AAABAE')
    return background


def create_image(mainchamp, favi, lane, counters, name_im):
    img = Image.new("RGB", WH, "#36393E")
    draw_top(base_url + favi, img, mainchamp, lane)
    for i in range(10):
        counter = counters[i]
        offset = (widths_o[i], heights_o[i])
        img.paste(draw_champ_window(base_url + name_im[i]['image'], WH_subimage, str(i + 1), name_im[i]['name'],
                                    counter['winRate'], counter['games']), offset)
    img.save('img.png', 'PNG')
    return 'img.png'
