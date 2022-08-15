from japanese import is_kana, is_kanji, is_japanese


def is_empty(s: str) -> bool:
    return s is None or s == '' or s.isspace()


def auto_lj(s: str) -> str:
    if is_japanese(s):
        return "{{lj|" + s + "}}"
    return s
