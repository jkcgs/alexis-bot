from discord import Guild

from bot.database import ServerConfig
from bot.lib.configuration import BotConfiguration


class GuildConfiguration:
    """
    Allows management of configuration for guilds, for example an anouncement channel for welcome messages.
    It can handle "global" configurations by passing None as the Guild. The values are fetched from the
    currently bot configured database. Default values and non-existant configurations are not automatically
    stored on the database. Also, this is made assuming that the database will not be changed during runtime,
    and the in-memory values are used. Values in memory are changed if the configurations are only changed
    with this class and are not synced by using getters.
    """

    _global_id = 'all'
    _list_separator = ','
    _comma_escape = '\1\1'
    _instances = {}

    @classmethod
    def get_instance(cls, guild: Guild = None, defaults=None):
        """
        Singleton method to cache this class' instance for guilds.
        :param guild: The Guild instance to use the instance for. It defaults to the global configurations.
        :param defaults: The default values for the instance. If the instance already existed, the defaults
        are set to the passed ones.
        """
        guild_id = cls._global_id if guild is None else str(guild.id)
        if guild_id not in GuildConfiguration._instances:
            GuildConfiguration._instances[guild_id] = GuildConfiguration(guild, None)
        else:
            GuildConfiguration._instances[guild_id].set_defaults(defaults)

        return GuildConfiguration._instances[guild_id]

    @staticmethod
    def get_all(guild_id=None):
        """
        Gather all settings stored for a guild as a dict.
        :param guild_id: The guild ID to use the instance for. It defaults to the global configurations.
        """
        if not guild_id:
            guild_id = GuildConfiguration._global_id

        config = ServerConfig.select().where(ServerConfig.serverid == guild_id)
        return {i.name: i.value for i in config}

    @staticmethod
    def get_value(guild_id, name, default=None):
        """
        Retrieve a value for a guild by its ID. If the value does not exist for that guild,
        the default value is returned. The default value is not stored on the database.
        :param guild_id: The guild ID to use the instance for. It defaults to the global configurations.
        :param name: The name of the value to fetch
        :param default: The default value to use.
        """
        if not guild_id:
            guild_id = GuildConfiguration._global_id

        try:
            config = ServerConfig.get(ServerConfig.serverid == guild_id and ServerConfig.name == name)
            return config.value
        except ServerConfig.DoesNotExist:
            return default

    @staticmethod
    def set_value(guild_id, name, value):
        """
        Sets a value for a guild's configuration.
        :param guild_id: The guild ID to set the configuration for.
        :param name: The configuration name.
        :param value: The value to be set for the configuration.
        :return: The value set.
        """
        config, created = ServerConfig.get_or_create(
            serverid=guild_id, name=name, defaults={'value': value}
        )

        if not created and config.value != value:
            config.value = value
            config.save()

        return config.value

    def __init__(self, guild: Guild = None, defaults=None):
        """
        :param guild: The discord.Server instance or server ID
        :param defaults: A `dict` of default values that will be return for a configuration
        name if the default value is not passed on the `get` method.
        """
        self.guild_id = str(guild.id) if guild is not None else self._global_id
        self._config = self.get_all(self.guild_id)
        self._defaults = {}

        if defaults:
            self.set_defaults(defaults)

    def set_defaults(self, defaults=None):
        """
        Sets the defaults values to be used if no default values are passed for this class' instance getters.
        :param defaults: A dict with the default values.
        """
        if defaults is not None and not issubclass(defaults.__class__, dict):
            raise ValueError('defaults param must be a dict or a subclass, instead, received {}'.format(
                defaults.__class__.__name__
            ))

        self._defaults = {} if defaults is None else defaults

    def has(self, name):
        """
        Checks if the server has a configuration value, without setting a default value.
        :param name: The configuration value name
        :return: A boolean value from the operation result.
        """
        return name in self._config

    def get(self, name, default=None):
        """
        Fetch a configuration value for a server. If the configuration does not exist, the default value from the
        defaults list will be returned. If there's no default value in the defaults list, the default value from the
        arguments is returned.
        :param name: The value name to retrieve
        :param default: The default value to use if the configuration does not exist
        :return: The requested configuration value.
        """
        default = default if default is not None else self.get_value(name, self._defaults.get(name, default))
        return self._config.get(name, default)

    def set(self, name, value):
        """
        Sets the configuration value. If the configuration value is not changed, nothing is done on the database.
        :param name: The configuration value to be set.
        :param value: The new configuration value.
        :return: The stored value.
        """
        self._config[name] = self.set_value(self.guild_id, name, value)
        return self._config[name]

    def unset(self, name):
        """
        Deletes a configuration value from the database.
        :param name: The configuration value name.
        :return: A boolean given if the value existed previously or not.
        """
        if not self.has(name):
            return False

        try:
            ins = ServerConfig.get(serverid=self.guild_id, name=name)
            ins.delete_instance()
            del self._config[name]
            return True
        except ServerConfig.DoesNotExist:
            return False

    def get_list(self, name, default=None):
        """
        Fetches a configuration value as a comma separated list. List elements that had commas in its values
        are stored as '\0\0', but replaced back to commas when returned.
        :param name: The configuration value name.
        :param default: The default value if it does not exist.
        :return: The requested configuration as a list
        """
        if default is None:
            default = []
        if not issubclass(default.__class__, list):
            raise ValueError('defaults param must be a list or a subclass, instead, received {}'.format(
                self._defaults.__class__.__name__
            ))

        if not self.has(name):
            return default

        val = self.get(name, '')
        val_list = default if val == '' else val.split(self._list_separator)
        val_list = [i.replace(self._comma_escape, ',') for i in val_list]
        return val_list

    def set_list(self, name, elements):
        """
        Stores a comma separated list in the configuration, overwriting current values. Values containing commas
        will have them replaced with '\0\0'.
        :param name: The configuration value name.
        :param elements: The list to be stored.
        """
        if not issubclass(elements.__class__, list):
            raise ValueError('elements param must be a list or a subclass, instead, received {}'.format(
                self._defaults.__class__.__name__
            ))

        value = self._list_separator.join([str(e).replace(',', self._comma_escape) for e in elements])
        self.set(name, value)

    def get_bool(self, name, default=True):
        """
        Retrieve a boolean value for a guild by its ID. If the value does not exist,
        the default value is returned, always as a boolean. The default value is not stored on the database.
        :param name: The name of the value to fetch
        :param default: The default value to use.
        """
        return self.get(name, default=str(int(bool(default)))) == '1'

    def set_bool(self, name, value):
        """
        Sets a boolean value for a guild's configuration.
        A true value is stored as '1' and a false value is stored as '0'.
        :param name: The configuration name.
        :param value: The value to be set for the configuration.
        :return: The boolean value set.
        """
        value_conv = str(int(bool(value)))
        return self.set(name, value_conv) == '1'

    def add(self, name, value, ignore_dupe=False):
        """
        Fetches a configuration value as a list, appends a value, then stores it.
        :param name: The configuration value name
        :param value: The value to be added. If it's already on the list, it won't be added.
        :param ignore_dupe: If the value is already on the list, it's added anyways.
        :return: The list with the new value added (if it wasn't on the list already).
        """
        values = self.get_list(name)
        if ignore_dupe or value not in values:
            values.append(value)
            self.set_list(name, values)

        return values

    def remove(self, name, value):
        """
        Fetches a configuration value as a list, removes a value if it exists, then stores the list.
        :param name: The configuration value name.
        :param value: The value to be removed from the list.
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        values = self.get_list(name)
        if value in values:
            values.remove(value)
            self.set_list(name, values)

        return values

    def remove_index(self, name, idx):
        """
        Fetches a configuration value as a list, removes a value by it's index, then stores the list.
        :param name: The configuration value name.
        :param idx: The value index, starting from zero. If the index is invalid, the list won't be modified.
        :return: The list with the value removed, or the same list if the item wasn't on the list.
        """
        values = self.get_list(name)
        if abs(values) >= len(values):
            return values

        del values[idx]
        self.set_list(name, values)
        return values

    # Specific values

    @property
    def prefix(self):
        bot_config = BotConfiguration.get_instance()
        return self.get('command_prefix', bot_config.prefix)

    @prefix.setter
    def prefix(self, value):
        self.set('command_prefix', value)
