import PySimpleGUI as sg
from helpers.constants import TOOL_NAME, VERSION
from views.audio_view import AudioView
from views.video_view import VideoView


class MainView:
    def __init__(self) -> None:
        self.window = None
        self.audio_view = AudioView()
        self.video_view = VideoView()
        self.create_ui()

    def create_ui(self):
        sg.theme('SystemDefault')
        layout = [
            [sg.TabGroup([[
                sg.Tab('audios', layout=self.audio_view.create_layout()),
                sg.Tab('videos', layout=self.video_view.create_layout()),
            ]])]
        ]
        self.window = sg.Window(f'{TOOL_NAME} v{VERSION}', layout, icon=sg.EMOJI_BASE64_PONDER, finalize=True)
        # set window for gui
        self.audio_view.set_window(self.window)
        self.video_view.set_window(self.window)
        while True:
            event, values = self.window.read(10)
            if event is None or event == sg.WIN_CLOSED:
                break
            self.audio_view.handle_events(event, values)
            self.video_view.handle_events(event, values)
