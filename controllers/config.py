import json
import os
from pydantic import BaseModel
from helpers.constants import CONFIG_AUDIOS_FILE, CONFIG_VIDEOS_FILE, ConcatOptions


class Claim(BaseModel):
    path: str
    background: str = ''
    pos: int

class Config(BaseModel):
    input_folder: str
    input_title: str
    output_folder: str
    with_gpu: bool = False
    files_output_number: int = 1
    files_input_number: int = 100
    threads: int = 1
    concat_option: str = ConcatOptions.CONCAT_DEMUXER.value
    claims: list[Claim] = []


class ConfigSetup:
    def __init__(self) -> None:
        self.config_audios_file = "configs/" + CONFIG_AUDIOS_FILE
        self.config_videos_file = "configs/" + CONFIG_VIDEOS_FILE
        if not os.path.exists('configs'):
            os.mkdir('configs')
        self.load_audios_config()
        self.load_videos_config()

    def store_audio_sub_config(self, config: Config):
        self.config_audios = config
        with open(self.config_audios_file, "w") as outfile:
            json.dump(self.config_audios.dict(), outfile)
            
    def store_video_sub_config(self, config: Config):
        self.config_videos = config
        with open(self.config_videos_file, "w") as outfile:
            json.dump(self.config_videos.dict(), outfile)

    def load_audios_config(self):
        try:
            with open(self.config_audios_file, "r") as infile:
                self.config_audios = Config(**json.load(infile))
        except:
            self.config_audios = Config(
                input_folder='',
                input_title='',
                output_folder='',
                with_gpu=False,
                files_output_number=1,
                files_input_number=100,
                threads=1,
                concat_option=ConcatOptions.CONCAT_DEMUXER.value,
                claims=[],
            )
            
    def load_videos_config(self):
        try:
            with open(self.config_videos_file, "r") as infile:
                self.config_videos = Config(**json.load(infile))
        except:
            self.config_videos = Config(
                input_folder='',
                input_title='',
                output_folder='',
                with_gpu=False,
                files_output_number=1,
                files_input_number=100,
                threads=1,
                concat_option=ConcatOptions.CONCAT_DEMUXER.value,
                claims=[],
            )
