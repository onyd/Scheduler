from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.metrics import sp
from functools import partial

from kivy.properties import BooleanProperty, NumericProperty, ReferenceListProperty, ColorProperty
from kivy.graphics import Line, Color


class AntiCollisionObject:
    pass


class DiscreteDragBehavior(object):
    drag_distance = NumericProperty(6)
    do_drag_x = BooleanProperty(True)
    do_drag_y = BooleanProperty(True)
    x_step = NumericProperty(10)
    y_step = NumericProperty(10)

    drag_rect_x = NumericProperty(0)
    drag_rect_y = NumericProperty(0)
    drag_rect_width = NumericProperty(100)
    drag_rect_height = NumericProperty(100)

    min_x = NumericProperty()
    max_x = NumericProperty()
    min_y = NumericProperty()
    max_y = NumericProperty()

    drag_rectangle = ReferenceListProperty(drag_rect_x, drag_rect_y,
                                           drag_rect_width, drag_rect_height)
    drag_boundaries = ReferenceListProperty(min_x, max_x, min_y, max_y)

    def __init__(self, **kwargs):
        self._drag_touch = None
        self._move_data = {"dx": 0.0, "dy": 0.0}

        super(DiscreteDragBehavior, self).__init__(**kwargs)

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def on_touch_down(self, touch):
        xx, yy, w, h = self.drag_rectangle
        x, y = touch.pos

        if not self.collide_point(x, y):
            touch.ud[self._get_uid('svavoid')] = True
            return super(DiscreteDragBehavior, self).on_touch_down(touch)

        if self._drag_touch or ('button' in touch.profile and
                                touch.button.startswith('scroll')) or\
                not ((xx < x <= xx + w) and (yy < y <= yy + h)):
            return super(DiscreteDragBehavior, self).on_touch_down(touch)

        # no mouse scrolling and object is selected, so the user is going to drag with this touch.
        touch.grab(self)
        uid = self._get_uid()
        touch.ud[uid] = {'mode': 'unknown', 'dx': 0, 'dy': 0}
        self._drag_touch = touch
        self._move_data = {"dx": 0.0, "dy": 0.0}
        return True

    def on_touch_move(self, touch):
        print("move")
        if self._get_uid('svavoid') in touch.ud or\
                (self._drag_touch is not None and self._drag_touch is not touch):
            return super(DiscreteDragBehavior, self).on_touch_move(touch) or\
                self._get_uid() in touch.ud

        if touch.grab_current is not self:
            return True

        # Get touch mode
        uid = self._get_uid()
        ud = touch.ud[uid]
        mode = ud['mode']
        if mode == 'unknown':
            ud['dx'] += abs(touch.dx)
            ud['dy'] += abs(touch.dy)
            if ud['dx'] > sp(self.drag_distance) or ud['dy'] > sp(
                    self.drag_distance):
                mode = 'drag'
            ud['mode'] = mode

        # Drag
        if mode == 'drag':
            self._move_data["dx"] += touch.dx
            self._move_data["dy"] += touch.dy

            # Do one step when value get greater than the corresponding step
            while self.do_drag_x and self.min_x <= self.x <= self.max_x and abs(
                    self._move_data["dx"]) >= self.x_step:
                if self._move_data["dx"] >= 0:
                    self._move_data["dx"] -= self.x_step
                    self.x += self.x_step
                else:
                    self._move_data["dx"] += self.x_step
                    self.x -= self.x_step
            while self.do_drag_y and abs(self._move_data["dy"]) >= self.x_step:
                if self._move_data["dy"] >= 0:
                    self._move_data["dy"] -= self.x_step
                    self.x += self.x_step
                else:
                    self._move_data["dy"] += self.x_step
                    self.x -= self.x_step

            # Check boundaries
            if self.x > self.max_x:
                self.x = self.max_x
            elif self.x < self.min_x:
                self.x = self.min_x
            if self.y > self.max_y:
                self.y = self.max_y
            elif self.y < self.min_y:
                self.y = self.min_y

        return True

    def on_touch_up(self, touch):
        x, y = touch.pos
        uid = self._get_uid()
        if uid in touch.ud:
            ud = touch.ud[uid]

            if self.collide_point(x, y) and ud['mode'] != 'drag':
                return True

            # avoid the drag if touch doesn't correspond
            if self._get_uid('svavoid') in touch.ud:
                return super(DiscreteDragBehavior, self).on_touch_up(touch)

            if self._drag_touch and self in [x() for x in touch.grab_list]:
                touch.ungrab(self)
                self._drag_touch = None
                ud = touch.ud[self._get_uid()]
                if ud['mode'] == 'unknown':
                    super(DiscreteDragBehavior, self).on_touch_down(touch)
                    Clock.schedule_once(partial(self._do_touch_up, touch), .1)
            else:
                if self._drag_touch is not touch:
                    super(DiscreteDragBehavior, self).on_touch_up(touch)

        return self._get_uid() in touch.ud

    def _do_touch_up(self, touch, *largs):
        super(DiscreteDragBehavior, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(DiscreteDragBehavior, self).on_touch_up(touch)
        touch.grab_current = None


class DiscreteMovableBehavior(object):
    buttons_width = NumericProperty()
    buttons_height = NumericProperty()
    line_width = NumericProperty(2)
    margin = NumericProperty(3)
    button_size = ReferenceListProperty(buttons_width, buttons_height)
    cursor_position = NumericProperty(0)
    do_center_button = BooleanProperty(False)
    do_move_x = BooleanProperty(True)

    min_cursor_position = NumericProperty(0)
    max_cursor_position = NumericProperty(float("inf"))

    x_step = NumericProperty(10)
    x_offset = NumericProperty(0)

    cursor_step = NumericProperty(1)

    selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(DiscreteMovableBehavior, self).__init__(**kwargs)
        self.register_event_type('on_move_left')
        self.register_event_type('on_move_right')

        self.show_y = None
        self.bind(selected=self.update_buttons, do_move_x=self.update_buttons)

    def on_move_left(self, step):
        pass

    def on_move_right(self, step):
        pass

    def set_cursor(self, cursor_position):
        self.cursor_position = cursor_position

    def draw_button(self, x, y, right):
        if right:
            x_target = x + self.buttons_width - self.margin
            y_target = y + self.buttons_height / 2.0
            x_up = x + self.margin
            y_up = y + self.buttons_height - self.margin
            x_bot = x + self.margin
            y_bot = y + self.margin
        else:
            x_target = x + self.margin
            y_target = y + self.buttons_height / 2.0
            x_up = x + self.buttons_width - self.margin
            y_up = y + self.buttons_height - self.margin
            x_bot = x + self.buttons_width - self.margin
            y_bot = y + self.margin

        with self.canvas.after:
            Color(0.0, 0.0, 0.0)
            # Arrow
            Line(width=self.line_width,
                 points=[x_up, y_up, x_target, y_target, x_bot, y_bot],
                 joint="miter",
                 cap="square",
                 group="button")

            # Button box
            Line(width=self.line_width,
                 rectangle=[x, y, self.buttons_width, self.buttons_height],
                 joint="miter",
                 cap="square",
                 group="button")

    def update_buttons(self, *args):
        self.canvas.after.remove_group("button")

        if not self.do_move_x:
            return
        if self.selected:
            if self.cursor_position < self.max_cursor_position:
                self.draw_button(self.x + self.width + self.margin,
                                 self.show_y,
                                 right=True)
            if self.cursor_position > self.min_cursor_position:
                self.draw_button(self.x - self.buttons_width - self.margin,
                                 self.show_y,
                                 right=False)

    def on_touch_down(self, touch):
        if touch.is_double_tap or not self.do_move_x or (
                'button' in touch.profile
                and touch.button.startswith('scroll')):
            return super(DiscreteMovableBehavior, self).on_touch_down(touch)

        x, y = touch.pos
        if self.selected and self.collide_button(x, y, right=True):
            return True
        elif self.selected and self.collide_button(x, y, right=False):
            return True

        if not self.collide_point(*touch.pos):
            self.selected = False
            return super(DiscreteMovableBehavior, self).on_touch_down(touch)

        return True

    def collide_button(self, x, y, right):
        if right:
            button_x = self.x + self.width + self.margin
            button_y = self.show_y
        else:
            button_x = self.x - self.buttons_width - self.margin
            button_y = self.show_y
        return button_x <= x <= button_x + self.buttons_width and button_y <= y <= button_y + self.buttons_height

    def on_touch_up(self, touch):
        if touch.is_double_tap or not self.do_move_x or (
                'button' in touch.profile
                and touch.button.startswith('scroll')):
            self.selected = False
            return super(DiscreteMovableBehavior, self).on_touch_up(touch)

        x, y = touch.pos
        if not self.selected:
            if self.collide_point(x, y):
                if self.do_center_button:
                    self.show_y = self.center_y - self.buttons_height / 2.0
                else:
                    self.show_y = y - self.buttons_height / 2.0
                self.selected = True
                return True
            else:
                return super(DiscreteMovableBehavior, self).on_touch_up(touch)
        else:
            if self.collide_button(
                    x, y, right=True
            ) and self.cursor_position < self.max_cursor_position:
                self.dispatch("on_move_right", self.cursor_step)
                self.x += self.x_step
                self.cursor_position += self.cursor_step
                self.update_buttons()
                return True
            elif self.collide_button(
                    x, y, right=False
            ) and self.cursor_position > self.min_cursor_position:
                self.dispatch("on_move_left", self.cursor_step)
                self.x -= self.x_step
                self.cursor_position -= self.cursor_step
                self.update_buttons()
                return True

        return super(DiscreteMovableBehavior, self).on_touch_up(touch)


class SelectDragBehavior(object):
    """This class is an adaptation of the DragBehavior class from kivy with selection feature"""
    drag_distance = NumericProperty(6)

    drag_rect_x = NumericProperty(0)
    drag_rect_y = NumericProperty(0)
    drag_rect_width = NumericProperty(100)
    drag_rect_height = NumericProperty(100)

    drag_rectangle = ReferenceListProperty(drag_rect_x, drag_rect_y,
                                           drag_rect_width, drag_rect_height)
    collision_margin = NumericProperty(3)
    selection_frame_color = ColorProperty((0., 0., 0., 1.))

    def __init__(self, **kwargs):
        self._drag_touch = None
        self.selected = False
        self.sdb_enabled = True

        super(SelectDragBehavior, self).__init__(**kwargs)

        self.bind(size=lambda *args: self.draw_selection_box())

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def select(self):
        self.selected = True
        self.draw_selection_box()

    def unselect(self):
        self.selected = False
        self.canvas.remove_group("selection_box")
        self._drag_touch = None

    def draw_selection_box(self, line_width=4):
        if not self.selected:
            return
        self.canvas.remove_group("selection_box")
        with self.canvas:
            Color(*self.selection_frame_color)
            Line(rectangle=(self.x - line_width, self.y - line_width,
                            self.width + 2 * line_width, self.height + 2 * line_width),
                 width=line_width,
                 group="selection_box")

    def handle_collisions(self, dx=0, dy=0):
        new_dx, new_dy = dx, dy
        for child in self.parent.children:
            x, y = self.x + dx, self.y + dy

            # Collision test
            if child is not self and isinstance(
                    child, AntiCollisionObject) and (
                        x + self.width + self.collision_margin > child.x
                        and x - self.collision_margin < child.right
                        and y + self.height + self.collision_margin > child.y
                        and y - self.collision_margin < child.top):
                # Compute distance bl relatively to bottom left corner and tr the top right one
                bl_x = abs(x - child.x - child.width)
                bl_y = abs(y - child.y - child.height)
                tr_x = abs(child.x - x - self.width)
                tr_y = abs(child.y - y - self.height)

                d_min = min(bl_x, bl_y, tr_x, tr_y)
                if d_min == bl_x:
                    self.x = child.x + child.width + self.collision_margin
                    new_dx = 0
                elif d_min == bl_y:
                    self.y = child.y + child.height + self.collision_margin
                    new_dy = 0
                elif d_min == tr_x:
                    self.right = child.x - self.collision_margin
                    new_dx = 0
                else:
                    self.top = child.y - self.collision_margin
                    new_dy = 0

        return new_dx, new_dy

    def on_touch_down(self, touch):
        if not self.sdb_enabled:
            return super(SelectDragBehavior, self).on_touch_down(touch)

        xx, yy, w, h = self.drag_rectangle
        x, y = touch.pos

        if not self.collide_point(x, y):
            self.unselect()
            touch.ud[self._get_uid('svavoid')] = True
            return super(SelectDragBehavior, self).on_touch_down(touch)

        if self._drag_touch or ('button' in touch.profile and
                                touch.button.startswith('scroll')) or\
                not ((xx < x <= xx + w) and (yy < y <= yy + h)):
            return super(SelectDragBehavior, self).on_touch_down(touch)

        # no mouse scrolling and object is selected, so the user is going to drag with this touch.
        touch.grab(self)
        uid = self._get_uid()
        touch.ud[uid] = {'mode': 'unknown', 'dx': 0, 'dy': 0}

        # not selected so the user swipe to move in
        if not self.selected:
            return super(SelectDragBehavior, self).on_touch_down(touch)

        self._drag_touch = touch

        return True

    def on_touch_move(self, touch):
        # Avoid drag
        if not self.sdb_enabled:
            return super(SelectDragBehavior, self).on_touch_move(touch)

        if self._get_uid('svavoid') in touch.ud or\
                (self._drag_touch is not None and self._drag_touch is not touch) or not self.sdb_enabled:
            return super(SelectDragBehavior, self).on_touch_move(touch) or\
                self._get_uid() in touch.ud

        if touch.grab_current is not self:
            return True

        # Get touch mode
        uid = self._get_uid()
        ud = touch.ud[uid]
        mode = ud['mode']
        if mode == 'unknown':
            ud['dx'] += abs(touch.dx)
            ud['dy'] += abs(touch.dy)
            if ud['dx'] > sp(self.drag_distance) or ud['dy'] > sp(
                    self.drag_distance):
                mode = 'drag'
            ud['mode'] = mode

        # Drag
        if mode == 'drag' and self.selected:
            dx, dy = self.handle_collisions(touch.dx, touch.dy)
            self.x += dx
            self.y += dy

        self.draw_selection_box()
        return True

    def on_touch_up(self, touch):
        if not self.sdb_enabled:
            return super(SelectDragBehavior, self).on_touch_up(touch)

        x, y = touch.pos
        uid = self._get_uid()
        if uid in touch.ud:
            ud = touch.ud[uid]

            if self.collide_point(
                    x, y) and not self.selected and ud['mode'] != 'drag':
                self.select()
                return True

            self.handle_collisions()
            self.draw_selection_box()

            # avoid the drag if touch doesn't correspond
            if self._get_uid('svavoid') in touch.ud:
                return super(SelectDragBehavior, self).on_touch_up(touch)

            if self._drag_touch and self in [x() for x in touch.grab_list]:
                touch.ungrab(self)
                self._drag_touch = None
                ud = touch.ud[self._get_uid()]
                if ud['mode'] == 'unknown':
                    super(SelectDragBehavior, self).on_touch_down(touch)
                    Clock.schedule_once(partial(self._do_touch_up, touch), .1)
            else:
                if self._drag_touch is not touch:
                    super(SelectDragBehavior, self).on_touch_up(touch)

        return self._get_uid() in touch.ud

    def _do_touch_up(self, touch, *largs):
        super(SelectDragBehavior, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(SelectDragBehavior, self).on_touch_up(touch)
        touch.grab_current = None
