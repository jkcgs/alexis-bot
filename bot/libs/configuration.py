import os

from ruamel.yaml import YAML

from bot import defaults

yaml = YAML(typ='safe')
yaml.default_flow_style = False


class StaticConfig:
    """
    Manages a YAML configuration file
    """
    def __init__(self, path='config.yml', autoload=False):
        """
        Initializes this class.
        :param path: YAML file to manage path
        :param autoload: Load the file on creating the instance
        """
        self.config = {}
        self.path = path

        if autoload:
            self.load()

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, item):
        return item in self.config

    def load(self, default_config=None):
        """
        Loads the configuration file
        :param default_config: Default settings to load into the file
        :return: A dict with the file data and the default settings, if passed.
        """
        with open(self.path) as f:
            loaded_conf = yaml.load(f)
            if loaded_conf is None:
                loaded_conf = {}

        self.config = loaded_conf

        if default_config is not None and isinstance(default_config, dict):
            self.config = {**default_config, **loaded_conf}
            self.save()

    def load_defaults(self, default_config):
        """
        Loads default settings into the file
        :param default_config: A dict with the defaults
        """
        if not isinstance(default_config, dict):
            raise RuntimeError('defaults argument must be a dict instance')

        self.config = {**default_config, **self.config}
        self.save()

    def save(self, reload=False):
        """
        Saves current settings to the file
        :param reload: Set to True to load again the file
        """
        with open(self.path, 'w') as f:
            yaml.dump(self.config, f)

        if reload:
            self.load()

    def get(self, name, default=None):
        """
        Retrieves a value from the settings
        :param name: The value name
        :param default: If the value's not on the configuration, this value will be returned, but not set. If this
        argument is not set, and the value by the given name does not exist, a KeyError exception will be raised.
        :return: The configuration value
        """
        if name not in self.config and default is None:
            raise KeyError('Key {} not found'.format(name))

        return self.config.get(name, default)

    def set(self, name, val):
        """
        Set and store a configuration value, then reload the configuration file.
        :param name: The name of the value to change
        :param val: The value to be save
        :return: The saved value
        """
        self.config[name] = val
        self.save(reload=True)
        return self.config[name]

    @staticmethod
    def get_config(name, default_config=None):
        """
        Loads a file inside the "config" folder from the current execution path, and returns an instance of this class.
        :param name: The file name (don't add '.yml', since it will be appended)
        :param default_config: Default values to load to the file
        :return: A StaticConfig instance for the loaded file
        """

        if not os.path.exists('config'):
            os.mkdir('config')

        conf_path = 'config/' + name + '.yml'
        if not os.path.exists(conf_path):
            with open(conf_path, 'a'):
                os.utime(conf_path, None)

        ins = StaticConfig('config/' + name + '.yml', True)
        if default_config is not None:
            ins.load_defaults(default_config)

        return ins

    @staticmethod
    def exists(name):
        return os.path.exists('config/' + name + '.yml')


class BotConfiguration(StaticConfig):
    def __init__(self):
        super().__init__(path='config.yml')
        self.load(defaults.config)
        self.loaded = True

    _instance = None

    @staticmethod
    def get_instance():
        if BotConfiguration._instance is None:
            BotConfiguration._instance = BotConfiguration()

        return BotConfiguration._instance
