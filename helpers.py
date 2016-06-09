"""
Helper functions
"""
import re
import youtube_dl


def youtube_url_validation(url):
    """
    Checks if the url is a valid youtube link.
    :param url: url to check against
    :type url: str
    :returns: None if it is not valid or the video-id if it is.
    """
    p = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.search(p, url)
    if youtube_regex_match:
        return youtube_regex_match.group(6)
    return youtube_regex_match


def get_vid_title(url):
    """
    Requests the title of a youtube video given a valid url.
    :param url: url to get title from
    :type url: str
    :returns: title of the video
    """
    with youtube_dl.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_title = info_dict.get('title', None)
    return video_title
