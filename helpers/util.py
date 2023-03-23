import random
import subprocess


def random_line(filename):
    lines = open(filename, encoding='utf-8').read().splitlines()
    return random.choice(lines)

def get_length(filename: str) -> float:
    cmd = f'ffprobe -i "{filename}" -show_entries format=duration -v quiet -of csv="p=0"'
    process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
    length = 0
    for out in process.stdout:
        try:
            length = float(out.split("\n")[0])
        except:
            pass
    return length

def call_ffmpeg(cmd):
    # print(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8') 
    for _ in process.stdout:
        pass
        # print(_.replace("\n", ""))