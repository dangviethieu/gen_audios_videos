import PySimpleGUI as sg

class BaseView:
    def __init__(self):
        self.window: sg.Window = None
    
    def set_window(self, window: sg.Window):
        self.window = window

    def create_layout(self):
        pass

    def handle_events(self):
        pass