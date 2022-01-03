from datetime import datetime
import traceback


class SerializableObject:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_class_by_name(import_name):
        parts = import_name.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m

    def to_dict(self, **kwargs):
        # Recursively serialize data object in list
        for key, value in kwargs.items():
            if isinstance(value, list):
                serialized = []
                for x in value:
                    try:
                        serialized.append(x.to_dict())
                    except:
                        serialized.append(x)
                kwargs[key] = serialized
            else:
                try:
                    kwargs[key] = value.to_dict()
                except:
                    pass

        obj = {
            'module': self.__class__.__module__,
            'class_name': self.__class__.__name__,
        }
        obj.update(kwargs)
        return obj

    @staticmethod
    def from_dict(data, **kwargs):
        module_class_name = ""
        try:
            module_class_name = data['module'] + "." + data['class_name']
            del data['module']
            del data['class_name']
        except:
            return data

        # Recursively deserialize data object in list
        for key, value in data.items():
            if isinstance(value, list):
                deserialized = []
                for x in value:
                    try:
                        deserialized.append(SerializableObject.from_dict(x))
                    except:
                        deserialized.append(x)
                        traceback.print_exc()

                data[key] = deserialized
            else:
                try:
                    data[key] = SerializableObject.from_dict(value)
                except:
                    pass
        object_class = SerializableObject.get_class_by_name(module_class_name)
        data.update(kwargs)
        obj = object_class(**data)
        return obj
