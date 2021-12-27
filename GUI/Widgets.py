from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivymd.toast.kivytoast.kivytoast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
import numpy as np
from math import ceil
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
from kivy.graphics import Color, Line, Triangle
from kivy.uix.modalview import ModalView

from kivy.properties import (StringProperty, ColorProperty, NumericProperty,
                             ListProperty, ObjectProperty, BooleanProperty,
                             ReferenceListProperty)

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.factory import Factory
from kivy.compat import string_types
from kivy.uix.recycleview.views import RecycleDataViewBehavior

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
from kivymd.uix.chip import MDChip
from kivymd.uix.menu import MDDropdownMenu
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
    bold_line = BooleanProperty(True)
    bold_width_multiplier = NumericProperty(2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.draw_grid)

    def draw_grid(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:

            Color(0.6, 0.6, 0.6, 1)
            for i in range(0, int(self.width) + 1, int(self.square_width)):
                # Vertical
                Line(
                    points=[
                        self.x + i, self.y, self.x + i, self.y + self.height
                    ],
                    width=self.line_width,
                )

            for j in range(0, int(self.height) + 1, int(self.square_height)):
                # Horizontal
                Line(
                    points=[
                        self.x, self.y + j, self.x + self.width, self.y + j
                    ],
                    width=self.line_width,
                )

            # Bigger
            if self.bold_line:
                Color(0.3, 0.3, 0.3, 1)
                for k in range(0, int(self.width) + 1, int(self.width / 3)):
                    # Vertical
                    Line(
                        width=self.bold_width_multiplier * self.line_width,
                        points=[
                            self.x + k, self.y, self.x + k,
                            self.y + self.height
                        ],
                    )
                for k in range(0, int(self.height) + 1, int(self.height / 3)):
                    # Horizontal
                    Line(
                        width=self.bold_width_multiplier * self.line_width,
                        points=[
                            self.x, self.y + k, self.x + self.width, self.y + k
                        ],
                    )


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
        self.tooltip_txt += "Begin: " + str(
            self.task.get_begin_day()) + " day" + "\n"
        self.tooltip_txt += "End: " + str(
            self.task.get_end_day()) + " day" + "\n"
        self.tooltip_txt += "Duration: " + str(
            round(self.task.get_duration(self.task.unit),
                  2)) + " " + self.task.unit + "\n"
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
            self.draw_selection_box()

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


class Task(Component):
    name = StringProperty("New")
    resource = NumericProperty(1)
    duration = NumericProperty(1)
    unit = StringProperty("hour")
    begin_time = NumericProperty()
    max_end_day = NumericProperty(allownone=True)
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
                 unit="hour",
                 begin_time=-1,
                 max_end_day=None,
                 description="",
                 activated=True,
                 state="pending",
                 fixed=False,
                 **kwargs):
        super().__init__(**kwargs)

        self.name = name
        self.resource = resource
        Clock.schedule_once(
            lambda x: self.set_duration(duration, "hour", force=True))
        self.unit = unit
        self.begin_time = begin_time
        self.max_end_day = max_end_day
        self.description = description
        self.activated = activated
        self.state = state
        self.prev_state = self.state
        self.fixed = fixed

        Clock.schedule_once(self.setup)

    def setup(self, *args):
        self.bind(activated=self.set_gradient_colors,
                  state=self.update_treatment,
                  fixed=self.draw_fixed_frame)
        self.bind(pos=lambda *args: self.app.manager.set_saved(False),
                  name=lambda *args: self.app.manager.set_saved(False),
                  resource=lambda *args: self.app.manager.set_saved(False),
                  duration=lambda *args: self.app.manager.set_saved(False),
                  unit=lambda *args: self.app.manager.set_saved(False),
                  description=lambda *args: self.app.manager.set_saved(False),
                  activated=lambda *args: self.app.manager.set_saved(False),
                  state=lambda *args: self.app.manager.set_saved(False),
                  fixed=lambda *args: self.app.manager.set_saved(False),
                  max_end_day=lambda *args: self.app.manager.set_saved(False),
                  assignments=lambda *args: self.app.manager.set_saved(False))
        self.bind(resource=self.update_planning_state,
                  duration=self.update_planning_state,
                  max_end_day=self.update_planning_state,
                  activated=self.update_planning_state,
                  state=self.update_planning_state)
        self.ids.duration_text_field.bind(text=self.update_duration)
        self.ids.resource_text_field.bind(text=self.update_resource)
        self.ids.max_end_day_text_field.bind(text=self.update_max_end_day)
        self.set_gradient_colors()
        self.draw_fixed_frame()

    def update_duration(self, instance, value):
        if value != "":
            self.set_duration(int(value), self.unit)

    def update_resource(self, instance, value):
        if value != "":
            self.resource = int(value)

    def update_max_end_day(self, instance, value):
        if value != "":
            self.max_end_day = int(value)

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

    def update_state(self, time):
        if self.state != "done":
            self.set_undone(time)

    def draw_fixed_frame(self, *args):
        self.canvas.after.remove_group("fixed_frame")
        if self.fixed:
            with self.canvas.after:
                Color(0.0, 0.0, 0.0)
                Line(rectangle=[*self.pos, *self.size],
                     width=2,
                     group="fixed_frame")

    def set_done(self):
        if self.get_begin_day() > self.app.manager.get_current_time("day") + 1:
            toast("The task cannot be done before it has begun")
            return
        if self.app.manager.has_undone_anterior_tasks(self):
            toast(
                "This task can't be set done because there is at least one undone anterior task"
            )
            return

        end_day = self.get_end_day()
        current_day = self.app.manager.get_current_time("day") + 1
        if end_day > current_day:
            self.set_unit("hour")
            self.set_duration(self.get_duration("hour") -
                              self.get_duration_between(
                                  current_day, end_day, dst_unit="hour"),
                              unit="hour")
        self.state = "done"

    def set_undone(self, day):
        if self.is_in_progress_for_day(day):
            self.state = "progress"
        elif self.get_begin_time('day') > day:
            self.state = "pending"
        elif self.get_end_time('day') <= day:
            self.state = "waiting_for_treatment"

    def update_planning_state(self, *args):
        self.app.manager.get_planning_screen().update_planning_state()

    def callback_on(self, *args):
        self.activated = True

    def callback_off(self, *args):
        self.activated = False

    def set_unit(self, unit):
        if self.fixed:
            return

        self.unit = unit

    def on_touch_down(self, touch):
        if touch.is_double_tap and self.collide_point(*touch.pos):
            description_field = TextInput(multiline=True)
            description_field.text = self.description

            def on_validate(*args):
                self.description = description_field.text
                sheetview.dismiss()

            sheetview = DialogSheetView(
                title='Description',
                content=description_field,
                on_validate=on_validate,
                on_cancel=lambda x: sheetview.dismiss(),
                size_hint=(0.8, 0.8))

            sheetview.open()
            return True
        else:
            return super().on_touch_down(touch)

    def get_begin_time(self, unit="day"):
        if unit == "day":
            return self.begin_time / self.app.manager.get_day_duration()
        elif unit == "hour":
            return self.begin_time

    def set_begin_time(self, begin_time, unit="day", force=False):
        if not force and (self.fixed or self.state == "done"):
            return

        if unit == "day":
            self.begin_time = begin_time * self.app.manager.get_day_duration()
        elif unit == "hour":
            self.begin_time = begin_time

    def get_duration(self, unit="day"):
        if unit == "hour":
            return self.duration
        elif unit == "day":
            return self.duration / self.app.manager.get_day_duration()

    def set_duration(self, duration, unit="day", force=False):
        if not force and (self.fixed or self.state == "done"):
            return

        if unit == "hour":
            self.duration = int(duration)
        elif unit == "day":
            self.duration = int(duration * self.app.manager.get_day_duration())

    def get_end_time(self, unit="day"):
        return self.get_begin_time(unit) + self.get_duration(unit)

    def get_max_end_time(self, unit="day"):
        if self.max_end_day is not None:
            if unit == "hour":
                return self.max_end_time * self.app.manager.get_day_duration()
            elif unit == "day":
                return self.max_end_time

    def is_in_progress_for_day(self, day):
        return int(self.get_begin_time("day")) <= day < ceil(
            self.get_end_time("day"))

    def do_continue(self, day):
        return day < int(ceil(self.get_end_time("day"))) - 1

    def get_duration_between(self, begin_day, end_day, dst_unit="hour"):
        begin_time = self.get_begin_time("hour")
        end_time = self.get_end_time("hour")
        begin_day *= self.app.manager.get_day_duration()
        end_day *= self.app.manager.get_day_duration()
        if begin_day < begin_time:
            begin_day = begin_time
        if end_day > end_time:
            end_day = end_time

        if dst_unit == "hour":
            return max(0, end_day - begin_day)

        return max(0,
                   end_day - begin_day) / self.app.manager.get_day_duration()

    def get_duration_for_day(self, day):
        return self.get_duration_between(day, day + 1, dst_unit="hour")

    def get_begin_day(self):
        return int(self.get_begin_time("day")) + 1

    def get_end_day(self):
        return int(ceil(self.get_end_time("day")))

    def get_progression(self):
        current_day = self.app.manager.get_current_time("day")
        return self.get_duration_between(
            self.get_begin_day() - 1, current_day,
            dst_unit="hour") / self.get_duration(unit="hour") * 100

    def get_consumed_resources(self):
        return self.resource

    def get_name(self):
        return self.name

    def to_dict(self, **kwargs):
        return super().to_dict(duration=self.duration,
                               resource=self.resource,
                               begin_time=self.begin_time,
                               max_end_day=self.max_end_day,
                               unit=self.unit,
                               name=self.name,
                               description=self.description,
                               activated=self.activated,
                               state=self.state,
                               fixed=self.fixed,
                               assignments=self.assignments,
                               **kwargs)


class StartTask(Component):
    def get_begin_time(self, unit="day"):
        return 0

    def get_duration(self, unit="day"):
        return 0


class EndTask(Component):
    begin_time = NumericProperty()
    unit = StringProperty("day")

    def get_begin_time(self, unit="day"):
        if unit == "day":
            return self.begin_time / self.app.manager.get_day_duration()
        else:
            return self.begin_time

    def set_begin_time(self, begin_time, unit="day"):
        if unit == "day":
            self.begin_time = begin_time * self.app.manager.get_day_duration()
        else:
            self.begin_time = begin_time

    def get_duration(self, unit="day"):
        return 0

    def to_dict(self, **kwargs):
        return super().to_dict(begin_time=self.begin_time,
                               unit=self.unit,
                               **kwargs)


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


class ScrollablePlanning(FloatLayout):
    chunk_size = NumericProperty()
    margin = NumericProperty()
    n_rows = NumericProperty(1)
    n_cols = NumericProperty(1)
    tasks_width = NumericProperty()
    tasks_height = NumericProperty(10)
    planning_unit = StringProperty("day")
    n_waiting_for_treatment = NumericProperty(0)

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

        self.bind(n_waiting_for_treatment=self.update_planning_state)
        self.app.manager.planning.bind(planning_state=self.update_cursor,
                                       horizons=self.update_cursor)

    def update_cursor(self, *args):
        if self.cursor:
            self.cursor.max_cursor_position = len(
                self.app.manager.get_horizons("day"))

    def update_planning_state(self, *args):
        if self.n_waiting_for_treatment == 0:
            self.app.manager.set_planning_state("to_validate")
        else:
            self.app.manager.set_planning_state("waiting_for_treatment")

    def set_cursor(self, time):
        self.cursor = TimeCursor(size_hint=(None, None),
                                 gradient_colors=[(0.8, 0.2, 0.1, 0.8),
                                                  (0.2, 0.2, 0.4, 0.8)],
                                 size=(self.chunk_size,
                                       self.ids.planning_grid.height),
                                 buttons_width=self.chunk_size,
                                 buttons_height=self.chunk_size,
                                 x_step=self.chunk_size,
                                 pos_hint={'top': 1})
        self.update_cursor()

        # Add the cusor in the backgroud
        children = self.ids.planning_layout.children.copy()
        self.ids.planning_layout.clear_widgets()
        self.ids.planning_layout.add_widget(self.cursor)
        for child in children:
            self.ids.planning_layout.add_widget(child)

        self.cursor.set_cursor(time)
        self.cursor.bind(cursor_position=lambda _, value: self.app.manager.
                         set_current_time(value))
        self.cursor.bind(cursor_position=lambda *args: self.app.manager.
                         get_planning_screen().update_planning_state())
        self.ids.planning_grid.bind(height=self.cursor.setter('height'))

    def set_times(self, end):
        self.ids.time_layout.clear_widgets()
        for i in range(1, end + 1):
            time_index = CircleIndex(index=f'{i}',
                                     size=(self.chunk_size - self.margin,
                                           self.chunk_size - self.margin),
                                     pos_hint={"center_y": 0.5})
            self.ids.time_layout.add_widget(time_index)
        self.n_cols = end

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

    def add_task_span(self, i, cursor_position, do_continue, movable,
                      planning_unit, task):
        task_span = TaskSpan(i=i,
                             cursor_position=cursor_position,
                             n=self.n_rows,
                             planning_unit=planning_unit,
                             square_width=self.chunk_size,
                             square_height=self.tasks_height,
                             task=task,
                             do_continue=do_continue,
                             do_move_x=movable)
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
        if self.cursor:
            self.ids.planning_layout.remove_widget(self.cursor)
        self.planning_unit = unit

        if self.planning_unit == "day":
            self.set_times(self.app.manager.get_horizon('day'))

            # Build the planning
            for i, task in enumerate(self.app.manager.get_tasks()):
                self.add_task_span(
                    i=i + 1,
                    cursor_position=task.get_begin_time("hour"),
                    do_continue=False,
                    movable=not (task.fixed or task.state == "done"),
                    planning_unit=self.planning_unit,
                    task=task)

            self.set_cursor(self.app.manager.get_current_time())
        else:
            self.set_times(self.app.manager.get_day_duration())

            # Build the planning
            current_time_hour = self.app.manager.get_current_time("hour")
            current_time_day = self.app.manager.get_current_time("day")
            for i, task in enumerate(self.app.manager.get_tasks()):
                begin_time_hour = task.get_begin_time("hour")
                if task.is_in_progress_for_day(current_time_day):
                    self.add_task_span(
                        i=i + 1,
                        cursor_position=max(
                            0, begin_time_hour - current_time_hour),
                        do_continue=task.do_continue(current_time_day),
                        movable=False,
                        planning_unit=self.planning_unit,
                        task=task)


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
                text=
                f"Do you want to remove the assignement {self.text} from task {self.assignement_list.task.get_name()} ?"
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
        horizon_day = self.app.manager.get_horizon("day")
        horizons = self.app.manager.get_horizons("hour")
        current_time = self.app.manager.get_current_time("day")
        max_t = min(len(horizons) + 1, current_time + 2)
        X = np.arange(0, horizon_day + 1)
        x = np.arange(0, max_t)
        y = np.array([horizons[0]] +
                     [horizon for horizon in horizons[:max_t - 1]])
        d_horizons = np.array([0] + [y[i] - y[i - 1] for i in range(1, max_t)])
        over_estimated_mask = d_horizons < 0
        under_estimated_mask = d_horizons > 0
        y_lim = max(y)

        for task in self.app.manager.get_tasks():
            end_day = task.get_end_day()
            if end_day <= current_time:
                duration = task.get_duration("hour")
                begin_day = task.get_begin_day()

                # Average the duration of the task over its execution
                duration_acc = 0
                for t in range(begin_day, end_day):
                    duration_acc += task.get_duration_for_day(t)
                    y[t] -= duration_acc
                for t in range(end_day, len(y)):
                    y[t] -= duration
        reg = LinearRegression().fit(np.reshape(x, (-1, 1)), y)

        self.fig, ax = plt.subplots()
        ax.bar(x[:-1], y[:-1], color='blue')
        ax.bar([x[-1]], [y[-1]], color='orange')
        ax.bar(x[under_estimated_mask],
               d_horizons[under_estimated_mask],
               color='red')
        ax.bar(x[over_estimated_mask],
               -d_horizons[over_estimated_mask],
               color='green')
        reg_line = ax.plot(X, [reg.coef_[0] * t + reg.intercept_ for t in X],
                           label='linear regression',
                           c='r')
        ax.set_ylabel("Remaining efforts (hour)")
        ax.set_xlabel("Days")
        ax.set_title("Burndown chart")
        ax.set_ylim([0, y_lim + 1])
        ax.set_xticks(X)
        ax.text(
            1.0,
            1.0,
            f'Velocity: {int(round(-reg.coef_[0]))} hour/day\nPlanned end day: {self.app.manager.get_planned_end_day()} day',
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
    unit = StringProperty()

    def set_unit(self, unit):
        self.unit = unit


class TimeCursor(DiscreteMovableBehavior, VerticalGradientRectangle):
    arrow_width = NumericProperty()


class TaskSpan(DiscreteMovableBehavior, HorizontalGradientRectangle,
               TaskTooltiped):
    i = NumericProperty()
    n = NumericProperty()
    spanning = NumericProperty()
    planning_unit = StringProperty()
    square_width = NumericProperty()
    square_height = NumericProperty()
    do_continue = BooleanProperty(False)
    task = ObjectProperty()
    compute_spanning = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = MDApp.get_running_app()

        Clock.schedule_once(self.setup)

    def setup(self, *args):
        self.set_gradient_colors()
        self.task.bind(state=self.set_gradient_colors,
                       description=self.setter('tooltip_txt'),
                       duration=self.update_spanning,
                       fixed=lambda instance, value: self.setter('do_move_x')
                       (instance, not value))
        self.task.bind(fixed=self.draw_fixed_frame,
                       duration=self.update_tooltip,
                       begin_time=self.update_tooltip)
        self.bind(do_continue=self.draw_continue_arrow,
                  cursor_position=lambda _, value: self.task.set_begin_time(
                      value, 'hour'))
        self.bind(cursor_position=lambda *args: self.task.update_state(
            self.app.manager.get_current_time()))
        self.update_spanning()
        self.update_tooltip()
        self.draw_continue_arrow()
        self.draw_fixed_frame()

    def update_spanning(self, *args):
        if self.planning_unit == "day":
            self.spanning = self.task.get_duration(self.planning_unit)
        else:
            self.spanning = self.task.get_duration_for_day(
                self.app.manager.get_current_time())
        self.max_cursor_position = self.app.manager.get_horizon(
            "hour") - self.spanning - 1

    def draw_continue_arrow(self, *args):
        self.canvas.after.remove_group("continue_arrow")
        if self.do_continue:
            with self.canvas.after:
                Color(0.0, 0.0, 0.0)
                Triangle(points=[
                    self.x + self.spanning * self.square_width, self.y,
                    self.x + self.spanning * self.square_width,
                    self.y + self.square_height,
                    self.x + (self.spanning + 1 / 2.0) * self.square_width,
                    self.y + self.square_height / 2.0
                ],
                         group="continue_arrow")

    def draw_fixed_frame(self, *args):
        self.canvas.after.remove_group("fixed_frame")
        if self.task.fixed:
            with self.canvas.after:
                Color(0.0, 0.0, 0.0)
                Line(rectangle=[*self.pos, *self.size],
                     width=2,
                     group="fixed_frame")

    def set_gradient_colors(self, *args):
        self.gradient_colors = self.task.get_state_gradient_colors()

    def on_touch_down(self, touch):
        if touch.is_double_tap and self.collide_point(*touch.pos):
            content = TaskTreatmentDialog(task=self.task, unit=self.task.unit)

            def on_validate(*args):
                self.task.set_unit(content.unit)
                try:
                    self.task.set_duration(
                        int(self.task.get_duration(content.unit)) +
                        int(content.ids.prolongation_field.text), content.unit)
                    self.task.update_state(self.app.manager.get_current_time())
                except:
                    if not (self.task.fixed or self.task.state == "done"):
                        toast("Invalid prolongation value")
                sheetview.dismiss()

            def on_done(*args):
                if self.task.state == "done":
                    self.task.set_undone(
                        self.app.manager.get_current_time("day"))
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