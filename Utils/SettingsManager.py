import json
from pathlib import Path
from Utils.FileManager import FileManager

# settings location
settings_path = Path("settings.json")


class SettingsManager:
    """This class make json manipulation easier, store data and allow us to get specific data faster without reloading the file everytime"""
    def __init__(self, json_file=settings_path):
        """Just store the data and path"""
        self.path = json_file
        self.data = FileManager.load_json(self.path)

    def _read_all(self):
        """This method is essentially for debugging and explore data"""
        return json.dumps(self.data, indent=2)

    def _get(self, name, default=None):
        """A getter to get the json encoded item with name: name"""

        return self.data.get(name, default)

    def __getitem__(self, item):
        return self._get(item)

    def _set(self, name, data):
        """A setter to set the json encoded item with name: name and update the file"""

        self.data[name] = data
        self.update()

    def get_paths(self):
        return self.data['paths']