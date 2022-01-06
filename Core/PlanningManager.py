from dateutil import rrule
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from Core.PlanningData import PlanningData
from GUI.Widgets import EndTask, StartTask
from Utils.TaskTime import TaskDelta, TaskDate
from Utils.DirectedGraph import DirectedGraph
from GUI.Widgets import Link
from Utils.FileManager import FileManager
from kivymd.toast import toast
import datetime


class PlanningManager:
    def __init__(self, app, settings):
        self.planning = None
        self.settings = settings
        self.link_container = None
        self.saved = True
        self.app = app

        self.time_cuts = None
        self.n_work_free_days_before_date = None

    def get_totals_hours(self):
        return self.planning.totals_hours

    def get_current_total_hours(self):
        if self.get_totals_hours():
            return self.get_totals_hours()[-1]
        else:
            return 0

    def set_total_hours(self, total_hours):
        day = self.date_to_index(
            self.get_current_date()) // self.get_day_duration()

        if day == len(self.get_totals_hours()):
            self.planning.totals_hours.append(total_hours)
            return

        # We have go back in planning time so we reset the computed totals_hours
        while day < len(self.get_totals_hours()):
            self.planning.totals_hours.pop()
        self.set_total_hours(total_hours)

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

    def get_current_date(self):
        return self.planning.current_date

    def increase_current_date(self, delta):
        self.planning.current_date += delta
        self.saved = False

    def decrease_current_date(self, delta):
        self.planning.current_date -= delta
        self.saved = False

    def set_current_date(self, date):
        self.planning.current_date = date
        self.saved = False

    def update_task(self, *args):
        for task in self.get_tasks():
            task.update_state()

    def update(self, *args):
        self.time_cuts = [0]
        self.n_work_free_days_before_date = {}

        work_free_day_count = 0
        for date in rrule.rrule(rrule.DAILY,
                                dtstart=self.get_project_begin_date().date,
                                until=self.get_project_end_date().date):
            self.n_work_free_days_before_date[
                date.date()] = work_free_day_count

            if date.weekday() in self.get_week_days():
                self.time_cuts.append(0)
            else:
                self.time_cuts[-1] += 1
                work_free_day_count += 1

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

    def get_project_begin_date(self) -> TaskDate:
        return self.planning.project_begin_date

    def set_project_begin_date(self, date: TaskDate):
        self.planning.project_begin_date = date

    def get_project_end_date(self) -> TaskDate:
        return self.planning.project_end_date

    def set_project_end_date(self, date: TaskDate):
        self.planning.project_end_date = date

    def get_week_days(self):
        return self.planning.week_days

    def date_to_index(self, task_date: TaskDate) -> int:
        """Return the index that represents the relative time in solver domain (ie in hour without the workfree days)"""
        if task_date is not None:
            delta = task_date - self.get_project_begin_date()
            return delta.get_duration(
                "hour") - self.n_work_free_days_before_date[
                    task_date.date] * self.get_day_duration()
        else:
            return None

    def index_to_date(self, index: int) -> TaskDate:
        """Return the corresponding TaskDate object where index is the time in the solver domain (ie in hour without the workfree days)"""
        date = self.get_project_begin_date()
        delta = TaskDelta(
            index +
            sum(self.time_cuts[:index // self.get_day_duration() + 1]) *
            self.get_day_duration())
        return date + delta

    def get_planned_end_date(self):
        for task in self.get_pert().V:
            if isinstance(task, EndTask):
                return task.get_begin_date()

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
            key=lambda x: (x.get_begin_date(), x.get_duration()))
        self.get_planning_screen().scrollable_planning.load()
        self.set_saved(False)

    def add_editor_link(self, begin, end):
        """Add an oriented link (graph + graphics) :
            begin: the first component
            end: the second component
            link_container: the widget which will be the parent of graphic link
            """
        self.get_pert().add_link(begin, end)

        self.link_container.add_widget(Link(begin=begin, end=end))

    def remove_editor_link(self, begin, end):
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
        for link in self.link_container.content.children:
            if isinstance(link, Link) and ((link.begin, link.end) == (begin, end) or (link.begin,
                                                                                      link.end) == (end,
                                                                                                    begin)):
                self.link_container.remove_widget(link)
                break

    def create(self, name, capacity, day_duration, week_days):
        self.planning = PlanningData(
            name=name,
            pert=DirectedGraph([StartTask(pos=(0, 0)),
                                EndTask(pos=(300, 0))]),
            capacity=capacity,
            day_duration=day_duration,
            week_days=week_days,
            project_begin_date=TaskDate.from_date(datetime.date.today(), 0),
            project_end_date=TaskDate.from_date(datetime.date.today(), 0),
            current_date=TaskDate.from_date(datetime.date.today(), 0))
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
        self.link_container = self.app.screen_manager.ids.graph_editor_screen.ids.edit_area
        self.planning.bind(current_date=self.update_task,
                           totals_hours=self.update)

        self.update()

        def update_state(instance, value):
            self.get_planning_screen().update_icon_state(value)

        self.planning.bind(planning_state=update_state)
        self.set_saved(True)

    def unload(self):
        self.planning = None
        self.link_container = None
        self.saved = True
        self.n_work_free_days_before_date = None
        self.time_cuts = None

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
