import re

hiragana_pattern = re.compile("[\u3041-\u3096]")
katakana_pattern = re.compile("[\u30A0-\u30FF]")
kanji_pattern = re.compile("[\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A]")
punctuation_pattern = re.compile("[\uFF5F-\uFF9F]")


def is_hiragana(c: str) -> bool:
    return not not hiragana_pattern.fullmatch(c)


def is_katakana(c: str) -> bool:
    # FIXME: is this the right place to deal with the dot?
    return katakana_pattern.fullmatch(c) is not None and c != '・'


def is_kana(c: str) -> bool:
    return is_hiragana(c) or is_katakana(c)


def is_kanji(c: str) -> bool:
    return c == "々" or not not kanji_pattern.fullmatch(c)


def is_punctuation_or_half_width_katakana(c: str) -> bool:
    return not not punctuation_pattern.fullmatch(c)


def is_japanese(s: str) -> bool:
    return any(is_kana(c) or is_kanji(c) or is_punctuation_or_half_width_katakana(c) for c in s)
