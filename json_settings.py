import json
import os


class JsonSettings:
    file_path = ''
    file_name = 'SC_Vision_Inspection'

    def _load_file(self):
        try:
            file = open(self.file_path + self.file_name, 'r')
        except FileNotFoundError:
            file = open(self.file_path + self.file_name, 'w')
            file.close()

        file = open(self.file_path + self.file_name, 'r')
        if not os.stat(self.file_path + self.file_name).st_size == 0:
            data = json.load(file)
            file.close()
            return data
        else:
            return None

    def _save_file(self, data):
        file = open(self.file_path + self.file_name, 'w')
        json.dump(data, file)
        file.close()

    def pretty_print(self):
        file = open(self.file_path + self.file_name, 'r')
        parsed = json.load(file)
        print(json.dumps(parsed, indent=4, sort_keys=True))
        file.close()

    def get_value(self, identifier: str, default_value: object):
        data = self._load_file()
        if data is None:
            return default_value

        if identifier not in data.keys():
            self.set_value(identifier, default_value)
            return default_value

        return data[identifier]

    def set_value(self, identifier: str, value: object):
        path = identifier.split('.')
        data = self._load_file()
        if data is None:
            data = {}

        data_keys = data.keys()
        raw_data = data

        for p in path[:-1]:
            if p in data_keys:
                data = data[p]
            else:
                data[p] = {}
                data = data[p]

        if identifier in data.keys():
            data[path[-1]] = str(value)
        else:
            data[path[-1]] = str(value)

        self._save_file(raw_data)
