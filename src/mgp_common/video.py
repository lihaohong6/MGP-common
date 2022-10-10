import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_TIME = datetime.now() + timedelta(days=1000)


class VideoSite(Enum):
    NICO_NICO = "niconico"
    BILIBILI = "bilibili"
    YOUTUBE = "YouTube"


@dataclass
class Video:
    site: VideoSite = None
    identifier: str = None
    url: str = None
    views: int = 0
    uploaded: datetime = DEFAULT_TIME
    thumb_url: str = None
    canonical = True

    def __str__(self) -> str:
        return f"VideoSite: {self.site}\n" \
               f"Id: {self.identifier}\n" \
               f"Views: {self.views}\n" \
               f"Uploaded: {self.uploaded}\n" \
               f"Thumb: {self.thumb_url}\n\n"


table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
tr = {}
for index in range(58):
    tr[table[index]] = index
s = [11, 10, 3, 8, 4, 6]
xor = 177451812
add = 8728348608


def av_to_bv(av: str) -> str:
    x = int(av[2:])
    x = (x ^ xor) + add
    r = list('BV1  4 1 7  ')
    for i in range(6):
        r[s[i]] = table[x // 58 ** i % 58]
    return ''.join(r)


def str_to_date(date: str) -> Optional[datetime]:
    if 'T' in date:
        date = date[:date.find('T')]
    date = date.split("-")
    if len(date) != 3:
        return None
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    return datetime(year=year, month=month, day=day)


def get_nc_info(vid: str) -> Video:
    if vid.find("nicovideo") != -1:
        vid = vid[vid.rfind("/") + 1:]
    url = f"https://www.nicovideo.jp/watch/{vid}"
    result = requests.get(url).text
    soup = BeautifulSoup(result, "html.parser")
    date = DEFAULT_TIME
    views = 0
    for script in soup.find_all('script'):
        t: str = script.get_text()
        index_start = t.find("uploadDate")
        if index_start != -1:
            index_start += len("uploadDate") + 3
            date = t[index_start:index_start + 10]
            date = str_to_date(date)
        index_start = t.find("userInteractionCount")
        if index_start != -1:
            index_start += len("userInteractionCount") + 2
            index_end = t.find("}", index_start)
            views = int(t[index_start:index_end])
    thumb = soup.find("meta", {"name": "thumbnail"})['content']
    return Video(VideoSite.NICO_NICO, vid, url, views, date, thumb)


def get_bb_info(vid: str) -> Video:
    if vid.find("bilibili") != -1:
        vid = vid[vid.rfind("/") + 1:]
        if vid.find("?") != -1:
            vid = vid[:vid.find("?")]
    if "av" in vid:
        vid = av_to_bv(vid)
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={vid}"
    response = json.loads(requests.get(url).text)
    epoch_time = int(response['data']['pubdate'])
    date = datetime.fromtimestamp(epoch_time)
    # remove extra information to be in sync with YT and Nico
    date = datetime(year=date.year, month=date.month, day=date.day)
    pic = response['data']['pic']
    views = response['data']['stat']['view']
    return Video(VideoSite.BILIBILI, vid, url, views, date, pic)


def get_yt_info(vid: str) -> Video:
    if vid.find("youtube.") != -1:
        vid = vid[vid.find("=") + 1:]
    elif vid.find("youtu.be") != -1:
        vid = vid[vid.rfind("/") + 1:]
    url = 'https://www.youtube.com/watch?v=' + vid
    text = requests.get(url).text
    soup = BeautifulSoup(text, "html.parser")
    interaction = soup.select_one('meta[itemprop="interactionCount"][content]')
    views = int(interaction['content'])
    date = str_to_date(soup.select_one('meta[itemprop="datePublished"][content]')['content'])
    return Video(VideoSite.YOUTUBE, vid, url, views, date,
                 thumb_url="https://img.youtube.com/vi/{}/0.jpg".format(vid))


info_func = {
    VideoSite.NICO_NICO: get_nc_info,
    VideoSite.BILIBILI: get_bb_info,
    VideoSite.YOUTUBE: get_yt_info
}


def video_from_site(site: VideoSite, identifier: str, canonical: bool = True) -> Optional[Video]:
    try:
        v = info_func[site](identifier)
    except Exception as e:
        logging.info(e)
        return None
    if not v:
        return None
    v.canonical = canonical
    return v
