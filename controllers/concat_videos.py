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


class ConcatVideoHandler(BaseHandler):
    def __init__(self) -> None:
        super().__init__(service='concat_videos')
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
        # # get files from input title folder
        # files_title_path = glob.glob(os.path.join(config.input_title, "*.txt"))
        # if not files_title_path:
        #     self.logs.put(f"No files in input title folder")
        #     self.tasks_done.put(1)
        #     return
        # files_title = []
        # for file_title_path in files_title_path:
        #     files_title.extend(open(file_title_path, encoding='utf-8').read().splitlines())
        
        # self.custom_log(f'Start concat each {config.files_input_number} files in total {len(files)} files in folder {config.input_folder}...')
        # tasks_to_accomplish = Queue()
        # split_point = int(len(files) / config.threads)
        # split_point = split_point if split_point > config.files_input_number else config.files_input_number
        # for index in range(config.threads):
        #     if index != config.threads - 1:
        #         tasks_to_accomplish.put((index, config ,files[split_point*index:split_point*(index+1)], files_title), block=True, timeout=5)
        #     else:
        #         tasks_to_accomplish.put((index, config, files[split_point*index:], files_title), block=True, timeout=5)
        # for _ in range(config.threads):
        #     p = ConcatTask(tasks_to_accomplish, self.logs, self.tasks_done)
        #     self.processes.append(p)
        #     p.start()

    def stop(self):
        self.custom_log('Stop concat video task')
        for process in self.processes:
            process.terminate()
        self.custom_log('----------------------------------------------------------------')
            

class ConcatTask(Process):
    def __init__(self, tasks_to_accomplish: Queue, logs: Queue, tasks_done: Queue) -> None:
        Process.__init__(self)
        self.tasks_to_accomplish = tasks_to_accomplish
        self.logs = logs
        self.tasks_done = tasks_done
        
    def create_video_from_audio_and_image(self, audio_file: str, image_file: str, output_file: str) -> bool:
        self._logger.info(f"Create video from audio and image: {audio_file} - {image_file} - {output_file}")
        cmd = f'ffmpeg -y -loop 1 -i "{image_file}" -i "{audio_file}" -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest "{output_file}"'
        response = call_ffmpeg(cmd)
        if response.status:
            self._logger.info(f"Create video from audio and image successfully")
            return True
        else:
            self._logger.error(f"Create video from audio and image failed: {response.message}")
            return False
        
    def create_video_from_audio_and_videos(self, audio_file: str, video_files: list[str], output_file: str) -> bool:
        self._logger.info(f"Create video from audio: {audio_file} - {output_file}")
        # get audio length
        audio_length = get_length(audio_file)
        self._logger.info(f"Audio length: {audio_length}")
        # loop video with audio length
        video_file = random.choice(video_files)
        video_file_ext = video_file.split('.')[-1]
        output_file_tmp = output_file.replace(f'.{video_file_ext}', f'_tmp.{video_file_ext}')
        cmd = f'ffmpeg -y -stream_loop -1 -i "{video_file}" -t {audio_length} {output_file_tmp}'
        response = call_ffmpeg(cmd)
        if response.status:
            self._logger.info(f"Create video successfully")
            # replace audio
            cmd = f'ffmpeg -y -i "{output_file_tmp}" -i "{audio_file}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{output_file}"'
            response = call_ffmpeg(cmd)
            if response.status:
                self._logger.info(f"Replace audio successfully")
                os.remove(output_file_tmp)
                return True
            else:
                self._logger.error(f"Replace audio failed: {response.message}")
                return False
        else:
            self._logger.error(f"Create video from audio failed: {response.message}")
            return False
    
    def run(self):
        self._logger = setup_custom_logger('concat video task')
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
                videos_created_from_claim = []
                for title in titles:
                    try:
                        # init params
                        title_video = title + "." + files[0].split('.')[-1]
                        title_video_cut = title + "_cut." + files[0].split('.')[-1]
                        title_description = title + ".txt"
                        description = ""
                        current_length = 0
                        files_input = deepcopy(files)
                        file_index = 0
                        files_output = []
                        # start concat
                        custom_log(f'#Thread {index+1}: concat {title_video} ...')
                        # option 1: concat demuxer
                        if config.concat_option == ConcatOptions.CONCAT_DEMUXER.value:
                            with open(f"configs/{title_video}.txt", "w", encoding='utf-8') as f:
                                while file_index < config.files_input_number:
                                    for claim in config.claims:
                                        if file_index == claim.pos:
                                            # create video from audio and image
                                            custom_log(f'#Thread {index+1}: ---> create video from audio and image')
                                            video_created_from_claim_path = os.path.abspath(f"configs/{Path(claim.path).stem}.{file.split('.')[-1]}")
                                            if not os.path.exists(video_created_from_claim_path):
                                                if self.create_video_from_audio_and_videos(claim.path, files, video_created_from_claim_path):
                                                    custom_log(f'#Thread {index+1}: ---> create video from audio and image successfully')
                                                    f.write(f"file '{video_created_from_claim_path}'\n")
                                                    # get length of claim file
                                                    claim_length = get_length(video_created_from_claim_path)
                                                    # add claim file into description file
                                                    description += f"{Path(video_created_from_claim_path).stem} - {time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                                                    current_length += claim_length
                                                    videos_created_from_claim.append(video_created_from_claim_path)
                                                else:
                                                    custom_log(f'#Thread {index+1}: ---> create video from audio and image failed!')
                                            else:
                                                f.write(f"file '{video_created_from_claim_path}'\n")
                                                # get length of claim file
                                                claim_length = get_length(video_created_from_claim_path)
                                                # add claim file into description file
                                                description += f"{Path(video_created_from_claim_path).stem} - {time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                                                current_length += claim_length
                                                videos_created_from_claim.append(video_created_from_claim_path)
                                            break
                                    while files_input:
                                        file = random.choice(files_input)
                                        if file not in files_output:
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
                            # cmd = f"ffmpeg -y -f concat -segment_time_metadata 1 -safe 0 -i \"configs/{title_video}.txt\" -vf select=concatdec_select -af aselect=concatdec_select,aresample=async=1 \"{config.output_folder}/{title_video}\""
                            cmd = f"ffmpeg -y -f concat -safe 0 -i \"configs/{title_video}.txt\" -vsync 1 -async -1 -c copy \"{config.output_folder}/{title_video_cut}\""
                            response = call_ffmpeg(cmd)
                            # remove txt file
                            os.remove(f"configs/{title_video}.txt")
                            if response.status:
                                # write description file
                                with open(f"{config.output_folder}/{title_description}", "w", encoding='utf-8') as f:
                                    f.write(description)
                                # check length of video
                                length_video_cut = get_length(f"{config.output_folder}/{title_video_cut}")
                                if length_video_cut > current_length + 10:
                                    cmd = f"ffmpeg -y -i \"{config.output_folder}/{title_video_cut}\" -ss 00:00:00 -t {time.strftime('%H:%M:%S', time.gmtime(current_length))} \"{config.output_folder}/{title_video}\""
                                    call_ffmpeg(cmd)
                                    try:
                                        os.remove(f"{config.output_folder}/{title_video_cut}")
                                    except:
                                        pass
                                custom_log(f'#Thread {index+1}: concat {title_video} successfully!')
                            else:
                                os.remove(f"{config.output_folder}/{title_video}")
                                custom_log(f'#Thread {index+1}: concat {title_video} failed!')
                                self._logger.error(f"Error: {response.message}")
                        # # option 2: concat filter
                        # else:
                        #     no_files = len(files_)
                        #     cmd = "ffmpeg -y "
                        #     for file_index, file in enumerate(files_):
                        #         for claim in config.claims:
                        #             if file_index == claim.pos:
                        #                 # create video from audio and image
                        #                 video_created_from_claim_path = os.path.abspath(f"configs/{Path(claim.path).stem}.{file.split('.')[-1]}")
                        #                 if not os.path.exists(video_created_from_claim_path):
                        #                     if self.create_video_from_audio_and_image(claim.path, claim.background, video_created_from_claim_path):
                        #                         cmd += "-i \"" + video_created_from_claim_path + "\" "
                        #                         no_files += 1
                        #                         # get length of claim file
                        #                         claim_length = get_length(video_created_from_claim_path)
                        #                         # add claim file into description file
                        #                         description += f"{Path(video_created_from_claim_path).stem} - {time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                        #                         current_length += claim_length
                        #                         videos_created_from_claim.append(video_created_from_claim_path)
                        #                     else:
                        #                         custom_log(f'#Thread {index+1}: ---> create video from audio and image failed!')
                        #                 break
                        #         cmd += "-i \"" + file + "\" "
                        #         # get length of claim file
                        #         file_length = get_length(file)
                        #         # add claim file into description file
                        #         description += f"{Path(file).stem} - {time.strftime('%H:%M:%S', time.gmtime(current_length))}\n"
                        #         current_length += file_length
                        #     cmd += "-filter_complex \""
                        #     for file_index in range(len(files_)):
                        #         cmd += "[" + str(file_index) + ":v][" + str(file_index) + ":a]"
                        #     cmd += f" concat=n={no_files}:v=1:a=1 [v][a]\" -map [v] -map [a] \"{config.output_folder}/{title_video}\""
                        #     response = call_ffmpeg(cmd)
                        #     if response.status:
                        #         # write description file
                        #         with open(f"{config.output_folder}/{title_description}", "w", encoding='utf-8') as f:
                        #             f.write(description)
                        #         custom_log(f'#Thread {index+1}: concat {title_video} successfully!')
                        #     else:
                        #         os.remove(f"{config.output_folder}/{title_video}")
                        #         custom_log(f'#Thread {index+1}: concat {title_video} failed!')
                        #         self._logger.error(f"Error: {response.message}")
                    except Exception as e:
                        custom_log(f'#Thread {index+1}: concat {title_video} failed!')
                        _, _, exc_tb = sys.exc_info()
                        custom_log(f'#Thread {index+1}: line: {exc_tb.tb_lineno}, error: {e}')
                # # remove claim files
                # for video_created_from_claim in videos_created_from_claim:
                #     try:
                #         os.remove(video_created_from_claim)
                #     except:
                #         pass
                self.tasks_done.put(1)
                custom_log(f'#Thread {index+1}: Done')
                return