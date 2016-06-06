import urllib
import json
import re
import youtube_dl


def youtube_url_validation(url):
    p = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.search(p, url)
    if youtube_regex_match:
        return youtube_regex_match.group(6)
    return youtube_regex_match


def get_vid_title(url):
    with youtube_dl.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_title = info_dict.get('title', None)
    return video_title
