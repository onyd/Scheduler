import os
import json


class FileManager:
    """This class (static) contains useful method to manipulate files"""
    def __init__(self):
        pass

    @staticmethod
    def write_in(file_path, data, mode='w'):
        """This method is useful in Parser to modify json file directly"""

        try:
            with open(file_path, mode, encoding='utf8') as file:
                file.write(data)

        except IOError as e:
            print("FileManager: I/O error({}): {}".format(e.errno, e.strerror))

    @staticmethod
    def read_in(file_path):
        """This method is also useful in Parser to load and read json file"""

        try:
            if not os.path.exists(file_path):
                print("New file created to {} because it didn't exist".format(
                    file_path))
                with open(file_path, 'w') as file:
                    pass

            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except IOError as e:
            print("FileManager: I/O error({}): {}".format(e.errno, e.strerror))

    @staticmethod
    def delete_file(path):
        try:
            os.remove(path)
        except IOError as e:
            print("Unexpected error: {}".format(e.strerror))

    @staticmethod
    def load_json(path):
        try:
            return json.loads(FileManager.read_in(path))
        except IOError as e:
            print("Unexpected error: {}".format(e.strerror))

    @staticmethod
    def save_json(path, data):
        try:
            FileManager.write_in(path, json.dumps(data))
        except IOError as e:
            print("Unexpected error: {}".format(e.strerror))
