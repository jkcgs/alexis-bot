import discord
from discord import Guild

from bot.database import ServerConfig


class DynConfiguration:
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

    def get_list(self, svid, name, separator=',', default=None):
        """
        Fetches a configuration value as a list
        :param svid: The server ID
        :param name: The configuration value name
        :param separator: The separator that will split the values (as it's stored as a single string)
        :param default: The default value to return if the config does not exist.
        :return: The requested configuration as a list
        """
        if default is None:
            default = []
        val = self.get(svid, name, '')
        return default if val == '' else val.split(separator)

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

        result = separator.join([str(e) for e in elements])
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

    _instance = None

    @staticmethod
    def get_instance():
        if not DynConfiguration._instance:
            DynConfiguration._instance = DynConfiguration()

        return DynConfiguration._instance


class GuildConfiguration:
    """
    Shortcut to manage a single server configuration from a Configuration instance.
    """
    def __init__(self, guild: discord.Guild = None):
        """
        :param guild: The discord.Server instance or server ID
        """
        self.guild_id = str(guild.id) if guild is not None else 'all'
        self.mgr = DynConfiguration.get_instance()

    def has(self, name):
        """
        Checks if the server has a configuration value, without setting a default value.
        :param name: The configuration value name
        :return: A boolean value from the operation result.
        """
        return self.mgr.has(self.guild_id, name)

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
        return self.mgr.get(self.guild_id, name, default, create)

    def set(self, name, value):
        """
        Stores a configuration in database and memory. If the value is the same as in memory, then the database is
        not altered.
        :param name: The configuration value to be set
        :param value: The new configuration value
        :return: The stored value
        """
        return self.mgr.set(self.guild_id, name, value)

    def unset(self, name):
        """
        Deletes a configuration value from the database. It does not raise any exceptions.
        :param name: The configuration value name
        :return: A boolean given if the value existed or not
        """
        return self.mgr.unset(self.guild_id, name)

    def get_list(self, name, separator=',', default=None):
        """
        Fetches a configuration value as a list
        :param name: The configuration value name
        :param separator: The separator that will split the values (as it's stored as a single string)
        :param default: The default value if it does not exist.
        :return: The requested configuration as a list
        """
        return self.mgr.get_list(self.guild_id, name, separator, default)

    def set_list(self, name, elements, separator='.'):
        """
        Stores a list in the configuration, overwriting current values.
        :param name: The configuration value name
        :param elements: The list to be stored
        :param separator: The glue for the items list (as it's stored as a single string)
        """
        self.mgr.set_list(self.guild_id, name, elements, separator)

    def add(self, name, value, separator=','):
        """
        Fetches a cofiguration value as a list, appends a value, then stores it.
        :param name: The configuration value name
        :param value: The value to be added. If it's already on the list, it won't be added.
        :param separator: The splitter string
        :return: The list with the new value added (if it wasn't on the list already)
        """
        return self.mgr.add(self.guild_id, name, value, separator)

    def remove(self, name, value, separator=','):
        """
        Fetches a cofiguration value as a list, removes a value if it exists, then stores the list.
        :param name: The configuration value name
        :param value: The value to be removed from the list
        :param separator: The splitter string (as the value is stored as a single string)
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        return self.mgr.remove(self.guild_id, name, value, separator)

    def remove_index(self, name, idx, separator=','):
        """
        Fetches a cofiguration value as a list, removes a value by it's index, then stores the list.
        :param name: The configuration value name
        :param idx: The value index, starting from zero. If the index is invalid, the list won't be modified.
        :param separator: The splitter string (as the value is stored as a single string)
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        return self.mgr.remove(self.guild_id, name, idx, separator)

    _instances = {}

    @staticmethod
    def get_instance(guild: Guild = None):
        guild_id = 'all' if guild is None else str(guild.id)
        if guild_id not in GuildConfiguration._instances:
            GuildConfiguration._instances[guild_id] = GuildConfiguration(guild)

        return GuildConfiguration._instances[guild_id]
