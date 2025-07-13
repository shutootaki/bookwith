from enum import Enum


class PodcastLanguage(str, Enum):
    EN_US = "en-US"
    JA_JP = "ja-JP"
    CMN_CN = "cmn-CN"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_
