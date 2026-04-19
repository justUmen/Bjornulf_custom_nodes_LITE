import os
import json
import datetime

class ToDoList:
    """
    A simple To-Do List node for ComfyUI that saves tasks to a file.
    Tasks are saved in a JSON file within a 'Bjornulf' folder in custom_nodes.
    """

    CATEGORY = "Bjornulf Tools"  # Category in ComfyUI node menu
    RETURN_TYPES = ()  # This node doesn't output anything directly
    OUTPUT_NODE = True  # This is an output node (utility, not processing data)

    FUNCTION = "todo_list"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "task_description": ("STRING", {"multiline": False, "default": ""}),
                "action": (["add_task", "remove_task", "clear_completed", "view_list", "no_action"], {"default": "view_list"}),
                "task_index_remove": ("INT", {"default": 0, "min": 0}), # For removing tasks by index
                "task_index_complete": ("INT", {"default": 0, "min": 0}), # For completing tasks by index (future enhancement)
                "load_on_startup": ("BOOLEAN", {"default": True}),
                "save_on_change": ("BOOLEAN", {"default": True}),
                "display_completed_tasks": ("BOOLEAN", {"default": True}),

            },
        }

    NODE_DISPLAY_NAME = "Bjornulf ToDo List"
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf Tools"

    def __init__(self):
        self.todo_file_path = self._get_todo_file_path()
        self.todo_list = []
        self.last_action = "view_list"  # Track last action to avoid redundant saves
        self.list_needs_refresh = True # Flag to re-render the list in UI

    def _get_todo_file_path(self):
        """Constructs the full path to the todo list JSON file."""
        bjornulf_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Bjornulf") # custom_nodes/Bjornulf
        if not os.path.exists(bjornulf_folder):
            os.makedirs(bjornulf_folder)
        return os.path.join(bjornulf_folder, "todo_list.json")

    def _load_todo_list(self):
        """Loads the todo list from the JSON file."""
        try:
            if os.path.exists(self.todo_file_path):
                with open(self.todo_file_path, 'r') as f:
                    self.todo_list = json.load(f)
            else:
                self.todo_list = [] # Start with an empty list if file doesn't exist
            self.list_needs_refresh = True # Force refresh after load
        except Exception as e:
            print(f"Error loading todo list: {e}")
            self.todo_list = [] # Ensure we have an empty list even on error

    def _save_todo_list(self):
        """Saves the todo list to the JSON file."""
        try:
            with open(self.todo_file_path, 'w') as f:
                json.dump(self.todo_list, f, indent=4) # Indent for readability
            self.last_action = "save" # Track save action
        except Exception as e:
            print(f"Error saving todo list: {e}")

    def todo_list(self, task_description, action, task_index_remove, task_index_complete, load_on_startup, save_on_change, display_completed_tasks):
        if load_on_startup and self.last_action != "load": # Load only once per workflow execution if requested
            self._load_todo_list()
            self.last_action = "load" # Track load action

        if action == "add_task" and task_description:
            self._add_task(task_description)
            if save_on_change:
                self._save_todo_list()
            self.list_needs_refresh = True
        elif action == "remove_task":
            self._remove_task(task_index_remove)
            if save_on_change:
                self._save_todo_list()
            self.list_needs_refresh = True
        elif action == "clear_completed":
            self._clear_completed_tasks()
            if save_on_change:
                self._save_todo_list()
            self.list_needs_refresh = True
        elif action == "view_list" or action == "no_action":
            pass # Just view/refresh the list
        else:
            print(f"Unknown action: {action}")

        return self.prepare_display_widgets(display_completed_tasks) # Prepare widgets always to update UI

    def _add_task(self, task_description):
        """Adds a new task to the todo list."""
        new_task = {
            "description": task_description.strip(),
            "completed": False,
            "created_at": datetime.datetime.now().isoformat()
        }
        self.todo_list.append(new_task)

    def _remove_task(self, task_index):
        """Removes a task from the todo list by its index (0-based)."""
        if 0 <= task_index < len(self.todo_list):
            self.todo_list.pop(task_index)
        else:
            print(f"Invalid task index for removal: {task_index}")

    def _clear_completed_tasks(self):
        """Removes all completed tasks from the todo list."""
        self.todo_list = [task for task in self.todo_list if not task["completed"]]

    def prepare_display_widgets(self, display_completed_tasks):
        """Prepares the widgets to display the todo list in the ComfyUI node."""
        display_text = "Bjornulf ToDo List:\n--------------------\n"

        tasks_to_display = self.todo_list if display_completed_tasks else [task for task in self.todo_list if not task["completed"]]

        if not tasks_to_display:
            display_text += "No tasks yet. Add some above!"
        else:
            for index, task in enumerate(tasks_to_display):
                status = "[x]" if task["completed"] else "[ ]"
                display_text += f"{index}: {status} {task['description']} (Created: {task['created_at'][:10]})\n" # Show date, truncate time

        # Create a widget to display the list. Only update if list has changed.
        if self.list_needs_refresh or not hasattr(self, 'display_widget') or self.display_widget.value != display_text:
            if hasattr(self, 'display_widget'):
                self.display_widget.value = display_text # Update existing widget
            else:
                self.display_widget = self.create_widget("STRING", "todo_display", text=display_text, multiline=True, readonly=True)
            self.list_needs_refresh = False # Reset refresh flag


        return {"ui": {"widget": [self.display_widget]}}