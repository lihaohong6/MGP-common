import json
import pickle
import re
from dataclasses import dataclass, field
from datetime import datetime
from textwrap import indent

import requests

import video
from config import get_cache_path
from japanese import is_japanese
from string_utils import is_empty, auto_lj
from video import Video, VideoSite, video_from_site


@dataclass
class Song:
    name_ja: str
    name_other: list[str] = field(default_factory=list)
    original: bool = True
    publish_date: datetime = None
    videos: list[Video] = field(default_factory=list)
    albums: list[str] = field(default_factory=list)


def parse_videos(videos: list, load_videos: bool = True) -> list[Video]:
    service_to_site: dict = {
        'NicoNicoDouga': VideoSite.NICO_NICO,
        'Youtube': VideoSite.YOUTUBE
    }
    result = []
    for v in videos:
        service = v['service']
        if v['pvType'] == 'Original' and service in service_to_site.keys():
            url = v['url']
            if load_videos:
                video = video_from_site(service_to_site.pop(service), url)
            else:
                video = Video(site=service_to_site.pop(service), url=url)
            if video:
                result.append(video)
    return result


def parse_albums(albums: list) -> list[str]:
    return [a['defaultName'] for a in albums]


def get_song_by_id(song_id: str, load_videos: bool = True) -> Song:
    url = f"https://vocadb.net/api/songs/{song_id}/details"
    response = json.loads(requests.get(url).text)
    name_ja = response['song']['defaultName']
    additional_names = [n for n in re.split(", *", response['additionalNames'])
                        if not is_empty(n)]
    publish_date = video.str_to_date(response['song'].get('publishDate', ""))
    original = response['song']['songType'] == 'Original'
    videos = parse_videos(response['pvs'], load_videos)
    albums = parse_albums(response['albums'])
    return Song(name_ja=name_ja, name_other=additional_names,
                original=original, publish_date=publish_date,
                videos=videos, albums=albums)


def get_producer_songs(producer_id: str) -> list[Song]:
    path = get_cache_path().joinpath("producer_songs_" + producer_id + ".pickle")
    if not path.exists():
        start = 0
        max_results = 50
        result = []
        while True:
            url = "https://vocadb.net/api/songs"
            response = requests.get(url, params={
                'start': start,
                'query': "",
                'maxResults': max_results,
                'sort': 'PublishDate',
                'artistId[]': producer_id,
                'artistParticipationStatus': 'Everything'
            })
            items = response.json()['items']
            for item in items:
                result.append(get_song_by_id(item['id'], load_videos=False))
            if len(items) < max_results:
                break
            start += max_results
        pickle.dump(result, open(path, "wb"))
    result = pickle.load(open(path, "rb"))
    return result


def get_producer_albums(producer_id: str) -> list[str]:
    start = 0
    max_results = 50
    result = []
    while True:
        url = "https://vocadb.net/api/albums"
        response = requests.get(url, params={
            'start': start,
            'query': "",
            'maxResults': max_results,
            'sort': 'ReleaseDate',
            'artistId[]': producer_id,
            'artistParticipationStatus': 'Everything'
        }).json()
        for album in response['items']:
            result.append(album['defaultName'])
        if len(response['items']) < max_results:
            break
        start += max_results
    result.reverse()
    return result
