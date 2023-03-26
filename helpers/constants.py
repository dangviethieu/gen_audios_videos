import enum


CONFIG_AUDIOS_FILE = 'config_audio_sub.json'
CONFIG_VIDEOS_FILE = 'config_video_sub.json'

VERSION = "1.0.1"
TOOL_NAME = "FFmpeg Concat Tool"

NEED_LOGIN = False
USERNAME = 'hieudv2'
PASSWORD = '123'

EXT_IMG = ['png', 'jpg', 'gif', 'jpeg']

class ConcatOptions(enum.Enum):
    CONCAT_DEMUXER = "concat demuxer (same codecs)"
    CONCAT_FILTER = "concat filter (diff codecs)"
