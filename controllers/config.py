import json
import os
from pydantic import BaseModel
from helpers.constants import CONFIG_AUDIOS_FILE


class Claim(BaseModel):
    path: str
    pos: int

class ConfigAudios(BaseModel):
    input_audios_folder: str
    input_audio_title: str
    output_audio_folder: str
    with_gpu: bool = False
    threads: int = 1
    claims: list[Claim] = []


class ConfigSetup:
    def __init__(self) -> None:
        self.config_audios_file = "configs/" + CONFIG_AUDIOS_FILE
        if not os.path.exists('configs'):
            os.mkdir('configs')
        self.load_audios_config()

    def store_audio_sub_config(self, config: ConfigAudios):
        self.config_audios = config
        with open(self.config_audios_file, "w") as outfile:
            json.dump(self.config_audios.dict(), outfile)

    def load_audios_config(self):
        try:
            with open(self.config_audios_file, "r") as infile:
                self.config_audios = ConfigAudios(**json.load(infile))
        except:
            self.config_audios = ConfigAudios(
                input_audios_folder='',
                input_audio_title='',
                output_audio_folder='',
                with_gpu=False,
                threads=1,
                claims=[
                    Claim(path='D:\FreeLancer\Video\gen_audios_videos\views\audio_view.py', pos=0),
                    Claim(path='views\audio_view.py', pos=1),
                    Claim(path='views\main_view.py', pos=2),
                ],
            )
