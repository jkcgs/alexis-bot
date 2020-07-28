import os

from ruamel.yaml import YAML

from bot import defaults as bot_defaults
from bot.lib.logger import create_logger

log = create_logger('Configuration')
yaml = YAML(typ='safe')
yaml.default_flow_style = False


class Configuration:
    """
    Manages a YAML configuration file
    """
    def __init__(self, path='config.yml', defaults=None, autoload=False):
        """
        Initializes this class.
        :param path: YAML file to manage path
        :param autoload: Load the file on creating the instance
        """
        self.path = path
        self._config = {}
        self._defaults = {}

        if defaults is not None:
            if not issubclass(defaults.__class__, dict):
                raise ValueError('defaults param must be a dict or a subclass, instead received a {}'.format(
                    defaults.__class__.__name__
                ))
            self._defaults = defaults.copy()

        if autoload:
            self.load()

    def load(self):
        """Loads the configuration file to this instance."""
        try:
            with open(self.path) as f:
                loaded_conf = yaml.load(f)
                if loaded_conf is None:
                    loaded_conf = {}

            self._config = loaded_conf
        except (FileNotFoundError, PermissionError) as e:
            log.error('Could not load the configuration file. %s: %s', e.__class__.__name__, str(e))
            pass

    def load_defaults(self, defaults):
        if not issubclass(defaults.__class__, dict):
            raise ValueError('defaults param must be a dict or a subclass, instead received a {}'.format(
                defaults.__class__.__name__
            ))
        self._defaults = {**self._defaults, **defaults}

    def get(self, name, default=None):
        """
        Retrieves a value from the settings
        :param name: The value name
        :param default: If the value's not on the configuration, this value will be returned, but not set. If this
        argument is not set, and the value by the given name does not exist, a KeyError exception will be raised.
        :return: The configuration value
        """
        default = default if default is not None else self._defaults.get(name, None)
        return self._config.get(name, default)

    def get_all(self):
        return {**self._defaults, **self._config}

    def __getitem__(self, item):
        return self.get(item)

    def __contains__(self, item):
        return item in {**self._config, **self._defaults}

    @classmethod
    def get_config_path(cls, name):
        config_path = 'config/' + name + '.yml'
        return config_path

    @classmethod
    def exists(cls, name):
        return os.path.exists(cls.get_config_path(name))

    @classmethod
    def get_config(cls, name, default_config=None):
        """
        Loads a file inside the "config" folder from the current execution path, and returns an instance of this class.
        :param name: The file name (don't add '.yml', since it will be appended)
        :param default_config: Default values to load to the instance
        :return: A Configuration instance for the loaded file
        """

        if not os.path.exists('config'):
            try:
                os.mkdir('config')
            except PermissionError:
                log.warning('Could not create the "config" folder.')
                pass

        config_path = cls.get_config_path(name)
        return Configuration(config_path, defaults=default_config, autoload=True)


class BotConfiguration(Configuration):
    def __init__(self):
        super().__init__('config.yml', bot_defaults.config, autoload=True)

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = BotConfiguration()

        return cls._instance

    @property
    def prefix(self):
        return self.get('command_prefix')
