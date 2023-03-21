import os
import time
from .base import BaseView, sg
from controllers.config import ConfigSetup


class AudioView(BaseView):
    def __init__(self):
        super().__init__()
        self.config_setup = ConfigSetup()
        self.table_claims = [[claim.path, claim.pos] for claim in self.config_setup.config_audios.claims]

    def create_layout(self):
        return [
            [
                sg.Text('Input audio folder:', size=(16,1)), 
                sg.In(self.config_setup.config_audios.input_audios_folder, size=(96,1), enable_events=True ,key='input_audios_folder'), 
                sg.FolderBrowse(),
            ],
            [
                sg.Text('Input audio title:', size=(16,1)), 
                sg.In(self.config_setup.config_audios.input_audio_title, size=(96,1), enable_events=True ,key='input_audio_title'), 
                sg.FolderBrowse(),
            ],
            [
                sg.Text('Output folder:', size=(16,1)), 
                sg.In(self.config_setup.config_audios.output_audio_folder, size=(96,1), enable_events=True ,key='output_audio_folder'), 
                sg.FolderBrowse(), 
            ],
            [
                sg.Table(
                    values=self.table_claims,
                    headings=['Path', 'Position'],
                    col_widths=[100, 10, 10],
                    auto_size_columns=False,
                    justification='left',
                    num_rows=10,
                    key='table_claims',
                    enable_events=True,
                    row_height=20,
                    def_col_width=10,
                    hide_vertical_scroll=True,
                    alternating_row_color='lightblue',
                    tooltip='This is a table',
                ),
                sg.Column([
                    [
                        sg.Button('Add', size=(20,1), button_color='green', key='add_claim'),
                    ],
                    [
                        sg.Button('Remove', size=(20,1), button_color='red', key='remove_claim'),
                    ],
                ])      
            ],
            [
                sg.Frame('Setting', [
                    [
                        sg.Text('With GPU Nvidia:',),
                        sg.Checkbox('Yes', default=self.config_setup.config_audios.with_gpu, key='with_gpu'),
                        sg.Text('Threads', size=(8,1)), sg.In(self.config_setup.config_audios.threads, key='threads', size=(3,1)),
                    ],
                ])
            ],
            [
                sg.Button('Start', size=(20,1), button_color='green', key='start_concat_audios'),
            ],
            [
                sg.Frame('Logs', [
                    [
                        sg.Multiline(size=(122, 10), key='logs_sub',)
                    ]
                ])
            ]
        ]

    def handle_events(self, event, values):
        pass