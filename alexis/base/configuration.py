import yaml


class StaticConfig:
    def __init__(self, path, autoload=False):
        self.config = {}
        self.path = path

        if autoload:
            self.load()

    def load(self):
        with open(self.path) as f:
            loaded_conf = yaml.safe_load(f)
            if loaded_conf is None:
                loaded_conf = {}

        self.config = loaded_conf

    def save(self):
        with open(self.path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get(self, name, default=''):
        return self.config.get(name, default)

    def set(self, name, val):
        self.config[name] = val
        self.save()
