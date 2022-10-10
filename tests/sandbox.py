from datetime import datetime

from mgp_common.string_utils import auto_lj, is_empty
from mgp_common.video import VideoSite, get_nc_info, video_from_site
from mgp_common.vocadb import get_producer_songs, Song


def song_to_str(song: Song):
    import wikitextparser as wtp
    t = wtp.Template("{{Producer_Song}}")
    mapping = {
        VideoSite.NICO_NICO: "nnd_id",
        VideoSite.YOUTUBE: 'yt_id',
        VideoSite.BILIBILI: 'bb_id'
    }
    image_link = ""
    for video in song.videos:
        if video.site in mapping:
            t.set_arg(mapping[video.site], video.identifier if video.identifier else "")
            if video.site == VideoSite.NICO_NICO:
                image_link = video.thumb_url.strip()
    for k, v in mapping.items():
        if not t.has_arg(v):
            t.set_arg(v, "")
    creator_mapping = {
        'Composer': '作曲',
        'Lyrics': '填词',
        'Animator': '视频制作',
        'Animators': '视频制作',
        'Illustrator': '画师',
        'Vocalist': '演唱者',
    }
    for role_english, role_chinese in creator_mapping.items():
        creators = song.creators.get(role_english, [])
        t.set_arg(role_chinese, "、".join(auto_lj(c) for c in creators))
    t.set_arg("投稿日期", song.publish_date.strftime("%Y年%m月%d日"))
    song_title = auto_lj(song.name_ja)
    article_link = ""
    if "{{lj" in song_title:
        article_link = song.name_ja
    t.set_arg("条目", article_link)
    t.set_arg("标题", song_title)
    t.set_arg("image", image_link)
    t.name += "\n"
    for arg in t.arguments:
        arg.name = arg.name.strip() + " "
        arg.value = " " + arg.value.strip() + "\n"
    return str(t)


def create_song_list(producer_id: str, producer_name: str = ""):
    songs = get_producer_songs(producer_id, load_videos=True)
    songs = [s for s in songs if len(s.videos) > 0]
    for s in songs:
        if s.publish_date is None:
            s.publish_date = datetime.now()
    songs.sort(key=lambda s: s.publish_date)
    result = []
    for song in songs:
        song.creators['Composer'] = song.creators.get('Composer', [producer_name])
        song.creators['Lyrics'] = song.creators.get('Lyrics', [producer_name])
        result.append(song_to_str(song))
    print("\n\n".join(result))


create_song_list("2226", "芳田")
