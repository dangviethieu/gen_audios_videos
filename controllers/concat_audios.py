from controllers import BaseHandler, setup_custom_logger
from controllers.config import Config, ConcatOptions
from helpers.util import call_ffmpeg, get_length
from typing import List
from multiprocessing import Process, Queue
import glob
import os
import sys
import time
import random
from pathlib import Path
from copy import deepcopy


class ConcatAudioHandler(BaseHandler):
    def __init__(self) -> None:
        super().__init__(service='concat_audios')
        self.processes: List[Process] = []
        self.logs = Queue()
        self.tasks_done = Queue()
        self.custom_log = lambda x: (self.logs.put(x), self._logger.info(x))
        
    def start(self, config: Config) -> None:
        self.custom_log('----------------------------------------------------------------')
        if not config.input_folder or not config.input_title or not config.output_folder:
            self.logs.put(f"No input folder or input title or output folder")
            self.tasks_done.put(1)
            return
        # get files from input folder
        files = glob.glob(os.path.join(config.input_folder, "*.*"))
        random.shuffle(files)
        # files.sort(key=lambda x:[int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
        if not files:
            self.logs.put(f"No files in input folder")
            self.tasks_done.put(1)
            return
        # get files from input title folder
        files_title_path = glob.glob(os.path.join(config.input_title, "*.txt"))
        if not files_title_path:
            self.logs.put(f"No files in input title folder")
            self.tasks_done.put(1)
            return
        files_title = []
        for file_title_path in files_title_path:
            files_title.extend(open(file_title_path, encoding='utf-8').read().splitlines())
        titles_output = []
        for _ in range(config.files_output_number):
            while files_title:
                title = random.choice(files_title)
                if title not in titles_output:
                    titles_output.append(title)
                    files_title.remove(title)
                    break
            else:
                self.logs.put(f"No more title to use")
                self.tasks_done.put(1)
                return
        
        self.custom_log(f'Start generate {config.files_output_number} files ...')
        tasks_to_accomplish = Queue()
        split_point = int(len(titles_output) / config.threads)
        for index in range(config.threads):
            if index != config.threads - 1:
                tasks_to_accomplish.put((index, config ,files, titles_output[split_point*index:split_point*(index+1)]), block=True, timeout=5)
            else:
                tasks_to_accomplish.put((index, config, files, titles_output[split_point*index:]), block=True, timeout=5)
        for _ in range(config.threads):
            p = ConcatTask(tasks_to_accomplish, self.logs, self.tasks_done)
            self.processes.append(p)
            p.start()

    def stop(self):
        self.custom_log('Stop concat audio task')
        for process in self.processes:
            process.terminate()
        self.custom_log('----------------------------------------------------------------')
            

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
                if not self.tasks_to_accomplish.empty():
                    index, config, files, titles = self.tasks_to_accomplish.get(block=True, timeout=5)
                    time.sleep(0.1)
                    config: Config = config
            except Exception as e:
                _, _, exc_tb = sys.exc_info()
                self._logger.error(f"Error: {e} at line {exc_tb.tb_lineno}")
                break
            else:
                for title in titles:
                    try:
                        # init params
                        title_audio = title + "." + files[0].split('.')[-1]
                        title_description = title + ".txt"
                        description = ""
                        current_length = 0
                        files_input = deepcopy(files)
                        files_output = []
                        file_index = 0
                        # start concat
                        custom_log(f'#Thread {index+1}: concat {title_audio} ...')
                        # option 1: concat demuxer
                        if config.concat_option == ConcatOptions.CONCAT_DEMUXER.value:
                            with open(f"configs/{title_audio}.txt", "w", encoding='utf-8') as f:
                                while file_index < config.files_input_number:
                                    for claim in config.claims:
                                        if index_file == claim.pos:
                                            # check file format
                                            if claim.path.split('.')[-1] == file.split('.')[-1]:
                                                f.write(f"file '{claim.path}'\n")
                                                # get length of claim file
                                                claim_length = get_length(claim.path)
                                                # add claim file into description file
                                                description += f"{Path(claim.path).stem} - {time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                                                current_length += claim_length
                                            else:
                                                custom_log(f'#Thread {index+1}: ---> need claim file {claim.pos} format same with input files format!')
                                            break
                                    while files_input:
                                        file = random.choice(files_input)
                                        if file not in files_output:
                                            files_input.remove(file)
                                            f.write(f"file '{file}'\n")
                                            # get length of claim file
                                            file_length = get_length(file)
                                            # add claim file into description file
                                            description += f"{Path(file).stem} - {time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                                            current_length += file_length
                                            files_output.append(file)
                                            file_index += 1
                                            break
                                    else:
                                        custom_log(f'#Thread {index+1}: ---> no more file to use!')
                                        break
                            cmd = f"ffmpeg -y -loglevel quiet -f concat -safe 0 -i \"configs/{title_audio}.txt\" -c copy \"{config.output_folder}/{title_audio}\""
                            response = call_ffmpeg(cmd)
                            if response.status:
                                os.remove(f"configs/{title_audio}.txt")
                                # write description file
                                with open(f"{config.output_folder}/{title_description}", "w", encoding='utf-8') as f:
                                    f.write(description)
                                custom_log(f'#Thread {index+1}: concat {title_audio} successfully!')
                            else:
                                os.remove(f"configs/{title_audio}.txt")
                                os.remove(f"{config.output_folder}/{title_audio}")
                                custom_log(f'#Thread {index+1}: concat {title_audio} failed!')
                                self._logger.error(f"Error: {response.message}")
                        # option 2: concat filter
                        else:
                            no_files = config.files_input_number
                            cmd = "ffmpeg -y "
                            while file_index < config.files_input_number:
                                for claim in config.claims:
                                    if index_file == claim.pos:
                                        cmd += "-i \"" + claim.path + "\" "
                                        no_files += 1
                                        # get length of claim file
                                        claim_length = get_length(claim.path)
                                        # add claim file into description file
                                        description += f"{Path(claim.path).stem} - {time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                                        current_length += claim_length
                                        break
                                while files_input:
                                    file = random.choice(files_input)
                                    if file not in files_output:
                                        cmd += "-i \"" + file + "\" "
                                        # get length of claim file
                                        file_length = get_length(file)
                                        # add claim file into description file
                                        description += f"{Path(file).stem} -{time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                                        current_length += file_length
                                        file_index += 1
                                        break
                                else:
                                    custom_log(f'#Thread {index+1}: ---> no more file to use!')
                                    break
                            cmd += "-filter_complex \""
                            for index_file in range(no_files):
                                cmd += "[" + str(index_file) + ":a]"
                            cmd += f" concat=n={no_files}:v=0:a=1 [a]\" -map [a] \"{config.output_folder}/{title_audio}\""
                            response = call_ffmpeg(cmd)
                            if response.status:
                                # write description file
                                with open(f"{config.output_folder}/{title_description}", "w", encoding='utf-8') as f:
                                    f.write(description)
                                custom_log(f'#Thread {index+1}: concat {title_audio} successfully!')
                            else:
                                os.remove(f"{config.output_folder}/{title_audio}")
                                custom_log(f'#Thread {index+1}: concat {title_audio} failed!')
                                self._logger.error(f"Error: {response.message}")
                    except Exception as e:
                        custom_log(f'#Thread {index+1}: concat {title_audio} failed!')
                        _, _, exc_tb = sys.exc_info()
                        custom_log(f'#Thread {index+1}: line: {exc_tb.tb_lineno}, error: {e}')
                self.tasks_done.put(1)
                custom_log(f'#Thread {index+1}: Done')
                return