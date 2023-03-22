from controllers import BaseHandler, setup_custom_logger
from controllers.config import ConfigAudios, ConcatOptions
from helpers.util import random_line
from typing import List
from multiprocessing import Process, Queue
import glob
import queue
import os
import re
import sys
import subprocess
import time
import random


class ConcatHandler(BaseHandler):
    def __init__(self) -> None:
        super().__init__(service='concat_audios')
        self.processes: List[Process] = []
        self.logs = Queue()
        self.tasks_done = Queue()
        
    def start(self, config: ConfigAudios) -> None:
        custom_log = lambda x: (self.logs.put(x), self._logger.info(x))
        custom_log('----------------------------------------------------------------')
        if not config.input_audios_folder or not config.input_audio_title or not config.output_audio_folder:
            self.logs.put(f"No input folder or input title or output folder")
            self.tasks_done.put(1)
            return
        # get files from input folder
        files = glob.glob(os.path.join(config.input_audios_folder, "*.*"))
        random.shuffle(files)
        # files.sort(key=lambda x:[int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
        if not files:
            self.logs.put(f"No files in input folder")
            self.tasks_done.put(1)
            return
        # get files from input title folder
        files_title_path = glob.glob(os.path.join(config.input_audio_title, "*.txt"))
        if not files_title_path:
            self.logs.put(f"No files in input title folder")
            self.tasks_done.put(1)
            return
        files_title = []
        for file_title_path in files_title_path:
            files_title.extend(open(file_title_path).read().splitlines())
        
        custom_log(f'Start concat each {config.files_number} files in total {len(files)} files in folder {config.input_audios_folder}...')
        tasks_to_accomplish = Queue()
        split_point = int(len(files) / config.threads)
        split_point = split_point if split_point > config.files_number else config.files_number
        for index in range(config.threads):
            # get random title
            if not files_title:
                for file_title_path in files_title_path:
                    for file_title in open(file_title_path).read().splitlines():
                        files_title += str(random.choice(range(0, 100))) + file_title
            title = random.choice(files_title)
            files_title.remove(title)
            self._logger.info(f"Title: {title}")
            if index != config.threads - 1:
                tasks_to_accomplish.put((index, config ,files[split_point*index:split_point*(index+1)], title))
            else:
                tasks_to_accomplish.put((index, config, files[split_point*index:], title))
        for _ in range(config.threads):
            p = ConcatTask(tasks_to_accomplish, self.logs, self.tasks_done)
            self.processes.append(p)
            p.start()

    def stop(self):
        for process in self.processes:
            process.terminate()
            

class ConcatTask(Process):
    def __init__(self, tasks_to_accomplish: Queue, logs: Queue, tasks_done: Queue) -> None:
        Process.__init__(self)
        self.tasks_to_accomplish = tasks_to_accomplish
        self.logs = logs
        self.tasks_done = tasks_done
    
    def run(self):
        self._logger = setup_custom_logger('concat audio task')
        custom_log = lambda x: (self.logs.put(x), self._logger.info(x))
        while True:
            try:
                index, config, files, title = self.tasks_to_accomplish.get_nowait()
                title = title + "." + files[0].split('.')[-1]
                time.sleep(0.1)
                config: ConfigAudios = config
            except Exception as e:
                _, _, exc_tb = sys.exc_info()
                self._logger.error(f"Error: {e} at line {exc_tb.tb_lineno}")
                break
            else:
                files_splitted = [files[i:i + config.files_number] for i in range(0, len(files), config.files_number)]
                for files_ in files_splitted:
                    try:
                        custom_log(f'#Thread {index+1}: concat {title} ...')
                        # option 1: concat demuxer
                        if config.concat_option == ConcatOptions.CONCAT_DEMUXER.value:
                            with open(f"configs/{title}.txt", "w", encoding='utf-8') as f:
                                for index_file, file in enumerate(files_):
                                    for claim in config.claims:
                                        if index_file == claim.pos:
                                            # check file format
                                            if claim.path.split('.')[-1] == file.split('.')[-1]:
                                                f.write(f"file '{claim.path}'\n")
                                            else:
                                                custom_log(f'#Thread {index+1}: ---> need claim file {claim.pos} format same with input files format!')
                                            break
                                    f.write(f"file '{file}'\n")
                            cmd = f"ffmpeg -y -loglevel quiet -f concat -safe 0 -i \"configs/{title}.txt\" -c copy \"{config.output_audio_folder}/{title}\""
                            process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) 
                            for _ in process.stdout:
                                pass
                            os.remove(f"configs/{title}.txt")
                            custom_log(f'#Thread {index+1}: concat {title} successfully!')
                        # option 2: concat filter
                        else:
                            no_files = len(files_)
                            cmd = "ffmpeg -y "
                            for index_file, file in enumerate(files_):
                                for claim in config.claims:
                                    if index_file == claim.pos:
                                        cmd += "-i \"" + claim.path + "\" "
                                        no_files += 1
                                        break
                                cmd += "-i \"" + file + "\" "
                            cmd += "-filter_complex \""
                            for index_file in range(len(files_)):
                                cmd += "[" + str(index_file) + ":a]"
                            cmd += f" concat=n={no_files}:v=0:a=1 [a]\" -map [a] \"{config.output_audio_folder}/{title}\""
                            process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8') 
                            for _ in process.stdout:
                                pass
                            custom_log(f'#Thread {index+1}: concat {title} successfully!')
                    except Exception as e:
                        custom_log(f'#Thread {index+1}: concat {title} failed!')
                        _, _, exc_tb = sys.exc_info()
                        custom_log(f'#Thread {index+1}: line: {exc_tb.tb_lineno}, error: {e}')
                self.tasks_done.put(1)
                custom_log(f'#Thread {index+1}: Done')
                return