from GUI.Screen import *
from GUI.Widgets import *
from Utils.SettingsManager import SettingsManager
from Core.PlanningManager import PlanningManager
from kivymd.uix.toolbar import MDToolbar
from kivymd.app import MDApp
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.config import Config
from kivymd.toast import toast

Config.set('input', 'mouse', 'mouse,disable_multitouch')


class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = SettingsManager()
        self.manager = PlanningManager(self, self.settings)

        self.tool_bar = MDToolbar(elevation=8)
        self.layout = GridLayout(cols=1)
        self.layout.add_widget(self.tool_bar)

    def build(self):
        self.screen_manager = Builder.load_file(r"GUI/main.kv")

        self.layout.add_widget(self.screen_manager)

        self.screen_manager.ids.new_file_btn.bind(
            on_release=self.screen_manager.ids.projects_list_screen.
            open_create_file_dialog)

        return self.layout

    def change_screen(self, name):
        if name == "burndown_screen" and not self.manager.get_planning_state(
        ) == "up_to_date":
            toast(
                "Planning is not up to date, please fix planning before accessing to burndown chart"
            )
            return

        self.screen_manager.current = name
