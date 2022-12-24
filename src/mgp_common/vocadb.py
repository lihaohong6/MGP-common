import json
import pickle
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests

import mgp_common.video
from mgp_common.config import get_cache_path
from mgp_common.string_utils import is_empty
from mgp_common.video import Video, VideoSite, video_from_site


@dataclass
class Song:
    name_ja: str
    name_chs: str = None
    name_other: List[str] = field(default_factory=list)
    original: bool = True
    publish_date: datetime = datetime.now() + timedelta(days=1000)
    videos: List[Video] = field(default_factory=list)
    albums: List[str] = field(default_factory=list)
    creators: Dict[str, List[str]] = field(default_factory=dict)


def parse_videos(videos: list, load_videos: bool = True) -> List[Video]:
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


def parse_albums(albums: list) -> List[str]:
    return [a['defaultName'] for a in albums]


vocaloid_names = {
    '初音ミク': "初音未来",
    '鏡音リン': "镜音铃",
    '鏡音レン': "镜音连",
    '巡音ルカ': "巡音流歌",
    'カイト': "KAITO",
    'メイコ': "MEIKO",
    '音街ウナ': "音街鳗",
    '歌愛ユキ': "歌爱雪",
    '結月ゆかり': "结月缘",
    '神威がくぽ': "神威乐步",
    'ブイフラワ': "v flower",
    'イア': "IA",
    'マユ': "MAYU",
    'GUMI': "GUMI",
    'ふかせ': "Fukase",
    'ギャラ子': 'Galaco',
    '心華': "心华",
    "紲星あかり": "绁星灯",
    '重音テト': "重音Teto",
    '鳴花ヒメ': '鸣花姬',
    '鳴花ミコト': '鸣花尊',
    '시유': 'SeeU',
    'Eleanor Forte': '爱莲娜·芙缇',
    'KAFU': '可不',
    'SeKai': '星界'
}


def name_shorten(name: str) -> str:
    for n in vocaloid_names.keys():
        if n in name:
            return n
    return name


def split_names(regex: str = "[・/，, ]+", text: str = "") -> List[str]:
    return re.split(regex, text)


def parse_creators(artists: Optional[list], artist_string: Optional[str]) -> Dict[str, List[str]]:
    if artists is None:
        artists = []
    if is_empty(artist_string) or len(split_names(text=artist_string)) != 2:
        artist_string = "feat."
    mapping: Dict[str, List[str]] = {}
    for artist in artists:
        if 'artist' in artist:
            name = artist['artist']['name']
            if artist['artist']['artistType'] == 'Vocaloid':
                # shorten names like 初音ミク V4X
                name = name_shorten(name)
        else:
            name = artist['name']
        roles = artist['roles']
        if roles == 'Default':
            roles = artist['categories']
        if roles == 'Other':
            continue
        roles = split_names(text=roles)
        name = name.strip()
        for role in roles:
            role = role.strip()
            if role in mapping:
                mapping[role].append(name)
            else:
                mapping[role] = [name]
    feat_split = artist_string.split("feat.")
    if "Vocalist" not in mapping and len(feat_split) > 1:
        names = split_names(text=feat_split[1])
        mapping['Vocalist'] = [name_shorten(n.strip()) for n in names if not is_empty(n)]
    if "Producer" not in mapping:
        names = split_names(text=feat_split[0])
        mapping['Producer'] = [n.strip() for n in names if not is_empty(n)]
    return mapping


def get_song_by_id(song_id: str, load_videos: bool = True) -> Song:
    url = f"https://vocadb.net/api/songs/{song_id}/details"
    response = json.loads(requests.get(url).text)
    name_ja = response['song']['defaultName']
    additional_names = [n for n in re.split(", *", response['additionalNames'])
                        if not is_empty(n)]
    publish_date = mgp_common.video.str_to_date(response['song'].get('publishDate', ""))
    if publish_date is None:
        publish_date = datetime.now() + timedelta(days=1000)
    original = response['song']['songType'] == 'Original'
    videos = parse_videos(response['pvs'], load_videos)
    for v in videos:
        if v.uploaded is not None and v.uploaded < publish_date:
            publish_date = v.uploaded
    albums = parse_albums(response['albums'])
    creators = parse_creators(response['artists'], response['artistString'])
    return Song(name_ja=name_ja, name_other=additional_names,
                original=original, publish_date=publish_date,
                videos=videos, albums=albums, creators=creators)


def get_producer_songs(producer_id: str, load_videos: bool = False) -> List[Song]:
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
                result.append(get_song_by_id(item['id'], load_videos))
            if len(items) < max_results:
                break
            start += max_results
        pickle.dump(result, open(path, "wb"))
    result = pickle.load(open(path, "rb"))
    return result


def get_producer_albums(producer_id: str, only_main: bool = True, only_original: bool = True) -> List[str]:
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
            'artistParticipationStatus': 'OnlyMainAlbums' if only_main else 'Everything',
            'discType': 'Album' if only_original else 'Unknown'
        }).json()
        for album in response['items']:
            result.append(album['defaultName'])
        if len(response['items']) < max_results:
            break
        start += max_results
    result.reverse()
    return result
