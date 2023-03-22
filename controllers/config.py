import json
import os
from pydantic import BaseModel
from helpers.constants import CONFIG_AUDIOS_FILE, ConcatOptions


class Claim(BaseModel):
    path: str
    pos: int

class ConfigAudios(BaseModel):
    input_audios_folder: str
    input_audio_title: str
    output_audio_folder: str
    with_gpu: bool = False
    files_number: int = 100
    threads: int = 1
    concat_option: str = ConcatOptions.CONCAT_DEMUXER.value
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
                files_number=100,
                threads=1,
                concat_option=ConcatOptions.CONCAT_DEMUXER.value,
                claims=[
                    Claim(path='D:\dangviethieu\python\gen_audios_videos\test\claim\Ai4-Lazii-8845956.mp3', pos=0),
                    Claim(path='D:\dangviethieu\python\gen_audios_videos\test\claim\ChayTimAiprelude-Uyen-8502530.mp3', pos=1),
                    Claim(path='D:\dangviethieu\python\gen_audios_videos\test\claim\ChetTrongEm-ThinhSuy-8261960.mp3', pos=2),
                ],
            )
