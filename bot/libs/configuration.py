import os
import discord
import peewee
from playhouse.db_url import connect
from ruamel.yaml import YAML


db = None
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

    def load(self, defaults=None):
        """
        Loads the configuration file
        :param defaults: Default settings to load into the file
        :return: A dict with the file data and the default settings, if passed.
        """
        with open(self.path) as f:
            loaded_conf = yaml.load(f)
            if loaded_conf is None:
                loaded_conf = {}

        self.config = loaded_conf

        if defaults is not None and isinstance(defaults, dict):
            self.config = {**defaults, **loaded_conf}
            self.save()

    def load_defaults(self, defaults):
        """
        Loads default settings into the file
        :param defaults: A dict with the defaults
        """
        if not isinstance(defaults, dict):
            raise RuntimeError('defaults argument must be a dict instance')

        self.config = {**defaults, **self.config}
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
    def get_config(name, defaults=None):
        """
        Loads a file inside the "config" folder from the current execution path, and returns an instance of this class.
        :param name: The file name (don't add '.yml', since it will be appended)
        :param defaults: Default values to load to the file
        :return: A StaticConfig instance for the loaded file
        """

        if not os.path.exists('config'):
            os.mkdir('config')

        conf_path = 'config/' + name + '.yml'
        if not os.path.exists(conf_path):
            with open(conf_path, 'a'):
                os.utime(conf_path, None)

        ins = StaticConfig('config/' + name + '.yml', True)
        if defaults is not None:
            ins.load_defaults(defaults)

        return ins

    @staticmethod
    def exists(name):
        return os.path.exists('config/' + name + '.yml')


class Configuration:
    """
    Manages per-server configuration on the database, cached on memory.
    """
    def __init__(self):
        """
        Initialize and fetch all the configuration from the database, then store it on memory.
        """
        self.q = ServerConfig.select().execute()
        self.sv = {}

        for conf in list(self.q):
            if conf.serverid not in self.sv:
                self.sv[conf.serverid] = {}
            self.sv[conf.serverid][conf.name] = conf.value

    def has(self, svid, name):
        """
        Checks if the server has a configuration value, without setting a default value.
        :param svid: The server ID
        :param name: The configuration value name
        :return: A boolean value from the operation result.
        """
        try:
            if svid not in self.sv:
                self.sv[svid] = {}

            if name in self.sv[svid]:
                return True

            ServerConfig.get(serverid=svid, name=name)
            return True
        except ServerConfig.DoesNotExist:
            return False

    def get(self, svid, name, default='', create=True):
        """
        Fetch a configuration value for a server. If the configuration does not exist, it will be initialized
        with the default value, then, is stored on memory. If the default value is None and the value does not
        exist, then the database will not be queried.
        :param svid: The server ID
        :param name: The value name to retrieve
        :param default: The default value to use if the configuration does not exist
        :param create: If the value does not exist, and the default value is passed, the value will be created
        on the database and cached on memory. Else, the default value is returned and nothing else.
        :return: The requested configuration value.
        """
        if svid not in self.sv:
            self.sv[svid] = {}

        if name not in self.sv[svid]:
            if default is None and not self.has(svid, name):
                return None

            if create:
                q, _ = ServerConfig.get_or_create(serverid=svid, name=name, defaults={'value': str(default)})
                self.sv[svid][name] = q.value
            else:
                return default or None

        return self.sv[svid][name]

    def set(self, svid, name, value):
        """
        Stores a configuration in database and memory. If the value is the same as in memory, then the database is
        not altered.
        :param svid: The server ID
        :param name: The configuration value to be set
        :param value: The new configuration value
        :return: The stored value
        """
        value = str(value)
        if self.get(svid, name, value) == value:
            return value

        q, _ = ServerConfig.get_or_create(serverid=svid, name=name)
        q.value = value
        q.save()
        self._local_save(svid, name, value)

        return q.value

    def unset(self, svid, name):
        """
        Deletes a configuration from the database. It does not raise any exceptions.
        :param svid: The server ID
        :param name: The configuration value name
        :return: A boolean given if the value existed or not
        """
        if self.has(svid, name):
            try:
                ins = ServerConfig.get(serverid=svid, name=name)
                ins.delete_instance()
                del self.sv[svid][name]
                return True
            except ServerConfig.DoesNotExist:
                return False
        return False

    def get_list(self, svid, name, separator=','):
        """
        Fetches a configuration value as a list
        :param svid: The server ID
        :param name: The configuration value name
        :param separator: The separator that will split the values (as it's stored as a single string)
        :return: The requested configuration as a list
        """
        val = self.get(svid, name, '')
        return [] if val == '' else val.split(separator)

    def set_list(self, svid, name, elements, separator=','):
        """
        Stores a list in the configuration, overwriting current values.
        :param svid: The server ID
        :param name: The configuration value name
        :param elements: The list to be stored
        :param separator: The glue for the items list (as it's stored as a single string)
        """
        if not isinstance(elements, list):
            raise RuntimeError('elements argument only supports a list instance')

        result = separator.join(elements)
        self.set(svid, name, result)

    def add(self, svid, name, value, separator=','):
        """
        Fetches a cofiguration value as a list, appends a value, then stores it.
        :param svid: The server ID
        :param name: The configuration value name
        :param value: The value to be added. If it's already on the list, it won't be added.
        :param separator: The splitter string
        :return: The list with the new value added (if it wasn't on the list already)
        """
        values = self.get_list(svid, name, separator)
        if value not in values:
            values.append(value)
            self.set_list(svid, name, values, separator)

        return values

    def remove(self, svid, name, value, separator=','):
        """
        Fetches a cofiguration value as a list, removes a value if it exists, then stores the list.
        :param svid: The server ID
        :param name: The configuration value name
        :param value: The value to be removed from the list
        :param separator: The splitter string (as the value is stored as a single string)
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        values = self.get_list(svid, name, separator)
        if value in values:
            values.remove(value)
            self.set_list(svid, name, values, separator)

        return values

    def remove_index(self, svid, name, idx, separator):
        """
        Fetches a cofiguration value as a list, removes a value by it's index, then stores the list.
        :param svid: The server ID
        :param name: The configuration value name
        :param idx: The value index, starting from zero. If the index is invalid, the list won't be modified.
        :param separator: The splitter string (as the value is stored as a single string)
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        values = self.get_list(svid, name, separator)
        if abs(values) >= len(values):
            return values

        del values[idx]
        self.set_list(svid, name, values, separator)
        return values

    def _local_save(self, svid, name, value):
        """
        Guarda una configuración en memoria solamente
        :param svid: El ID del servidor
        :param name: El nombre de la configuración
        :param value: El valor de la configuración
        :return: El valor de la configuración guardada
        """
        if svid not in self.sv:
            self.sv[svid] = {}

        self.sv[svid][name] = str(value)
        return self.sv[svid][name]


class ServerConfiguration:
    """
    Shortcut to manage a single server configuration from a Configuration instance.
    """
    def __init__(self, mgr, server):
        """
        :param mgr: The Configuration instance for the global configuration manager
        :param server: The discord.Server instance or server ID
        """
        self.svid = server.id if isinstance(server, discord.Server) else server
        self.mgr = mgr

    def has(self, name):
        """
        Checks if the server has a configuration value, without setting a default value.
        :param name: The configuration value name
        :return: A boolean value from the operation result.
        """
        return self.mgr.has(self.svid, name)

    def get(self, name, default='', create=True):
        """
        Fetch a configuration value for a server. If the configuration does not exist, it will be initialized
        with the default value, then, is stored on memory. If the default value is None and the value does not
        exist, then the database will not be queried.
        :param name: The value name to retrieve
        :param default: The default value to use if the configuration does not exist
        :param create: If the value does not exist, and the default value is passed, the value will be created
        on the database and cached on memory. Else, the default value is returned and nothing else.
        :return: The requested configuration value.
        """
        return self.mgr.get(self.svid, name, default, create)

    def set(self, name, value):
        """
        Stores a configuration in database and memory. If the value is the same as in memory, then the database is
        not altered.
        :param name: The configuration value to be set
        :param value: The new configuration value
        :return: The stored value
        """
        return self.mgr.set(self.svid, name, value)

    def unset(self, name):
        """
        Deletes a configuration value from the database. It does not raise any exceptions.
        :param name: The configuration value name
        :return: A boolean given if the value existed or not
        """
        return self.mgr.unset(self.svid, name)

    def get_list(self, name, separator=','):
        """
        Fetches a configuration value as a list
        :param name: The configuration value name
        :param separator: The separator that will split the values (as it's stored as a single string)
        :return: The requested configuration as a list
        """
        return self.mgr.get_list(self.svid, name, separator)

    def set_list(self, name, elements, separator='.'):
        """
        Stores a list in the configuration, overwriting current values.
        :param name: The configuration value name
        :param elements: The list to be stored
        :param separator: The glue for the items list (as it's stored as a single string)
        """
        self.mgr.set_list(self.svid, name, elements, separator)

    def add(self, name, value, separator=','):
        """
        Fetches a cofiguration value as a list, appends a value, then stores it.
        :param name: The configuration value name
        :param value: The value to be added. If it's already on the list, it won't be added.
        :param separator: The splitter string
        :return: The list with the new value added (if it wasn't on the list already)
        """
        return self.mgr.add(self.svid, name, value, separator)

    def remove(self, name, value, separator=','):
        """
        Fetches a cofiguration value as a list, removes a value if it exists, then stores the list.
        :param svid: The server ID
        :param name: The configuration value name
        :param value: The value to be removed from the list
        :param separator: The splitter string (as the value is stored as a single string)
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        return self.mgr.remove(self.svid, name, value, separator)

    def remove_index(self, name, idx, separator=','):
        """
        Fetches a cofiguration value as a list, removes a value by it's index, then stores the list.
        :param svid: The server ID
        :param name: The configuration value name
        :param idx: The value index, starting from zero. If the index is invalid, the list won't be modified.
        :param separator: The splitter string (as the value is stored as a single string)
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        return self.mgr.remove(self.svid, name, idx, separator)


def get_database():
    global db
    cfg = StaticConfig('config.yml')
    cfg.load({'database_url': 'sqlite:///database.db'})

    dburl = cfg['database_url']
    if dburl.startswith('mysql:'):
        dburl += '&amp;' if '?' in dburl else '?'
        dburl += 'charset=utf8mb4;'

    if db is None:
        db = connect(dburl)

    return db


class BaseModel(peewee.Model):
    class Meta:
        database = get_database()


class ServerConfig(BaseModel):
    serverid = peewee.TextField()
    name = peewee.TextField()
    value = peewee.TextField(default='')


def init_db():
    tdb = get_database()
    tdb.create_tables([ServerConfig], safe=True)
    return tdb
