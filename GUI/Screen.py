from pathlib import Path
import os
import copy

from kivy.uix.screenmanager import Screen

from kivy.properties import ListProperty, ObjectProperty

from kivymd.app import MDApp
from kivymd.toast import toast

from GUI.Widgets import *
from Core.SchedulerSolver import SchedulerSolver
from Utils.FileManager import FileManager
from Utils.ImageConcatenator import ImageConcatenator


class ProjectsListScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.app = MDApp.get_running_app()

    def open_create_file_dialog(self, *args):
        """Called when a new file is being created, it asks the name, the capacity and save it with just the StartTask and EndTask pre inserted"""
        content = CreateProjectDialogContent()

        def create_file(*args):
            sheetview.dismiss()
            self.app.manager.create(content.ids.name_field.text,
                                    int(content.ids.capacity_field.text),
                                    int(content.ids.day_duration_field.text))
            self.load_file_list()

        sheetview = DialogSheetView(title='Create new project',
                                    content=content,
                                    on_validate=create_file,
                                    on_cancel=lambda x: sheetview.dismiss(),
                                    size_hint=(None, None),
                                    size=(500, 250))

        sheetview.open()

    def open_file(self, instance):
        self.app.manager.load(instance.text)
        self.app.change_screen("choose_editor_screen")

    def load_file_list(self, *args):
        """Load the available files:
        return the MDList with all available files as ListItem"""
        self.app.screen_manager.ids.file_list.clear_widgets()

        settings = self.app.settings
        path = Path(settings.get_paths()['save_path'])

        for file_name in os.listdir(path):
            if file_name.endswith('.json'):
                file = ProjectListItem(text=file_name[:-5])
                file.bind(on_release=self.open_file)
                self.app.screen_manager.ids.file_list.add_widget(file)

    def on_pre_enter(self, *args):
        self.app.tool_bar.right_action_items = []
        self.app.tool_bar.left_action_items = []

        Clock.schedule_once(self.load_file_list, 0.1)

    def on_leave(self, *args):
        self.menus = []
        self.app.screen_manager.ids.file_list.clear_widgets()
        return super().on_leave(*args)


class ChooseEditorScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.app = MDApp.get_running_app()

    def on_pre_enter(self):
        def go_back(*args):
            self.app.manager.unload()
            self.app.manager.quit('projects_list_screen')

        self.app.tool_bar.left_action_items = [['arrow-left', go_back]]
        self.app.tool_bar.right_action_items = []


class BacklogScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.app = MDApp.get_running_app()

    def on_pre_enter(self):
        self.app.tool_bar.left_action_items = [[
            'arrow-left',
            lambda x: self.app.manager.quit("choose_editor_screen")
        ]]

        self.app.tool_bar.right_action_items = [[
            'content-save', lambda x: self.app.manager.save()
        ]]

        backlog = Backlog()
        backlog.setup()
        self.add_widget(backlog)

    def on_leave(self, *args):
        self.clear_widgets()


class BurndownScreen(Screen):
    burndown_chart = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)

        self.app = MDApp.get_running_app()

    def on_pre_enter(self):
        self.app.tool_bar.left_action_items = [[
            'arrow-left',
            lambda x: self.app.manager.quit("choose_editor_screen")
        ]]

        self.app.tool_bar.right_action_items = [[
            'file-export', lambda x: self.burndown_chart.export_burndown(
                self.app.manager.get_planning_path(extension="_burndown.png"))
        ]]

        self.burndown_chart.setup()


class PlanningScreen(Screen):
    scrollable_planning = ObjectProperty()

    def __init__(self, **kw):
        super().__init__(**kw)

        self.app = MDApp.get_running_app()

    def update_icon_state(self, state):
        self.scrollable_planning.ids.state_icon.state = state

    def edge_generator(self, adjacencies):
        for i1, adj in enumerate(adjacencies):
            for i2 in adj:
                yield i1, i2

    def compute_gantt(self):
        # Get PERT graph and copy in  case we have to remove unactivated tasks
        pert_graph = self.app.manager.get_pert()
        pert_copy = pert_graph.copy()

        tasks = []
        durations = []
        consumed_resources = []
        min_begin_times = []
        max_end_times = []
        fixed_begin_time = []
        end_task = None
        for i, v in enumerate(pert_graph.V):
            if isinstance(v, EndTask):
                durations.append(0)
                consumed_resources.append(0)
                min_begin_times.append(None)
                max_end_times.append(None)
                fixed_begin_time.append(None)
                end_task = v
            elif not isinstance(v, StartTask) and v.activated:
                durations.append(v.get_duration('hour'))
                consumed_resources.append(
                    v.get_consumed_resources() if v.state != "done" else 0)
                tasks.append(v)
                max_end_times.append(v.get_max_end_time('hour'))
                if v.state == "done" or v.state == "progress" or v.fixed:
                    min_begin_times.append(None)
                    fixed_begin_time.append(v.get_begin_time('hour'))
                else:
                    min_begin_times.append(
                        self.app.manager.get_current_time('hour'))
                    fixed_begin_time.append(None)
            else:
                pert_copy.remove_vertex(v)

        # Solve the linear problem
        solver = SchedulerSolver(
            n_tasks=len(tasks) + 1,  # Don't forget the end task
            end_index=pert_copy.V.index(end_task),
            anteriority_edges=list(self.edge_generator(pert_copy.A)),
            fixed_begin_times=fixed_begin_time,
            min_begin_times=min_begin_times,
            max_end_times=max_end_times,
            durations=durations,
            consumed_resources=consumed_resources,
            capacity=self.app.manager.get_capacity())
        if solver.solve():
            # Set general variables and save
            for i, task in enumerate(tasks):
                task.set_begin_time(int(np.argmax(solver.solution[i], axis=0)),
                                    'hour')
            end_task.set_begin_time(solver.end_time, 'hour')
            self.app.manager.set_horizon(solver.horizon, 'hour')
            self.app.manager.set_planning_state("up_to_date")
        else:
            self.app.manager.set_planning_state("unsolvable")

    def validate_planning(self):
        if self.app.manager.get_planning_state() == "waiting_for_treatment":
            toast(
                "Planning cannot be validated because there is at least one task the needs treatment"
            )
        elif self.app.manager.get_planning_state() == "to_validate":
            self.compute_gantt()
        elif self.app.manager.get_planning_state() == "unsolvable":
            toast(
                "It seems that the planning is unsolvable, please check your constraints in the PERT"
            )
        self.update_icon_state(self.app.manager.get_planning_state())

    def add_waiting_for_treatment(self):
        self.scrollable_planning.n_waiting_for_treatment += 1

    def remove_waiting_for_treatment(self):
        self.scrollable_planning.n_waiting_for_treatment -= 1

    def update_planning_state(self, *args):
        self.scrollable_planning.update_planning_state()

    def export_planning(self):
        entries_path = str(
            self.app.manager.get_planning_path(extension="_entries.png"))
        tasks_path = str(
            self.app.manager.get_planning_path(extension="_tasks.png"))
        time_path = str(
            self.app.manager.get_planning_path(extension="_time.png"))
        planning_path = str(
            self.app.manager.get_planning_path(extension="_planning.png"))
        self.scrollable_planning.ids.entries.export_to_png(entries_path)
        self.scrollable_planning.ids.tasks_layout.export_to_png(tasks_path)
        self.scrollable_planning.ids.time_layout.export_to_png(time_path)
        self.scrollable_planning.ids.planning_layout.export_to_png(
            planning_path)

        left_path = str(
            self.app.manager.get_planning_path(extension="_left.png"))
        right_path = str(
            self.app.manager.get_planning_path(extension="_right.png"))
        ImageConcatenator.vertical_concatenate(left_path, entries_path,
                                               tasks_path)
        ImageConcatenator.vertical_concatenate(right_path, time_path,
                                               planning_path)

        ImageConcatenator.horizontal_concatenate(
            str(self.app.manager.get_planning_path(extension="_gantt.png")),
            left_path, right_path)

        FileManager.delete_file(entries_path)
        FileManager.delete_file(time_path)
        FileManager.delete_file(tasks_path)
        FileManager.delete_file(planning_path)
        FileManager.delete_file(left_path)
        FileManager.delete_file(right_path)

    def on_pre_enter(self):

        self.app.tool_bar.left_action_items = [[
            'arrow-left', lambda x: self.app.manager.quit(
                "choose_editor_screen", lambda: self.scrollable_planning.
                unload())
        ]]

        def update_planning(*args):
            self.validate_planning()
            self.scrollable_planning.load()

        self.app.tool_bar.right_action_items = [
            ['sort', lambda x: self.app.manager.sort_tasks_by_begin_time()],
            ['check-outline', update_planning],
            ['content-save', lambda x: self.app.manager.save()],
            ['file-export', lambda x: self.export_planning()]
        ]

        self.scrollable_planning.setup()
        update_planning()


class GraphEditorScreen(Screen):

    right_action_items = ListProperty([])
    left_action_items = ListProperty([])

    def __init__(self, **kw):
        self.pre_selected = None

        self.register_event_type("on_edit_mode")
        self.register_event_type("on_selection_mode")

        self.app = MDApp.get_running_app()

        super().__init__(**kw)

    def hide_action_bar(self):
        """Hide the bottom action bar"""
        self.remove_widget(self.bottom_action_bar)

    def show_action_bar(self):
        """Show the bottom action bar"""
        self.add_widget(self.bottom_action_bar)

    # Task/DirectedGraph operations
    def add_component(self, component, x=None, y=None, init=False):
        """Add a component:
            component: the component to add
            x: the x coordinate of the component
            y: the y coordinate of the component"""
        self.ids.edit_area.add_widget(component)
        if x and y:
            component.pos = x, y
        self.app.manager.get_pert().add_vertex(component)

        component.bind(on_add_link=self.add_link,
                       on_remove_link=self.remove_link)
        self.bind(on_edit_mode=component.edit_mode,
                  on_selection_mode=component.selection_mode)
        if not init:
            self.app.manager.set_saved(False)
            self.app.manager.set_planning_state("to_validate")

    def remove_component(self, component):
        """Remove a component:
            component: the component to remove
            """
        self.app.manager.get_pert().remove_vertex(component)
        self.ids.edit_area.remove_widget(component)
        self.app.manager.set_saved(False)
        self.app.manager.set_planning_state("to_validate")

    def place_mode_component(self, component):
        """Enter in place component mode (not a mode as link mode):
            component: the component to place, which will be centered in the view, touch transparent, and an add button to place it
            """
        def center_component(*args):
            component.center = self.ids.edit_area.to_local(
                *self.ids.view.center)

        self.ids.edit_area.bind(on_transform_with_touch=center_component)

        # Validation
        validation_btn = RightBottomFloatingButton(
            icon='check',
            md_bg_color=self.app.theme_cls.accent_color,
            elevation_normal=8)
        self.add_widget(validation_btn)

        def validate_pos(*args):
            self.change_mode(None)
            self.remove_widget(validation_btn)
            self.ids.edit_area.unbind(on_transform_with_touch=center_component)

        validation_btn.bind(on_press=validate_pos)

        def reset_mode(*args):
            self.remove_component(component)
            self.remove_widget(validation_btn)
            self.change_mode(None)

        self.set_selection_tool_bar(reset_mode)
        self.hide_action_bar()
        component.sdb_enabled = False

    def delete_mode_component(self, component=None):
        """Enter in delete mode:
            component: the component to remove, first call with component=None will look for selected component and ignite a second call which will delete it"""
        if component:
            # Remove all links with its neighbors
            for neighbor in self.app.manager.get_pert().unoriented_neighbors(
                    component):
                self.app.manager.remove_editor_link(component, neighbor,
                                                    self.ids.edit_area)

            self.remove_component(component)

        else:
            for child in self.ids.edit_area.content.children:
                if isinstance(child, Task) and child.selected:
                    self.delete_mode_component(child)
                    break

            print("Error: no selected component")

    def add_link(self, _, instance):
        """Called when mode="add_link" and a component is clicked, add link if two components have been selected else register selection and wait for second call:
            instance: the component object that has been clicked """
        # Take the first selection
        if self.pre_selected is None:
            self.pre_selected = instance
            instance.select()
        elif self.pre_selected != instance:
            # The selection is correct and no link exist in both direction
            if not self.app.manager.get_pert().adjacent(
                    self.pre_selected,
                    instance) and not self.app.manager.get_pert().adjacent(
                        instance, self.pre_selected):
                self.app.manager.add_editor_link(self.pre_selected, instance,
                                                 self.ids.edit_area)
                self.app.manager.set_saved(False)
                self.app.manager.set_planning_state("to_validate")
                self.change_mode(None)
            else:
                print("Error: link already exist")
                self.change_mode(None)
        else:
            self.pre_selected.unselect()
            self.pre_selected = None

    def remove_link(self, _, instance):
        """Called when mode="remove_link" and a component is clicked, remove link if two components have been selected else register selection and wait for second call:
            instance: the component object that has been clicked """
        # Take the first selection
        if self.pre_selected is None:
            self.pre_selected = instance
            instance.select()
        # The selection is correct
        elif self.pre_selected != instance:
            # Remove the link whatever the order of selection
            if self.app.manager.get_pert().adjacent(self.pre_selected,
                                                    instance):
                self.app.manager.remove_editor_link(self.pre_selected,
                                                    instance,
                                                    self.ids.edit_area)
                self.app.manager.set_saved(False)
                self.app.manager.set_planning_state("to_validate")
                self.change_mode(None)
            elif self.app.manager.get_pert().adjacent(instance,
                                                      self.pre_selected):
                self.app.manager.remove_editor_link(instance,
                                                    self.pre_selected,
                                                    self.ids.edit_area)
                self.app.manager.set_saved(False)
                self.app.manager.set_planning_state("to_validate")
                self.change_mode(None)
            else:
                print("Error: no link")
                self.change_mode(None)
        else:
            self.pre_selected.unselect()
            self.pre_selected = None

    # Misc
    def change_mode(self, mode=None):
        """Change the mode, edit mode for default behavior like drag, select one component ... and selection mode for enable selection of two components, with drag disabled, bottom bar hidden:
            mode: the mode (None=default, 'add_link', 'remove_link' """
        if mode is None:
            self.dispatch("on_edit_mode", mode)
        else:
            self.dispatch("on_selection_mode", mode)

        print(f"->Change link mode to {mode} mode")

    def to_center(self):
        """Go to the center of the edit_area"""
        self.ids.edit_area.to_center()

    def place_new_component(self):
        component = Task(name="New", duration=1, resource=1)
        self.add_component(component,
                           *self.ids.edit_area.to_local(*self.ids.view.center))
        self.place_mode_component(component)

    # Event
    def on_edit_mode(self, mode):
        """Setup the bars properties for edit mode"""
        self.pre_selected = None

        self.app.tool_bar.md_bg_color = self.app.theme_cls.primary_color
        self.set_tool_bar()
        self.show_action_bar()

    def on_selection_mode(self, mode):
        """Setup the bars properties for selection mode"""
        self.app.tool_bar.md_bg_color = self.app.theme_cls.accent_color
        self.set_selection_tool_bar(lambda *args: self.change_mode(None))
        self.hide_action_bar()

    def on_pre_leave(self, *args):
        """Un load edit_area contents"""
        self.ids.edit_area.content.clear_widgets()
        return super().on_pre_leave(*args)

    def set_tool_bar(self):
        self.app.tool_bar.left_action_items = [[
            'arrow-left',
            lambda x: self.app.manager.quit("choose_editor_screen")
        ]]
        self.app.tool_bar.right_action_items = [[
            'image-filter-center-focus', lambda x: self.to_center()
        ]]

    def set_selection_tool_bar(self, callback):
        self.app.tool_bar.left_action_items = [['arrow-left', callback]]
        self.app.tool_bar.right_action_items = []

    def on_pre_enter(self):
        """Initialize some widgets and display graph list"""
        self.set_tool_bar()
        self.ids.action_bar.on_action_button = self.place_new_component
        self.ids.edit_area.setup_grid()

        # Build the graph in editor
        pert = self.app.manager.get_pert()
        for component in pert.V:
            self.add_component(component, init=True)
            for neighboor in pert.neighbors(component):
                self.app.manager.add_editor_link(component, neighboor,
                                                 self.ids.edit_area)
