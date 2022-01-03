from kivymd.app import MDApp
from Utils.XAbleObject import SerializableObject
import datetime


class TaskDate(SerializableObject):
    """Represents a task date relative to project begin date and allow conversion between theoretical time domain and real time domain (with work free days)
    """
    def __init__(self, date_str: str, hour: int, **kwargs):
        super().__init__(**kwargs)
        self.date = datetime.date.fromisoformat(date_str)
        self.hour = hour

        self.app = MDApp.get_running_app()

    @classmethod
    def from_date(cls, date: datetime.date, hour: int):
        return cls(str(date), hour)

    def floored(self):
        return TaskDate.from_date(self.date, 0)

    def ceiled(self):
        if self.hour == 0:
            return TaskDate.from_date(self.date, 0)
        else:
            return TaskDate.from_date(self.date + datetime.timedelta(days=1),
                                      0)

    def get_hour(self):
        return self.hour

    def get_day(self):
        return self.date.day

    def get_date(self):
        return (self.date, self.hour)

    def next_day(self):
        hour = self.hour
        self.date += datetime.timedelta(days=1)
        self.hour = 0
        return self.app.manager.get_day_duration() - hour

    def __add__(self, other):
        if not isinstance(other, (TaskDelta)):
            raise ValueError(
                f"Cannot add object of type {type(other)} to an object of type {type(self)}, only {TaskDelta} are allowed."
            )

        date = self.date
        hour = self.hour + other.get_duration()
        while hour >= self.app.manager.get_day_duration():
            date += datetime.timedelta(days=1)
            hour -= self.app.manager.get_day_duration()

        return TaskDate.from_date(date, hour)

    def __sub__(self, other):
        if not isinstance(other, (TaskDelta, TaskDate)):
            raise ValueError(
                f"Cannot substract object of type  {type(other)} to an object of type {type(self)}, only {TaskDelta} and {TaskDate} are allowed."
            )
        if isinstance(other, TaskDelta):
            date = self.date
            hour = self.hour - other.get_duration()
            while hour < 0:
                date -= datetime.timedelta(days=1)
                hour += self.app.manager.get_day_duration()

            return TaskDate.from_date(date, hour)
        else:

            return TaskDelta((self.date - other.date).days *
                             self.app.manager.get_day_duration() + self.hour -
                             other.hour)

    def __lt__(self, other):
        if not isinstance(other, TaskDate):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDate} are allowed."
            )
        return (self.date, self.hour) < (other.date, other.hour)

    def __gt__(self, other):
        if not isinstance(other, TaskDate):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDate} are allowed."
            )
        return (self.date, self.hour) > (other.date, other.hour)

    def __le__(self, other):
        if not isinstance(other, TaskDate):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDate} are allowed."
            )
        return (self.date, self.hour) <= (other.date, other.hour)

    def __ge__(self, other):
        if not isinstance(other, TaskDate):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDate} are allowed."
            )
        return (self.date, self.hour) >= (other.date, other.hour)

    def __eq__(self, other):
        if not isinstance(other, TaskDate):
            return False

        return (self.date, self.hour) == (other.date, other.hour)

    def __str__(self) -> str:
        return str(self.date) + f" {self.hour} h"

    def to_dict(self, **kwargs):
        return super().to_dict(date_str=str(self.date),
                               hour=self.hour,
                               **kwargs)


class TaskDelta(SerializableObject):
    """Represents a task time variation
    """
    def __init__(self, hours: int, **kwargs):
        super().__init__(**kwargs)
        self.hours = hours

        self.app = MDApp.get_running_app()

    @classmethod
    def day(cls, manager):
        return cls(manager.get_day_duration())

    @classmethod
    def from_time(cls, time: int, unit: int, manager):
        if unit == "day":
            return cls(time * manager.get_day_duration())
        elif unit == "hour":
            return cls(time)

    def get_duration(self, unit="hour"):
        if unit == "hour":
            return self.hours
        elif unit == "day":
            working_day, hour = divmod(self.hours,
                                       self.app.manager.get_day_duration())
            return working_day + hour / self.app.manager.get_day_duration()
        elif unit == "split":
            working_day, hour = divmod(self.hours,
                                       self.app.manager.get_day_duration())
            return working_day, hour

    def set_duration(self, duration, unit="hour"):
        if unit == "hour":
            self.hours = duration
        elif unit == "day":
            self.hours = int(duration * self.app.manager.get_day_duration())
        elif unit == "split":
            self.hours = duration[0] * self.app.manager.get_day_duration(
            ) + duration[1]

    def add_duration(self, duration, unit="hour"):
        self.set_duration(self.get_duration(unit) + duration, unit=unit)

    def __add__(self, other):
        if not isinstance(other, (TaskDelta, TaskDate)):
            raise ValueError(
                f"Cannot add object of type {type(other)} to an object of type {type(self)}, only {TaskDelta} and {TaskDate} are allowed."
            )

        if isinstance(other, TaskDate):
            return other + self
        else:
            return TaskDelta(self.hours + other.hours)

    def __sub__(self, other):
        if not isinstance(other, TaskDelta):
            raise ValueError(
                f"Cannot substract object of type {type(other)} to an object of type {type(self)}, only {TaskDelta} are allowed."
            )
        return TaskDelta(self.hours - other.hours)

    def __mult__(self, other):
        if not isinstance(other, int):
            raise ValueError(
                f"Cannot mult object of type {type(other)} to an object of type {type(self)}, only {int} are allowed."
            )

        return TaskDelta(self.hours * other)

    def __lt__(self, other):
        if not isinstance(other, TaskDelta):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDelta} are allowed."
            )
        return self.hours < other.hours

    def __gt__(self, other):
        if not isinstance(other, TaskDelta):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDelta} are allowed."
            )
        return self.hours > other.hours

    def __le__(self, other):
        if not isinstance(other, TaskDelta):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDelta} are allowed."
            )
        return self.hours <= other.hours

    def __ge__(self, other):
        if not isinstance(other, TaskDelta):
            raise ValueError(
                f"Cannot compare {type(other)} to an object of type {type(self)}, only {TaskDelta} are allowed."
            )
        return self.hours >= other.hours

    def __eq__(self, other):
        if not isinstance(other, TaskDelta):
            return False

        return self.hours == other.hours

    def __str__(self) -> str:
        working_day, hour = divmod(self.hours,
                                   self.app.manager.get_day_duration())
        return f"{working_day}d {hour}h"

    def to_dict(self, **kwargs):
        return super().to_dict(hours=self.hours, **kwargs)
