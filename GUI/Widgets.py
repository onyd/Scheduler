from copy import copy
import enum
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivymd.toast.kivytoast.kivytoast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
import numpy as np
from math import ceil
import datetime
from dateutil import rrule
from sklearn.linear_model import LinearRegression

from kivy.metrics import sp, dp

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatterlayout import ScatterLayout

from kivy.core.window import Window
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Triangle, Rectangle
from kivy.uix.modalview import ModalView

from kivy.properties import (StringProperty, ColorProperty, NumericProperty,
                             ListProperty, ObjectProperty, BooleanProperty,
                             ReferenceListProperty)

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.factory import Factory
from kivy.compat import string_types

from kivymd.app import MDApp
from kivymd.uix.behaviors import (
    RectangularElevationBehavior,
    RectangularRippleBehavior,
    BackgroundColorBehavior,
)
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton, MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.list import (
    IRightBodyTouch,
    OneLineAvatarIconListItem,
)
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.chip import MDChip
from kivymd.uix.menu import MDDropdownMenu
from Utils.TaskTime import TaskDate, TaskDelta
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt

from GUI.Behavior import (SelectDragBehavior, AntiCollisionObject)
from GUI.Behavior import DiscreteMovableBehavior

from Utils.XAbleObject import SerializableObject


class HorizontalGradientRectangle(RelativeLayout):
    gradient_colors = ListProperty()


class VerticalGradientRectangle(RelativeLayout):
    gradient_colors = ListProperty()


class RectangleIconLabelButton(
        RectangularRippleBehavior,
        RectangularElevationBehavior,
        ButtonBehavior,
        BackgroundColorBehavior,
        BoxLayout,
):
    text = StringProperty("")
    source = StringProperty(None, allownone=True)
    frame_color = ColorProperty()
    frame_width = NumericProperty(3.0)
    image_size = ListProperty([36, 36])


class SwitchBase(BoxLayout):
    text = StringProperty()
    font_size = NumericProperty(12)

    color = ColorProperty((0.4, 0.4, 0.4, 1))
    selected_color = ColorProperty(None, allownone=True)

    callback = ObjectProperty(lambda x: None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not touch.is_mouse_scrolling:
            self.callback(self.text)

            if isinstance(self.parent, CustomSwitch):
                self.parent.switch(self.text)


class SwitchCursor(BoxLayout):
    current_color = ColorProperty()

    text = StringProperty()
    font_size = NumericProperty(12)

    anim_duration = NumericProperty(0.5)


class CustomSwitch(RelativeLayout):
    selected = StringProperty()
    selected_switch = ObjectProperty()
    spacing = NumericProperty(4)

    cursor = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_once(lambda _: self.switch(self.selected), 0.1)

    def find_by_text(self, text):
        for children in self.children:
            if isinstance(children, SwitchBase) and children.text == text:
                return children

    def switch(self, text):
        self.selected_switch = self.find_by_text(text)
        self.selected = text

        # Animation
        cursor_anim = Animation(
            pos=self.selected_switch.pos,
            current_color=self.selected_switch.selected_color,
            d=self.cursor.anim_duration,
            t="in_out_expo",
        )
        label_fade_anim = Animation(label_opacity=0,
                                    d=self.cursor.anim_duration / 4,
                                    t="in_out_expo")
        label_fade_anim.bind(on_complete=self.update_text)
        label_in_anim = Animation(label_opacity=1,
                                  d=self.cursor.anim_duration / 4,
                                  t="in_out_expo")

        anim = cursor_anim & (label_fade_anim + label_in_anim)
        anim.start(self.cursor)

    def update_cursor(self, *args):
        if self.selected_switch is not None:
            self.cursor.pos = self.selected_switch.pos
            self.cursor.size = self.selected_switch.size
            self.cursor.current_color = self.selected_switch.selected_color
            self.update_text()

    def update_text(self, *args):
        self.cursor.text = self.selected_switch.text

    def on_size(self, *args):
        i = 0
        n = len(self.children) - 1  # -1 for the cursor

        for child in reversed(self.children):
            child.size = self.width / n - self.spacing, self.height * 0.65

            if isinstance(child, SwitchCursor):
                self.cursor = child
            else:
                child.center = (
                    self.x + (2 * i + 1) * self.width / (2 * n),
                    self.center_y,
                )
                i += 1

        Clock.schedule_once(lambda x: self.update_cursor())


class Grid(FloatLayout):
    square_width = NumericProperty(20)
    square_height = NumericProperty(20)
    square_size = ReferenceListProperty(square_width, square_height)
    line_width = NumericProperty(1)
    line_color = ColorProperty([0.6, 0.6, 0.6, 1.0])

    bold_line_horizontal = BooleanProperty(True)
    bold_line_vertical = BooleanProperty(True)
    bold_step_horizontal = NumericProperty()
    bold_step_vertical = NumericProperty()
    bold_width_multiplier = NumericProperty(2)
    bold_color = ColorProperty([0.3, 0.3, 0.3, 1.0])

    colored_rows = ListProperty()
    rows_color = ColorProperty([0.7, 0.7, 0.7, 1.0])
    colored_columns = ListProperty()
    columns_color = ColorProperty([0.7, 0.7, 0.7, 1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.draw_grid,
                  square_size=self.draw_grid,
                  line_width=self.draw_grid,
                  line_color=self.draw_grid,
                  bold_line_horizontal=self.draw_grid,
                  bold_line_vertical=self.draw_grid,
                  bold_step_horizontal=self.draw_grid,
                  bold_step_vertical=self.draw_grid,
                  bold_width_multiplier=self.draw_grid,
                  bold_color=self.draw_grid,
                  colored_rows=self.draw_grid,
                  rows_color=self.draw_grid,
                  colored_columns=self.draw_grid,
                  columns_color=self.draw_grid)

    def draw_grid(self, *args):
        try:
            self.canvas.before.clear()
            with self.canvas.before:
                Color(rgba=self.rows_color)
                for row in self.colored_rows:
                    Rectangle(pos=(self.x,
                                   self.height - row * self.square_height),
                              size=(self.width, self.square_height))
                Color(rgba=self.columns_color)
                for column in self.colored_columns:
                    Rectangle(pos=(column * self.square_width, self.y),
                              size=(self.square_width, self.height))

                Color(rgba=self.line_color)
                for j in range(0, int(self.width) + 1, int(self.square_width)):
                    # Vertical
                    Line(
                        points=[
                            self.x + j, self.y, self.x + j,
                            self.y + self.height
                        ],
                        width=self.line_width,
                    )

                for i in range(0,
                               int(self.height) + 1, int(self.square_height)):
                    # Horizontal
                    Line(
                        points=[
                            self.x, self.y + i, self.x + self.width, self.y + i
                        ],
                        width=self.line_width,
                    )

                # Bigger
                if self.bold_line_vertical:
                    Color(rgba=self.bold_color)
                    for k in range(
                            0,
                            int(self.width) + 1,
                            int(self.bold_step_vertical * self.square_width)):
                        # Vertical
                        Line(
                            width=self.bold_width_multiplier * self.line_width,
                            points=[
                                self.x + k, self.y, self.x + k,
                                self.y + self.height
                            ],
                        )
                if self.bold_line_horizontal:
                    for k in range(
                            0,
                            int(self.height) + 1,
                            int(self.bold_step_horizontal *
                                self.square_height)):
                        # Horizontal
                        Line(
                            width=self.bold_width_multiplier * self.line_width,
                            points=[
                                self.x, self.y + k, self.x + self.width,
                                self.y + k
                            ],
                        )
        except:
            pass


class Tooltip(Label):
    pass


class Tooltipped(Widget):
    tooltip_txt = StringProperty('Tooltip')
    tooltip_cls = ObjectProperty(Tooltip)
    close_distance = NumericProperty(5)

    def __init__(self, **kwargs):
        self._tooltip = None
        super().__init__(**kwargs)
        fbind = self.fbind
        fbind('tooltip_cls', self._build_tooltip)
        fbind('tooltip_txt', self._update_tooltip)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self._build_tooltip()

        self.closed = True

    def _build_tooltip(self, *largs):
        if self._tooltip:
            self._tooltip = None
        cls = self.tooltip_cls
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        self._tooltip = cls()
        self._update_tooltip()

    def _update_tooltip(self, *largs):
        txt = self.tooltip_txt
        if txt:
            self._tooltip.text = txt
        else:
            self._tooltip.text = ''

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        self._tooltip.pos = pos
        Clock.unschedule(self.display_tooltip
                         )  # cancel scheduled event since I moved the cursor

        # close if it's opened
        if self.collide_point(*self.to_parent(*self.to_widget(*pos))):
            if self.closed:
                Clock.schedule_once(self.display_tooltip, 0.5)
        else:
            self.close_tooltip()

    def close_tooltip(self, *args):
        Window.remove_widget(self._tooltip)
        self.closed = True

    def display_tooltip(self, *args):
        Window.add_widget(self._tooltip)
        self.closed = False


class TaskTooltiped(Tooltipped):
    task = ObjectProperty()

    def update_tooltip(self, *args):
        self.tooltip_txt = ""
        self.tooltip_txt += "Name: " + self.task.name + "\n"
        self.tooltip_txt += "Begin: " + str(self.task.begin_date) + "\n"
        self.tooltip_txt += "End: " + str(self.task.get_end_date()) + "\n"
        self.tooltip_txt += "Duration: " + str(self.task.duration) + "\n"
        self.tooltip_txt += "Description: \n" + self.task.description


class StateIcon(RelativeLayout, Tooltipped):
    states = ListProperty()
    colors = ListProperty()
    tooltip_txts = ListProperty()
    state = StringProperty()
    color = ColorProperty()

    def __init__(self, **kw):
        super().__init__(**kw)

        Clock.schedule_once(lambda x: self.set_state(self.states[0]), 0.1)
        self.bind(state=self.update)

    def update(self, instance, state):
        for i, s in enumerate(self.states):
            if s == state:
                self.color = self.colors[i]
                self.tooltip_txt = self.tooltip_txts[i]

    def set_state(self, state):
        if state in self.states:
            self.state = state


class Component(SelectDragBehavior, BoxLayout, SerializableObject,
                AntiCollisionObject):
    icon = StringProperty("message_bubble.png")
    selected_button = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = None
        self.app = MDApp.get_running_app()

        self.register_event_type("on_add_link")
        self.register_event_type("on_remove_link")

    def setup_gui(self, *args):
        super().setup_gui(*args)

        self.bind(size=lambda x, y: self.draw_selection_box())

    def selection_mode(self, igniter, mode):
        self.mode = mode
        self.selection_frame_color = (0., 1., 0., 1.)
        self.sdb_enabled = False

        # the current selected componet will be pre selected
        if self.selected:
            igniter.pre_selected = self

    def edit_mode(self, igniter, mode):
        self.mode = mode
        self.sdb_enabled = True
        self.unselect()
        self.selection_frame_color = (0., 0., 0., 1.)

    # Event
    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos) and self.mode:
            # add/remove link if predecessor exist or add it and wait for a second touch
            if self.mode == "add_link":
                self.dispatch("on_add_link", self)

            elif self.mode == "remove_link":
                self.dispatch("on_remove_link", self)

        return super().on_touch_down(touch)

    def on_add_link(self, *args):
        pass

    def on_remove_link(self, *args):
        pass

    def to_dict(self, **kwargs):
        return super().to_dict(pos=self.pos, **kwargs)


class SheetView(ModalView, RectangularElevationBehavior,
                BackgroundColorBehavior):
    radius = ListProperty([
        0,
    ])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = MDApp.get_running_app().theme_cls.bg_light


class DialogSheetView(SheetView):
    title = StringProperty("")
    content = ObjectProperty()
    on_validate = ObjectProperty(lambda x: x)
    on_cancel = ObjectProperty(lambda x: x)

    def __init__(self,
                 title="",
                 content=None,
                 on_validate=lambda x: x,
                 on_cancel=lambda x: x,
                 **kwargs):
        super().__init__(**kwargs)

        self.title = title
        self.content = content
        self.on_validate = on_validate
        self.on_cancel = on_cancel

        self.ids.validate_btn.bind(on_press=self.on_validate)
        self.ids.cancel_btn.bind(on_press=self.on_cancel)

        self.ids.content_layout.add_widget(self.content)


class CheckableChip(MDChip):
    active = BooleanProperty(False)

    def on_press(self):
        self.active = not self.active
        return super().on_press()


class Task(Component):
    name = StringProperty("New")
    begin_date = ObjectProperty()
    duration = ObjectProperty()
    resource = NumericProperty(1)
    max_end_date = ObjectProperty(allownone=True)
    min_begin_date = ObjectProperty(allownone=True)
    gradient_colors = ListProperty()
    description = StringProperty("")
    activated = BooleanProperty(True)
    state = StringProperty("pending")
    fixed = BooleanProperty(False)
    assignments = ListProperty([])

    bar_height = NumericProperty()

    def __init__(self,
                 name,
                 duration,
                 resource,
                 begin_date=TaskDate.from_date(datetime.date.today(), 0),
                 min_begin_date=None,
                 max_end_date=None,
                 description="",
                 activated=True,
                 state="pending",
                 fixed=False,
                 **kwargs):
        super().__init__(**kwargs)

        self.name = name
        self.resource = resource
        self.begin_date = begin_date
        self.max_end_date = max_end_date
        self.min_begin_date = min_begin_date
        self.description = description
        self.activated = activated
        self.state = state
        self.prev_state = self.state
        self.fixed = fixed

        Clock.schedule_once(lambda *args: self.setup(duration))

    def setup(self, duration):
        self.bind(activated=self.set_gradient_colors,
                  state=self.update_treatment,
                  fixed=self.draw_fixed_frame,
                  pos=self.draw_fixed_frame,
                  duration=self.update_duration_fields)
        self.bind(pos=lambda *args: self.app.manager.set_saved(False),
                  name=lambda *args: self.app.manager.set_saved(False),
                  resource=lambda *args: self.app.manager.set_saved(False),
                  duration=lambda *args: self.app.manager.set_saved(False),
                  description=lambda *args: self.app.manager.set_saved(False),
                  activated=lambda *args: self.app.manager.set_saved(False),
                  state=lambda *args: self.app.manager.set_saved(False),
                  fixed=lambda *args: self.app.manager.set_saved(False),
                  min_begin_date=lambda *args: self.app.manager.set_saved(
                      False),
                  max_end_date=lambda *args: self.app.manager.set_saved(False),
                  assignments=lambda *args: self.app.manager.set_saved(False))
        self.bind(resource=self.update_planning_state,
                  begin_date=self.update_planning_state,
                  duration=self.update_planning_state,
                  min_begin_date=self.update_planning_state,
                  max_end_date=self.update_planning_state,
                  activated=self.update_planning_state,
                  state=self.update_planning_state)
        self.set_duration(duration, force=True)

        # Duration/resource binds
        self.ids.day_text_field.bind(text=self.update_duration)
        self.ids.hour_text_field.bind(text=self.update_duration)
        self.ids.resource_text_field.bind(text=self.update_resource)

        # max/min datebinds
        self.ids.min_begin_date_picker_button.bind(
            on_release=self.open_min_begin_date_picker)
        self.ids.min_begin_date_reset_button.bind(
            on_release=lambda *args: self.update_min_begin_date(None))
        self.ids.max_end_date_picker_button.bind(
            on_release=self.open_max_end_date_picker)
        self.ids.max_end_date_reset_button.bind(
            on_release=lambda *args: self.update_max_end_date(None))

        self.set_gradient_colors()
        self.draw_fixed_frame()

    def update_duration(self, *args):
        day = self.ids.day_text_field.text
        hour = self.ids.hour_text_field.text
        duration = TaskDelta(0)
        if day != "":
            duration.add_duration(int(day), unit="day")
        if hour != "":
            duration.add_duration(int(hour), unit="hour")
        self.set_duration(duration)

    def update_duration_fields(self, *args):
        day, hour = self.duration.get_duration("split")
        self.ids.day_text_field.input_text = str(day)
        self.ids.hour_text_field.input_text = str(hour)

    def update_resource(self, instance, value):
        if value != "":
            self.resource = int(value)

    def update_min_begin_date(self, date):
        if date is not None:
            self.min_begin_date = TaskDate.from_date(date, 0)
        else:
            self.min_begin_date = None

    def open_min_begin_date_picker(self, *args):
        min_begin_date_dialog = MDDatePicker()
        min_begin_date_dialog.bind(on_save=lambda instance, date, date_range:
                                   self.update_min_begin_date(date))
        min_begin_date_dialog.open()

    def update_max_end_date(self, date):
        if date is not None:
            self.max_end_date = TaskDate.from_date(date, 0)
        else:
            self.max_end_date = None

    def open_max_end_date_picker(self, *args):
        max_end_date_dialog = MDDatePicker()
        max_end_date_dialog.bind(on_save=lambda instance, date, date_range:
                                 self.update_max_end_date(date))
        max_end_date_dialog.open()

    def get_state_gradient_colors(self):
        if self.state == "done":
            return [(0.0, 0.7, 0.4, 0.6), (0.0, 0.2, 0.7, 0.6)]
        elif self.state == "pending":
            return [(0.8, 0., 0., 0.5), (0.2, 0.2, 0.7, 0.6)]
        elif self.state == "waiting_for_treatment":
            return [(1.0, 0.5, 0.1, 0.6), (0.9, 0.9, 0.0, 0.6)]
        elif self.state == "progress":
            return [(0.8, 0.0, 0.8, 0.6), (0.2, 0.2, 0.7, 0.6)]

    def set_gradient_colors(self, *args):
        if self.activated:
            self.gradient_colors = self.get_state_gradient_colors()
        else:
            self.gradient_colors = [(0.7, 0.7, 0.7, 0.5), (0.2, 0.2, 0.2, 0.5)]

    def update_treatment(self, instance, value):
        # We enter in waiting_for_treatment state so the counter increases
        if value == "waiting_for_treatment":
            self.app.manager.get_planning_screen().add_waiting_for_treatment()
        # We exit waiting_for_treatment state so the counter decreases
        elif self.prev_state == "waiting_for_treatment" and value != "waiting_for_treatment":
            self.app.manager.get_planning_screen(
            ).remove_waiting_for_treatment()
        self.prev_state = value
        self.set_gradient_colors()

    def update_state(self, *args):
        if self.state != "done":
            self.set_undone()

    def draw_fixed_frame(self, *args):
        self.canvas.after.remove_group("fixed_frame")
        if self.fixed:
            with self.canvas.after:
                Color(0.5, 0.1, 0.3)
                Line(rectangle=[*self.pos, *self.size],
                     width=2,
                     group="fixed_frame")

    def set_done(self):
        if self.begin_date > self.app.manager.get_current_date(
        ) + TaskDelta.day(self.app.manager):
            toast("The task cannot be done before it has begun")
            return
        if self.app.manager.has_undone_anterior_tasks(self):
            toast(
                "This task can't be set done because there is at least one undone anterior task"
            )
            return

        current_date = self.app.manager.get_current_date()
        if self.get_end_date().floored() > current_date:
            delta = TaskDelta(
                sum(self.get_durations_span()[:int(
                    ceil((current_date + TaskDelta.day(self.app.manager) -
                          self.begin_date).get_duration("day")))]))

            self.set_duration(delta)
        self.state = "done"

    def set_undone(self):
        if self.is_in_progress_for_date(self.app.manager.get_current_date(),
                                        strict=False):
            self.state = "progress"
        elif self.begin_date > self.app.manager.get_current_date():
            self.state = "pending"
        elif self.get_end_date() <= self.app.manager.get_current_date():
            self.state = "waiting_for_treatment"

    def update_planning_state(self, *args):
        self.app.manager.get_planning_screen().update_planning_state()

    def callback_on(self, *args):
        self.activated = True

    def callback_off(self, *args):
        self.activated = False

    def on_touch_down(self, touch):
        if touch.is_double_tap and self.collide_point(*touch.pos):
            content = EditTaskDialogContent()
            content.ids.description_input.text = self.description
            content.ids.name_text_field.input_text = self.name

            def on_validate(*args):
                self.name = content.ids.name_text_field.text
                self.description = content.ids.description_input.text
                sheetview.dismiss()

            sheetview = DialogSheetView(
                title='Edit task',
                content=content,
                on_validate=on_validate,
                on_cancel=lambda x: sheetview.dismiss(),
                size_hint=(0.8, 0.8))

            sheetview.open()
            return True
        else:
            return super().on_touch_down(touch)

    def is_in_progress_for_date(self, date, strict=True):
        """Return True iff the task is in progress at date, strict=False indicates to consider day extended interval"""
        if strict:
            return self.begin_date <= date < self.get_end_date()
        else:
            return self.begin_date.floored() <= date < self.get_end_date(
            ).ceiled()

    def do_continue(self, date, strict=True):
        if strict:
            return date < self.get_end_date()
        else:
            return date < (self.get_end_date() - TaskDelta(1)).floored()

    def get_begin_date(self):
        return self.begin_date

    def set_begin_date(self, begin_date, force=False):
        if not force and (self.fixed or self.state == "done"):
            return

        self.begin_date = begin_date

    def get_duration(self):
        return self.duration

    def set_duration(self, duration: TaskDelta, force=False):
        if not force and self.state == "done":
            return

        self.duration = duration

    def add_duration(self, duration: TaskDelta, force=False):
        if not force and self.state == "done":
            return

        self.duration += duration

    def get_end_date(self):
        durations_span = [
            e if e != 0 else 7 for e in self.get_durations_span()
        ]
        return self.begin_date + TaskDelta(sum(durations_span))

    def get_durations_span(self):
        duration = self.duration.get_duration("hour")
        task_date = copy(self.begin_date)
        span = []
        while duration > 0:
            if task_date.date.weekday() in self.app.manager.get_week_days():
                day_duration = min(task_date.next_day(), duration)
                span.append(day_duration)
                duration -= day_duration
            else:
                span.append(0)
                task_date.next_day()
        return span

    def get_progression(self):
        if self.state == "done":
            return 100

        current_date = self.app.manager.get_current_date()
        return sum(self.get_durations_span()[:max(
            0, int(ceil((current_date - self.begin_date).get_duration("day")))
        )]) / self.duration.get_duration() * 100

    def get_consumed_resources(self):
        return self.resource

    def get_name(self):
        return self.name

    def to_dict(self, **kwargs):
        return super().to_dict(duration=self.duration,
                               begin_date=self.begin_date,
                               resource=self.resource,
                               min_begin_date=self.min_begin_date,
                               max_end_date=self.max_end_date,
                               name=self.name,
                               description=self.description,
                               activated=self.activated,
                               state=self.state,
                               fixed=self.fixed,
                               assignments=self.assignments,
                               **kwargs)


class EditTaskDialogContent(BoxLayout):
    pass


class StartTask(Component):
    def get_begin_date(self):
        return self.app.manager.get_project_begin_date()

    def get_duration(self):
        return TaskDelta(0)


class EndTask(Component):
    begin_date = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_begin_date(self):
        return self.begin_date

    def set_begin_date(self, begin_date):
        self.begin_date = begin_date

    def get_duration(self):
        return TaskDelta(0)

    def to_dict(self, **kwargs):
        return super().to_dict(begin_date=self.begin_date, **kwargs)


class ComponentBar(RelativeLayout):
    pass


class SwitchComponentBar(RelativeLayout):
    pass


class GradientComponentBar(ComponentBar, HorizontalGradientRectangle):
    pass


class GradientSwitchComponentBar(SwitchComponentBar,
                                 HorizontalGradientRectangle):
    pass


class GrabableGrid(ScatterLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_grid(self):
        self.grid = Grid(size_hint=(None, None))
        self.grid.bind(height=lambda instance, value: self.grid.setter(
            'bold_step_horizontal')
            (instance, value / self.grid.square_height / 3),
            width=lambda instance, value: self.grid.setter(
            'bold_step_vertical')
            (instance, value / self.grid.square_width / 3))
        self.add_widget(self.grid)

        self.bind(size=self.update_grid)
        Clock.schedule_once(self.update_grid)
        Clock.schedule_once(self.to_center)

    def collide_point(self, x, y):
        x0, y0 = self.parent.to_local(self.parent.x, self.parent.y)
        x1, y1 = self.parent.to_local(self.parent.right, self.parent.top)

        if x > x0 and x < x1 and y > y0 and y < y1:
            return True
        else:
            return False

    def on_touch_up(self, touch):

        # Round coordinates to have "aimed positioning"
        if touch.grab_current is self:
            touch.ungrab(self)
            x = self.pos[0] / 10
            x = round(x, 0)
            x = x * 10
            y = self.pos[1] / 10
            y = round(y, 0)
            y = y * 10
            self.pos = x, y
            return super().on_touch_up(touch)

    def on_transform_with_touch(self, touch):
        # When there is translation change position of the grid to keep it in view
        view_center = self.to_local(self.parent.center_x, self.parent.center_y)
        self.from_center = (
            view_center[0] - self.grid.center_x,
            view_center[1] - self.grid.center_y,
        )
        if abs(self.from_center[0]) > self.grid.width / 3:
            if self.from_center[0] > 0:
                self.grid.x += self.grid.width / 3
            else:
                self.grid.x -= self.grid.width / 3

        if abs(self.from_center[1]) > self.grid.height / 3:
            if self.from_center[1] > 0:
                self.grid.y += self.grid.height / 3
            else:
                self.grid.y -= self.grid.height / 3

        self.grid.draw_grid()

    def on_touch_down(self, touch):

        if touch.is_mouse_scrolling:
            if touch.button == "scrolldown":
                # zoom in
                if self.scale < self.scale_max:
                    self._set_scale(self.scale * 1.1)
                    if self.scale > self.scale_max:
                        self.scale = self.scale_max

            elif touch.button == "scrollup":
                # zoom out
                if self.scale > self.scale_min:
                    self._set_scale(self.scale * 0.9)
                    if self.scale < self.scale_min:
                        self.scale = self.scale_min

        return super().on_touch_down(touch)

    def update_grid(self, *args):
        s = 3 * max(*self.size) / self.scale_min
        self.grid.size = s, s
        self.grid.draw_grid()

    def to_center(self, *args):
        self.center = self.parent.width / 2, self.parent.height / 2
        self.grid.center = self.width / 2, self.height / 2
        self.grid.draw_grid()


class TimeSpan(BoxLayout):
    begin_date = ObjectProperty()
    end_date = ObjectProperty()
    text = StringProperty()
    margin = NumericProperty()
    chunk_size = NumericProperty()
    index_unit = StringProperty()

    bar_y = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setup()

    def setup(self):
        rule = rrule.DAILY if self.index_unit == "day" else rrule.HOURLY
        for i, date in enumerate(
                rrule.rrule(rule, dtstart=self.begin_date,
                            until=self.end_date)):
            self.ids.week_days_layout.add_widget(
                CircleIndex(index=str(date.day)
                            if self.index_unit == "day" else str(i),
                            size_hint=(None, None),
                            size=(self.chunk_size - self.margin,
                                  self.chunk_size - self.margin)))


class ScrollablePlanning(FloatLayout):
    chunk_size = NumericProperty()
    margin = NumericProperty()
    n_rows = NumericProperty()
    n_cols = NumericProperty()
    tasks_width = NumericProperty()
    tasks_height = NumericProperty(10)
    planning_unit = StringProperty("day")
    n_waiting_for_treatment = NumericProperty(0)
    show_time_cursor = BooleanProperty(True)

    cursor = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()

    def setup(self, *args):
        self.tasks_height = self.chunk_size
        self.n_waiting_for_treatment = 0

        for task in self.app.manager.get_tasks():
            self.add_task(task.name)
            if task.state == "waiting_for_treatment":
                self.n_waiting_for_treatment += 1

        self.bind(n_waiting_for_treatment=self.update_planning_state,
                  show_time_cursor=lambda *args: self.setup_cursor(self.app.manager.get_current_date()))
        self.app.manager.planning.bind(planning_state=self.update_cursor,
                                       totals_hours=self.update_cursor)
        self.setup_cursor(self.app.manager.get_current_date())

    def update_week_days(self, *args):
        self.ids.planning_grid.colored_columns = []
        if self.planning_unit == "day":
            for i, date in enumerate(
                    rrule.rrule(
                        rrule.DAILY,
                        dtstart=self.app.manager.get_project_begin_date().date,
                        until=self.app.manager.get_project_end_date().date)):
                if date.weekday() not in self.app.manager.get_week_days():
                    self.ids.planning_grid.colored_columns.append(i)

    def update_cursor(self, *args):
        if self.cursor:
            self.cursor.max_cursor_position = self.app.manager.get_current_total_hours(
            ) // self.app.manager.get_day_duration()

    def update_planning_state(self, *args):
        if self.n_waiting_for_treatment == 0:
            self.app.manager.set_planning_state("to_validate")
        else:
            self.app.manager.set_planning_state("waiting_for_treatment")

    def setup_cursor(self, date):
        if self.show_time_cursor:
            self.cursor = TimeCursor(size_hint=(None, None),
                                     gradient_colors=[(0.8, 0.2, 0.1, 0.6),
                                                      (0.2, 0.2, 0.4, 0.6)],
                                     size=(self.chunk_size,
                                           self.ids.planning_grid.height),
                                     buttons_width=self.chunk_size,
                                     buttons_height=self.chunk_size,
                                     x_step=self.chunk_size,
                                     pos_hint={'top': 1})
            self.update_cursor()

            # Add the cusor in the backgroud
            self.ids.planning_layout.add_widget(self.cursor)

            self.cursor.set_cursor(
                (date -
                 self.app.manager.get_project_begin_date()).get_duration("day"))
            self.cursor.bind(cursor_position=lambda *args: self.app.manager.
                             get_planning_screen().update_planning_state())
            self.ids.planning_grid.bind(height=self.cursor.setter('height'))
        elif self.cursor:
            self.ids.planning_layout.remove_widget(self.cursor)

    def set_times(self, start_date, end_date):
        self.ids.time_layout.clear_widgets()

        freq = 7 if self.planning_unit == "day" else self.app.manager.get_day_duration(
        )
        rule = rrule.WEEKLY if self.planning_unit == "day" else rrule.DAILY
        delta = datetime.timedelta(
            days=freq -
            1) if self.planning_unit == "day" else datetime.timedelta(
                hours=freq - 1)

        self.n_cols = 0
        for i, date in enumerate(
                rrule.rrule(rule, dtstart=start_date, until=end_date)):
            end = date + delta
            text = f"({date.day}-{date.month}-{date.year}) Week {i+1} ({end.day}-{end.month}-{end.year})" if self.planning_unit == "day" else f"Day ({date.day}-{date.month}-{date.year})"
            time_span = TimeSpan(text=text,
                                 begin_date=date,
                                 end_date=end,
                                 index_unit=self.planning_unit,
                                 chunk_size=self.chunk_size,
                                 margin=self.margin,
                                 pos_hint={"center_y": 0.5})
            self.ids.time_layout.add_widget(time_span)
            self.n_cols += freq

    def on_unit_switch(self, unit):
        self.load(unit)

    def add_task(self, task_name):
        self.n_rows = len(self.ids.tasks_layout.children) + 1
        task_label = TaskLabel(text=task_name,
                               index=f"{self.n_rows}",
                               width=self.tasks_width)
        self.ids.tasks_layout.add_widget(task_label)

        self.bind(tasks_height=task_label.setter('height'))

        def update_tasks_height(*args):
            if self.chunk_size < task_label.ids.label.height > self.tasks_height:
                self.tasks_height = task_label.ids.label.height
            task_label.height = self.tasks_height

        Clock.schedule_once(update_tasks_height)

    def add_task_span(self, i, j, planning_unit, task):
        task_span = TaskSpan(i=i,
                             cursor_position=j,
                             n=self.n_rows,
                             planning_unit=planning_unit,
                             square_width=self.chunk_size,
                             square_height=self.tasks_height,
                             task=task)
        self.bind(tasks_height=task_span.setter('square_height'))
        self.ids.planning_grid.add_widget(task_span)

    def unload(self):
        self.ids.tasks_layout.clear_widgets()
        self.ids.time_layout.clear_widgets()
        self.ids.planning_grid.clear_widgets()
        if self.cursor:
            self.ids.planning_layout.remove_widget(self.cursor)

    def load(self, unit='day'):
        self.ids.time_layout.clear_widgets()
        self.ids.planning_grid.clear_widgets()
        self.planning_unit = unit

        if self.planning_unit == "day":
            self.ids.unit_switch.switch("day")
            self.set_times(self.app.manager.get_project_begin_date().date,
                           self.app.manager.get_project_end_date().date)

            # Build the planning
            for i, task in enumerate(self.app.manager.get_tasks()):
                self.add_task_span(
                    i=i + 1,
                    j=(task.begin_date -
                       self.app.manager.get_project_begin_date()).hours,
                    planning_unit=self.planning_unit,
                    task=task)

            self.show_time_cursor = True
        else:
            self.ids.unit_switch.switch("hour")
            date = datetime.datetime.combine(
                self.app.manager.get_project_begin_date().date +
                datetime.timedelta(days=self.cursor.cursor_position),
                datetime.datetime.min.time())
            self.set_times(
                date, date +
                datetime.timedelta(hours=self.app.manager.get_day_duration()))

            # Build the planning
            current_date = self.app.manager.get_current_date()
            for i, task in enumerate(self.app.manager.get_tasks()):
                if task.is_in_progress_for_date(current_date, strict=False):
                    self.add_task_span(
                        i=i + 1,
                        j=max(0, (task.begin_date - current_date).hours) *
                        self.app.manager.get_day_duration(),
                        planning_unit=self.planning_unit,
                        task=task)
            self.show_time_cursor = False
        self.update_week_days()


class CreateProjectDialogContent(BoxLayout):
    pass


class Backlog(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()

    def setup(self):
        self.ids.to_do_layout.clear_widgets()
        self.ids.pending_layout.clear_widgets()
        self.ids.done_layout.clear_widgets()

        for task in self.app.manager.get_tasks():
            if task.state == "done":
                self.ids.done_layout.add_widget(TaskItem(task=task))
            elif task.state == "pending":
                self.ids.pending_layout.add_widget(TaskItem(task=task))
            else:
                self.ids.to_do_layout.add_widget(TaskItem(task=task))


class AddChipField(BoxLayout):
    pass


class AssignmentChip(MDChip):
    assignement_list = ObjectProperty()

    def on_touch_up(self, touch):
        if touch.is_double_tap and self.collide_point(*touch.pos):
            color = self.assignement_list.app.theme_cls.primary_color

            validate_btn = MDFlatButton(text="Validate", text_color=color)
            discard_btn = MDFlatButton(text="Discard", text_color=color)
            name_field = MDLabel(
                text=f"Do you want to remove the assignement {self.text} from task {self.assignement_list.task.get_name()} ?"
            )

            dialog = MDDialog(title="Remove assignment",
                              type="custom",
                              content_cls=name_field,
                              buttons=[discard_btn, validate_btn])
            dialog.auto_dismiss = False

            def validate(*args):
                self.assignement_list.task.assignments.remove(self.text)
                self.assignement_list.ids.content.remove_widget(self)
                dialog.dismiss()

            def discard(*args):
                dialog.dismiss()

            validate_btn.bind(on_press=validate)
            discard_btn.bind(on_press=discard)

            dialog.open()

        return super().on_touch_up(touch)


class ChipList(BoxLayout):
    task = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()

        Clock.schedule_once(lambda x: self.setup())

    def setup(self):
        for assignment in self.task.assignments:
            self.ids.content.add_widget(
                AssignmentChip(text=assignment, assignement_list=self))

    def open_add_dialog(self):
        color = self.app.theme_cls.primary_color

        validate_btn = MDFlatButton(text="Validate", text_color=color)
        discard_btn = MDFlatButton(text="Discard", text_color=color)
        name_field = AddChipField()

        dialog = MDDialog(title="Assign a person to the task",
                          type="custom",
                          content_cls=name_field,
                          buttons=[discard_btn, validate_btn])
        dialog.auto_dismiss = False

        def validate(*args):
            self.task.assignments.append(name_field.ids.field.text)
            self.ids.content.add_widget(
                AssignmentChip(text=name_field.ids.field.text,
                               assignement_list=self))
            dialog.dismiss()

        def discard(*args):
            dialog.dismiss()

        validate_btn.bind(on_press=validate)
        discard_btn.bind(on_press=discard)

        dialog.open()


class TaskItem(HorizontalGradientRectangle, TaskTooltiped):
    task = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)

        Clock.schedule_once(lambda x: self.setup())

    def setup(self):
        self.gradient_colors = self.task.get_state_gradient_colors()
        self.update_tooltip()


class BurndownChart(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = MDApp.get_running_app()

    def setup(self):
        self.clear_widgets()

        # Compute burndown chart
        totals_hours = self.app.manager.get_totals_hours()
        current_index = self.app.manager.date_to_index(
            self.app.manager.get_current_date(
            )) // self.app.manager.get_day_duration()
        project_end_index = self.app.manager.date_to_index(
            self.app.manager.get_project_end_date(
            )) // self.app.manager.get_day_duration()
        max_t = min(len(totals_hours) + 1, current_index + 2)
        X = np.arange(0, project_end_index + 1)
        x = np.arange(0, max_t)
        y = np.array([totals_hours[0]] +
                     [total_hours for total_hours in totals_hours[:max_t - 1]])
        d_totals_hours = np.array([0] +
                                  [y[i] - y[i - 1] for i in range(1, max_t)])
        over_estimated_mask = d_totals_hours < 0
        under_estimated_mask = d_totals_hours > 0
        y_lim = max(y)

        for task in self.app.manager.get_tasks():
            if task.state == "done":
                durations_span = [
                    e for e in task.get_durations_span() if e != 0
                ]
                duration_acc = 0
                i = 1  # Begin to 1 because of the right shift of barplot
                begin_index = self.app.manager.date_to_index(
                    task.begin_date) // self.app.manager.get_day_duration()
                # Average the duration of the task over its execution
                for date in rrule.rrule(
                        rrule.DAILY,
                        dtstart=task.begin_date.date,
                        until=self.app.manager.get_project_end_date().date):
                    if date.weekday() in self.app.manager.get_week_days():
                        if begin_index + i >= len(y):
                            break
                        if i - 1 < len(durations_span):
                            duration_acc += durations_span[i - 1]
                        y[begin_index + i] -= duration_acc
                        i += 1

        reg = LinearRegression().fit(np.reshape(x, (-1, 1)), y)

        # Plot
        self.fig, ax = plt.subplots()
        ax.bar(x[:-1], y[:-1], color='blue')
        ax.bar([x[-1]], [y[-1]], color='orange')
        ax.bar(x[under_estimated_mask],
               d_totals_hours[under_estimated_mask],
               color='red')
        ax.bar(x[over_estimated_mask],
               -d_totals_hours[over_estimated_mask],
               color='green')
        reg_line = ax.plot(X, [reg.coef_[0] * t + reg.intercept_ for t in X],
                           label='linear regression',
                           c='r')
        ax.set_ylabel("Remaining efforts (hour)")
        ax.set_xlabel("Days")
        ax.set_title("Burndown chart")
        ax.set_ylim([0, y_lim + 1])
        ax.set_xticks(X)
        end_date = self.app.manager.get_planned_end_date()
        ax.text(
            1.0,
            1.0,
            f'Velocity: {int(round(-reg.coef_[0]))} hour/day\nPlanned: {end_date}|{self.app.manager.date_to_index(end_date)//self.app.manager.get_day_duration()+1}',
            horizontalalignment='right',
            verticalalignment='bottom',
            transform=ax.transAxes)

        colors = {
            'added work': 'red',
            'deleted work': 'green',
            'remaining work': 'blue',
            'current remaining work': 'orange'
        }
        labels = list(colors.keys())
        handles = [
            plt.Rectangle((0, 0), 1, 1, color=colors[label])
            for label in labels
        ]
        ax.legend(handles + reg_line, labels + ['linear regression'])
        self.add_widget(FigureCanvasKivyAgg(self.fig))

    def export_burndown(self, path):
        self.fig.savefig(path)


class TaskLabel(BoxLayout):
    text = StringProperty()
    index = StringProperty()
    min_chunk_size = NumericProperty()


class TaskTreatmentDialog(BoxLayout):
    task = ObjectProperty()
    unit = StringProperty("hour")

    def set_unit(self, unit):
        self.unit = unit


class TimeCursor(DiscreteMovableBehavior, VerticalGradientRectangle):
    arrow_width = NumericProperty()

    def __init__(self, **kwargs):
        self.app = MDApp.get_running_app()
        super().__init__(**kwargs)

    def on_move_left(self, *args):
        self.app.manager.decrease_current_date(TaskDelta.day(self.app.manager))
        if self.app.manager.get_current_date().date.weekday(
        ) not in self.app.manager.get_week_days():
            self.cursor_position -= 1
            self.dispatch("on_move_left")

    def on_move_right(self, *args):
        self.app.manager.increase_current_date(TaskDelta.day(self.app.manager))
        if self.app.manager.get_current_date().date.weekday(
        ) not in self.app.manager.get_week_days():
            self.cursor_position += 1
            self.dispatch("on_move_right")


class TaskSpanSpacer(Widget):
    square_width = NumericProperty()
    square_height = NumericProperty()


class TaskSpanElement(HorizontalGradientRectangle):
    square_width = NumericProperty()
    square_height = NumericProperty()

    hour_span = NumericProperty(0)

    do_have_index = BooleanProperty(False)
    index = StringProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.square_index = None

        self.bind(do_have_index=self.update_index)
        self.update_index()

    def update_index(self, *args):
        if self.do_have_index:
            self.square_index = SquareIndex(index=self.index,
                                            text_color=(1.0, 1.0, 1.0, 1.0),
                                            bg_color=(0.4, 0.4, 0.4, 0.6),
                                            pos_hint={'center_x': 0.5, 'center_y': 0.5})
            self.bind(index=self.square_index.setter('index'))
            self.add_widget(self.square_index)
        elif self.square_index:
            self.remove_widget(self.square_index)
            self.square_index = None


class TaskSpan(DiscreteMovableBehavior, RelativeLayout, TaskTooltiped):
    i = NumericProperty()
    n = NumericProperty()
    planning_unit = StringProperty()
    square_width = NumericProperty()
    square_height = NumericProperty()
    task = ObjectProperty()

    gradient_colors = ListProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = MDApp.get_running_app()

        Clock.schedule_once(self.setup)

    def setup(self, *args):
        self.task.bind(state=self.set_gradient_colors,
                       description=self.setter('tooltip_txt'),
                       duration=self.build,
                       begin_date=self.build)
        self.task.bind(fixed=self.draw_fixed_frame,
                       duration=self.update_tooltip,
                       begin_date=self.update_tooltip)
        self.bind(cursor_position=self.task.update_state)

        if self.planning_unit == "day":
            self.task.bind(
                fixed=self.update_do_move_x,
                state=self.update_do_move_x)
            self.update_do_move_x()
        else:
            self.do_move_x = False

        self.update_tooltip()
        self.build()
        self.draw_continue_arrow()
        Clock.schedule_once(self.draw_fixed_frame)

    def update_do_move_x(self, *args):
        self.do_move_x = not (self.task.state == "done" or self.task.fixed)

    def on_move_left(self, *args):
        self.task.set_begin_date(self.task.begin_date - TaskDelta(1))
        if self.task.begin_date.date.weekday(
        ) not in self.app.manager.get_week_days():
            self.cursor_position -= 1
            self.dispatch("on_move_left")

    def on_move_right(self, *args):
        self.task.set_begin_date(self.task.begin_date + TaskDelta(1))
        if self.task.begin_date.date.weekday(
        ) not in self.app.manager.get_week_days():
            self.cursor_position += 1
            self.dispatch("on_move_right")

    def get_current_span(self, unit="hour"):
        if unit == "hour":
            return self.durations_span[int(
                ceil(
                    (self.app.manager.get_current_date() - self.task.begin_date
                     ).hours / self.app.manager.get_day_duration())
            )] * self.app.manager.get_day_duration()
        elif unit == "day":
            return self.durations_span[int(
                ceil((self.app.manager.get_current_date() -
                      self.task.begin_date).hours /
                     self.app.manager.get_day_duration()))]

    def build(self, *args):
        self.gradient_colors = self.task.get_state_gradient_colors()
        self.durations_span = self.task.get_durations_span()
        self.ids.layout.clear_widgets()

        if self.planning_unit == "day":
            elements = []
            begin_gradient_color = self.gradient_colors[0]
            durations_acc = 0
            for i, hours in enumerate(self.durations_span):
                if hours > 0:
                    durations_acc += self.durations_span[i]
                    t = durations_acc / self.task.duration.get_duration()
                    end_gradient_color = list(
                        (1 - t) * np.array(self.gradient_colors[0]) +
                        t * np.array(self.gradient_colors[1]))
                    element = TaskSpanElement(square_width=self.square_width,
                                              square_height=self.square_height,
                                              gradient_colors=[
                                                  begin_gradient_color,
                                                  end_gradient_color
                                              ],
                                              hour_span=hours)
                    elements.append(element)
                    self.ids.layout.add_widget(element)
                    begin_gradient_color = end_gradient_color
                else:
                    self.ids.layout.add_widget(
                        TaskSpanSpacer(square_width=self.square_width,
                                       square_height=self.square_height))
            indexed = elements[len(elements)//2]
            indexed.index = str(self.task.get_consumed_resources())
            indexed.do_have_index = True
        else:
            element = TaskSpanElement(square_width=self.square_width,
                                      square_height=self.square_height,
                                      gradient_colors=self.gradient_colors,
                                      hour_span=self.get_current_span(
                                          "hour"),
                                      index=str(
                                          self.task.get_consumed_resources()),
                                      do_have_index=True)
            self.ids.layout.add_widget(element)

    def draw_continue_arrow(self, *args):
        self.canvas.after.remove_group("continue_arrow")
        if self.planning_unit == "hour" and self.task.do_continue(
                self.app.manager.get_current_date(), strict=False):
            span = self.get_current_span("day")
            with self.canvas.after:
                Color(0.0, 0.0, 0.0)
                Triangle(points=[
                    self.x + span * self.square_width, self.y,
                    self.x + span * self.square_width,
                    self.y + self.square_height,
                    self.x + (span + 1 / 2.0) * self.square_width,
                    self.y + self.square_height / 2.0
                ],
                    group="continue_arrow")

    def draw_fixed_frame(self, *args):
        self.canvas.after.remove_group("fixed_frame")
        if self.task.fixed:
            with self.canvas.after:
                Color(0.5, 0.1, 0.3)
                Line(rectangle=[*self.pos, *self.size],
                     width=2,
                     group="fixed_frame")

    def set_gradient_colors(self, *args):
        self.gradient_colors = self.task.get_state_gradient_colors()

        begin_gradient_colors = self.gradient_colors[0]
        durations_acc = 0
        for i, element in enumerate(self.ids.layout.children[::-1]):
            if isinstance(element, TaskSpanElement):
                durations_acc += self.durations_span[i]
                t = durations_acc / self.task.duration.get_duration()
                end_gradient_color = list(
                    (1 - t) * np.array(self.gradient_colors[0]) +
                    t * np.array(self.gradient_colors[1]))
                element.gradient_colors = [
                    begin_gradient_colors, end_gradient_color
                ]
                begin_gradient_colors = end_gradient_color

    def on_touch_down(self, touch):
        if touch.is_double_tap and self.collide_point(*touch.pos):
            content = TaskTreatmentDialog(task=self.task)

            def on_validate(*args):
                try:
                    self.task.duration.add_duration(
                        int(content.ids.prolongation_field.text), content.unit)
                    self.task.update_state()
                    self.build()
                except:
                    if not (self.task.fixed or self.task.state == "done"):
                        toast("Invalid prolongation value")
                sheetview.dismiss()

            def on_done(*args):
                if self.task.state == "done":
                    self.task.set_undone()
                else:
                    self.task.set_done()
                sheetview.dismiss()

            def on_fix(*args):
                self.task.fixed = not self.task.fixed
                sheetview.dismiss()

            content.ids.done_button.bind(on_release=on_done)
            content.ids.fix_button.bind(on_release=on_fix)

            sheetview = DialogSheetView(
                title='Task treatment',
                content=content,
                on_validate=on_validate,
                on_cancel=lambda x: sheetview.dismiss(),
                size_hint=(0.8, None),
                height=200)

            sheetview.open()
            return True
        else:
            return super().on_touch_down(touch)


class CircleIndex(BoxLayout):
    index = StringProperty()
    text_color = ColorProperty()
    bg_color = ColorProperty()


class SquareIndex(BoxLayout):
    index = StringProperty()
    text_color = ColorProperty()
    bg_color = ColorProperty()


class Link(FloatLayout):
    begin = ObjectProperty()
    end = ObjectProperty()

    color = ColorProperty((0.0, 0.0, 0.0, 1))
    arrow_length = NumericProperty(dp(16))
    arrow_angle = NumericProperty(40)
    line_width = NumericProperty(1.5)
    bezier_distance = NumericProperty(200)
    margin = NumericProperty(dp(6))

    orientation_x = NumericProperty(1)
    orientation_y = NumericProperty(0)

    begin_margin = NumericProperty(dp(32))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Clock.schedule_once(self.setup)

    def setup(self, *args):
        self.begin.bind(pos=self.draw_link, size=self.draw_link)
        self.end.bind(pos=self.draw_link, size=self.draw_link)
        self.draw_link()

    def _rotate(self, alpha, x, y, cx, cy):
        return (x - cx) * np.cos(alpha) - (y - cy) * np.sin(alpha) + cx, (
            x - cx) * np.sin(alpha) + (y - cy) * np.cos(alpha) + cy

    def draw_link(self, *args):
        self.canvas.before.clear()

        x1, y1 = self.begin.pos
        x2, y2 = self.end.pos

        w1, h1 = self.begin.size
        w2, h2 = self.end.size

        # Compute best orientation
        if y2 > y1 + h1:
            self.orientation_x = 0
            self.orientation_y = 1
        elif y2 + h2 < y1:
            self.orientation_x = 0
            self.orientation_y = -1
        else:
            if x2 > x1 + h1:
                self.orientation_x = 1
            else:
                self.orientation_x = -1

            self.orientation_y = 0

        # Get center coords of the corresponding side
        if self.orientation_x == 1:
            x1 = x1 + w1
        elif self.orientation_x == 0:
            x1 = x1 + w1 / 2
            x2 = x2 + w2 / 2
        elif self.orientation_x == -1:
            x2 = x2 + w2

        if self.orientation_y == 1:
            y1 = y1 + h1
        elif self.orientation_y == 0:
            y1 = y1 + h1 / 2
            y2 = y2 + h2 / 2
        elif self.orientation_y == -1:
            y2 = y2 + h2

        # Adpat bezier_distance to widget's distance
        if self.orientation_x != 0:
            self.bezier_distance = abs(x1 - x2) / 4
        else:
            self.bezier_distance = abs(y1 - y2) / 4

        x_mid, y_mid = (x1 + x2) / 2, (y1 + y2) / 2

        # Rotation angle to almost align arrow with line
        alpha = np.arctan2(y1 - y2, x1 - x2)
        x_arrow = x_mid + self.arrow_length * np.cos(
            self.arrow_angle * np.pi / 180)
        y_arrow = y_mid + self.arrow_length * np.sin(
            self.arrow_angle * np.pi / 180)

        self.canvas.before.add(Color(*self.color))
        # Link
        self.canvas.before.add(
            Line(width=self.line_width,
                 bezier=(x1, y1,
                         x1 + self.bezier_distance * self.orientation_x,
                         y1 + self.bezier_distance * self.orientation_y,
                         x2 - self.bezier_distance * self.orientation_x, y2 -
                         self.bezier_distance * self.orientation_y, x2, y2)))
        # Arrow
        self.canvas.before.add(
            Line(width=self.line_width,
                 points=[
                     *self._rotate(alpha, x_arrow, y_arrow, x_mid, y_mid),
                     x_mid, y_mid, *self._rotate(
                         alpha, x_arrow, 2 * y_mid - y_arrow, x_mid, y_mid)
                 ],
                 joint="miter",
                 cap="square"))


class DuplicateProjectDialogContent(BoxLayout):
    pass


class ProjectListItem(OneLineAvatarIconListItem, RectangularRippleBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()

        self.menu = MDDropdownMenu(
            caller=self.ids.edit_button,
            items=[{
                "text": "Delete",
                "viewclass": "OneLineListItem",
                "on_release": self.delete_callback,
            }, {
                "text": "Duplicate",
                "viewclass": "OneLineListItem",
                "on_release": self.duplicate_callback,
            }],
            width_mult=3,
        )

        self.ids.edit_button.bind(on_release=lambda x: self.menu.open())

    def delete_callback(self):
        self.app.manager.delete(self.text)
        self.app.screen_manager.get_screen(
            "projects_list_screen").load_file_list()
        self.menu.dismiss()

    def duplicate_callback(self):
        content = DuplicateProjectDialogContent()

        def duplicate_file(*args):
            self.app.manager.duplicate(self.text, content.ids.name_field.text)
            self.app.screen_manager.get_screen(
                "projects_list_screen").load_file_list()
            sheetview.dismiss()

        sheetview = DialogSheetView(title='Duplicate the project',
                                    content=content,
                                    on_validate=duplicate_file,
                                    on_cancel=lambda x: sheetview.dismiss(),
                                    size_hint=(None, None),
                                    size=(500, 150))
        self.menu.dismiss()
        sheetview.open()


class RightBottomFloatingButton(MDFloatingActionButton):
    margin = NumericProperty(sp(12))


class ScrollingGridLayout(ScrollView):
    def add_widget(self, widget, index=0):
        if isinstance(widget, MDGridLayout):
            super().add_widget(widget)
        else:
            self.scroll_lay.add_widget(widget, index)

    def remove_widget(self, widget):
        self.scroll_lay.remove_widget(widget)


class RightIconButton(IRightBodyTouch, MDIconButton):
    pass
