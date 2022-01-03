from pathlib import Path
from kivy.event import EventDispatcher
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from Utils.TaskTime import TaskDate

from Utils.XAbleObject import SerializableObject
from Utils.FileManager import FileManager
from Utils.DirectedGraph import DirectedGraph


class PlanningData(SerializableObject, EventDispatcher):
    """This is the model of a planning_data graph where:
            name: allow to identify the planning_data graph
            graph: the DirectedGraph which represents the anteriority relations"""
    planning_state = StringProperty()
    current_date = ObjectProperty()
    totals_hours = ListProperty()

    def __init__(self,
                 name: str,
                 pert: DirectedGraph,
                 capacity: int,
                 day_duration: int,
                 week_days: list,
                 project_begin_date: TaskDate,
                 project_end_date: TaskDate,
                 current_date: TaskDate,
                 planning_state="up_to_date",
                 totals_hours=[]):
        self.name = name
        self.pert = pert
        self.planning_state = planning_state
        self.capacity = capacity
        self.day_duration = day_duration
        self.totals_hours = totals_hours
        self.current_date = current_date
        self.project_begin_date = project_begin_date
        self.project_end_date = project_end_date
        self.week_days = week_days

    @staticmethod
    def get_planning_data_path_by_name(name, settings, extension=".json"):
        """name: the PlanningData file name
        return: the path to the planning_data file"""
        planning_data_path = Path(settings.get_paths()['save_path'])

        return planning_data_path / (name + extension)

    def to_dict(self):
        return super().to_dict(pert=self.pert,
                               planning_state=self.planning_state,
                               capacity=self.capacity,
                               day_duration=self.day_duration,
                               totals_hours=self.totals_hours,
                               current_date=self.current_date,
                               project_begin_date=self.project_begin_date,
                               project_end_date=self.project_end_date,
                               week_days=self.week_days)

    @classmethod
    def load_planning_data(cls, name, settings):
        """Build the pert and additionnal planning data from file where:
              path: path to json encoded dict containing all necessary data to rebuild components and links (assuming that stored object inherit from SerializableObject or is raw data)
          return: the corresponding PlanningData object"""
        data = FileManager.load_json(
            PlanningData.get_planning_data_path_by_name(name, settings))
        if data is not None:
            return cls.from_dict(data, name=name)
        else:
            raise ValueError(
                "Something has gone wrong with this planning file")
