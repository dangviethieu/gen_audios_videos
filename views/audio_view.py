from .base import BaseView, sg
from controllers.config import ConfigSetup, Config, Claim
from controllers.concat_audios import ConcatAudioHandler
from helpers.constants import ConcatOptions


class AudioView(BaseView):
    def __init__(self):
        super().__init__()
        self.config_setup = ConfigSetup()
        self.concat_handler = ConcatAudioHandler()
        self.selected_row = None
        self.table_audio_claims = [[claim.path, claim.pos] for claim in self.config_setup.config_audios.claims]
        
    def claim_window(self):
        layout = [
            [
                sg.Text("Claim path", size=(10,1)),
                sg.In("", size=(50,1), enable_events=True ,key='claim_file'),
                sg.FileBrowse(),
            ],
            [
                sg.Text("Claim position", size=(10,1)),
                sg.In("", size=(50,1), enable_events=True ,key='claim_position'),
            ],
            [
                sg.Button("Add", key="add_claim"),
            ]
        ]
        window = sg.Window("Claim Audio", layout, modal=True)
        while True:
            event, values = window.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            if event == "add_claim":
                if values['claim_file'] and values['claim_position']:
                    self.table_audio_claims.append([values['claim_file'], values['claim_position']])
                    self.window['table_audio_claims'].update(values=self.table_audio_claims)
                    window.close()
                    break
                else:
                    sg.popup_auto_close("Please fill all fields", auto_close_duration=2)
            
        window.close()

    def create_layout(self):
        return [
            [
                sg.Text('Input audio folder:', size=(16,1)), 
                sg.In(self.config_setup.config_audios.input_folder, size=(96,1), enable_events=True ,key='input_audios_folder'), 
                sg.FolderBrowse(),
            ],
            [
                sg.Text('Input audio title:', size=(16,1)), 
                sg.In(self.config_setup.config_audios.input_title, size=(96,1), enable_events=True ,key='input_audio_title'), 
                sg.FolderBrowse(),
            ],
            [
                sg.Text('Output folder:', size=(16,1)), 
                sg.In(self.config_setup.config_audios.output_folder, size=(96,1), enable_events=True ,key='output_audio_folder'), 
                sg.FolderBrowse(), 
            ],
            [
                sg.Frame('Claims', [
                    [
                        sg.Table(
                            values=self.table_audio_claims,
                            headings=['Path', 'Pos'],
                            col_widths=[83, 5],
                            auto_size_columns=False,
                            justification='left',
                            num_rows=10,
                            key='table_audio_claims',
                            enable_events=True,
                            row_height=20,
                            def_col_width=10,
                            hide_vertical_scroll=True,
                        ),
                        sg.Column([
                            [
                                sg.Button('Add', size=(6,1), key='add_audio_claim'),
                            ],
                            [
                                sg.Button('Remove', size=(6,1), key='remove_audio_claim'),
                            ],
                        ], vertical_alignment='top')
                    ]
                ])
            ],
            [
                sg.Frame('Setting', [
                    [
                        sg.Text('With GPU Nvidia:',visible=False),
                        sg.Checkbox('Yes', default=self.config_setup.config_audios.with_gpu, key='audio_with_gpu', visible=False),
                        sg.Text('No files'), sg.In(self.config_setup.config_audios.files_number, key='audio_files_number', size=(3,1)), 
                        sg.Text('Threads', size=(8,1)), sg.In(self.config_setup.config_audios.threads, key='audio_threads', size=(3,1)),
                        sg.Text('Concat options:'),
                        sg.Combo([ConcatOptions.CONCAT_DEMUXER.value, ConcatOptions.CONCAT_FILTER.value], default_value=self.config_setup.config_audios.concat_option, key='audio_concat_options', enable_events=True), 
                    ],
                ])
            ],
            [
                sg.Button('Start', size=(20,1), button_color='green', key='start_concat_audios'),
                sg.Button('Stop', size=(20,1), button_color='red', key='stop_concat_audios', visible=False),
            ],
            [
                sg.Frame('Logs', [
                    [
                        sg.Multiline(size=(122, 10), key='logs_audios',)
                    ]
                ])
            ]
        ]

    def handle_events(self, event, values):
        if event == 'table_audio_claims':
            self.selected_row = str(values['table_audio_claims'][0])
        if event == 'add_audio_claim':
            self.claim_window()
        if event == 'remove_audio_claim':
            if self.selected_row:
                self.table_audio_claims.remove(self.table_audio_claims[int(self.selected_row)])
                self.window['table_audio_claims'].update(values=self.table_audio_claims)
                self.selected_row = None
            else:
                sg.popup_auto_close("Please select a row", auto_close_duration=2)
        if event == 'start_concat_audios':
            # update UI
            self.window['start_concat_audios'].update(visible=False)
            self.window['stop_concat_audios'].update(visible=True)
            # store config
            self.config_setup.store_audio_sub_config(
                Config(
                    input_folder=self.window['input_audios_folder'].get(),
                    output_folder=self.window['output_audio_folder'].get(),
                    input_title=self.window['input_audio_title'].get(),
                    with_gpu=self.window['audio_with_gpu'].get(),
                    files_number=self.window['audio_files_number'].get(),
                    threads=self.window['audio_threads'].get(),
                    concat_option=self.window['audio_concat_options'].get(),
                    claims=[Claim(path=claim[0], pos=claim[1]) for claim in self.table_audio_claims],
                )
            )
            # run concat
            self.concat_handler.start(self.config_setup.config_audios)
        if event == 'stop_concat_audios':
            # update UI
            self.window['start_concat_audios'].update(visible=True)
            self.window['stop_concat_audios'].update(visible=False)
            # stop concat
            self.concat_handler.stop()
        # update logs
        while not self.concat_handler.logs.empty():
            self.window['logs_audios'].print(self.concat_handler.logs.get())
        while not self.concat_handler.tasks_done.empty():
            self.concat_handler.tasks_done.get()
            self.window['start_concat_audios'].update(visible=True)
            self.window['stop_concat_audios'].update(visible=False)