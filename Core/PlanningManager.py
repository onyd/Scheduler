from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from Core.PlanningData import PlanningData
from GUI.Widgets import EndTask, StartTask
from Utils.DirectedGraph import DirectedGraph
from GUI.Widgets import Link
from Utils.FileManager import FileManager
from kivymd.toast import toast
from math import ceil


class PlanningManager:
    def __init__(self, app, settings):
        self.planning = None
        self.settings = settings
        self.links = []
        self.saved = True
        self.app = app

    def get_horizons(self, unit="day"):
        if unit == "hour":
            return self.planning.horizons
        else:
            return [
                horizon // self.get_day_duration()
                for horizon in self.planning.horizons
            ]

    def get_horizon(self, unit="day", day=-1):
        if unit == "day":
            return self.planning.horizons[day] // self.get_day_duration()
        else:
            return self.planning.horizons[day]

    def set_horizon(self, horizon, unit="day"):
        day = self.get_current_time("day")
        if day == len(self.get_horizons('day')):
            if unit == "day":
                self.planning.horizons.append(horizon *
                                              self.get_day_duration())
            elif unit == "hour":
                self.planning.horizons.append(horizon)
            return

        # We have go back in planning time so we reset the computed horizons
        while day < len(self.get_horizons('day')):
            self.planning.horizons.pop()
        self.set_horizon(horizon, unit)

    def get_capacity(self):
        return self.planning.capacity

    def get_pert(self):
        return self.planning.pert

    def get_tasks(self):
        tasks = []
        for task in self.get_pert().V:
            if not isinstance(task, (StartTask, EndTask)):
                tasks.append(task)
        return tasks

    def get_current_time(self, unit="day"):
        if unit == "day":
            return self.planning.current_time
        else:
            return self.planning.current_time * self.get_day_duration()

    def set_current_time(self, time):
        self.planning.current_time = time
        for task in self.get_tasks():
            task.update_state(self.get_current_time())
        self.saved = False

    def set_saved(self, saved):
        self.saved = saved

    def get_planning_screen(self):
        return self.app.screen_manager.get_screen("planning_screen")

    def get_planning_state(self):
        return self.planning.planning_state

    def set_planning_state(self, state):
        self.planning.planning_state = state

    def get_day_duration(self):
        return self.planning.day_duration

    def set_day_duration(self, duration):
        self.planning.day_duration = duration

    def get_planned_end_day(self):
        for task in self.get_pert().V:
            if isinstance(task, EndTask):
                return int(ceil(task.get_begin_time("day")))

    def has_undone_anterior_tasks(self, to_check):
        pert_copy = self.planning.pert.copy()
        for task in self.get_pert().V:
            if isinstance(task, (StartTask, EndTask)):
                pert_copy.remove_vertex(task)
            elif task.state == "done":
                pert_copy.remove_vertex(task)
        return pert_copy.in_degree(to_check) != 0

    def sort_tasks_by_begin_time(self):
        self.get_pert().sort_verticies(
            key=lambda x: (x.get_begin_time('hour'), x.get_duration('hour')))
        self.get_planning_screen().scrollable_planning.load()
        self.set_saved(False)

    def add_editor_link(self, begin, end, link_container):
        """Add an oriented link (graph + graphics) :
            begin: the first component
            end: the second component
            link_container: the widget which will be the parent of graphic link
            """
        self.get_pert().add_link(begin, end)

        link = Link(begin=begin, end=end)
        link_container.add_widget(link)

        self.links.append(link)

    def remove_editor_link(self, begin, end, link_container):
        """Remove link in graph and graphics stuff:
            begin: the first component
            end: the second component
            (if the orientation is reversed, it retry with begin and end reversed)"""
        # Delete link in graph
        if self.get_pert().adjacent(begin, end):
            self.get_pert().remove_link(begin, end)
        else:
            try:
                self.get_pert().remove_link(end, begin)
            except:
                print("Error: no link")
                return

        # Find graphic link to delete it
        for link in self.links:
            if (link.begin, link.end) == (begin, end) or (link.begin,
                                                          link.end) == (end,
                                                                        begin):
                link_container.remove_widget(link)
                self.links.remove(link)
                return

    def create(self, name, capacity, day_duration):
        self.planning = PlanningData(
            name=name,
            pert=DirectedGraph([StartTask(pos=(0, 0)),
                                EndTask(pos=(300, 0))]),
            capacity=capacity,
            day_duration=day_duration)
        self.save()

    def get_planning_path(self, name=None, extension=".json"):
        if name is None:
            name = self.planning.name
        return PlanningData.get_planning_data_path_by_name(
            name, self.settings, extension)

    def save(self, name=None):
        """Save the graph"""
        FileManager.save_json(
            self.get_planning_path(name=name, extension=".json"),
            self.planning.to_dict())
        self.set_saved(True)
        toast("Saved succesfully")

    def duplicate(self, src_name, dst_name):
        data = FileManager.load_json(
            PlanningData.get_planning_data_path_by_name(
                src_name, self.settings))
        FileManager.save_json(
            self.get_planning_path(name=dst_name, extension=".json"), data)

    def delete(self, name=None):
        """Delete the current planning if it has been saved
          return: None"""
        path = PlanningData.get_planning_data_path_by_name(name, self.settings)
        if path:
            FileManager.delete_file(path)
            toast("Deleted succesfully")
        else:
            print("Error: delete planning has failed")

    def load(self, name):
        """Shortcut to load the graph:
            name: the graph name to load"""
        self.planning = PlanningData.load_planning_data(name, self.settings)

        def update_state(instance, value):
            self.get_planning_screen().update_icon_state(value)

        self.planning.bind(planning_state=update_state)
        self.set_saved(True)

    def unload(self):
        self.planning = None
        self.links = []
        self.saved = True

    def reload(self):
        self.load(self.planning.name)

    def quit(self, to_go_screen_name, callback=lambda: ()):
        if not self.saved:
            color = self.app.theme_cls.primary_color

            save_btn = MDFlatButton(text="Save", text_color=color)
            discard_btn = MDFlatButton(text="Discard", text_color=color)
            text = MDLabel(
                text="Would you like to save the project before leaving ?")

            dialog = MDDialog(title="Create a new Task",
                              type="custom",
                              content_cls=text,
                              buttons=[discard_btn, save_btn])
            dialog.auto_dismiss = False

            def save(*args):
                self.save()
                dialog.dismiss()
                callback()
                self.app.change_screen(to_go_screen_name)

            def discard(*args):
                self.reload()
                dialog.dismiss()
                callback()
                self.app.change_screen(to_go_screen_name)

            save_btn.bind(on_press=save)
            discard_btn.bind(on_press=discard)

            dialog.open()
        else:
            callback()
            self.app.change_screen(to_go_screen_name)
