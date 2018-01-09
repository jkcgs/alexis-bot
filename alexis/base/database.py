import discord
import peewee

db = peewee.SqliteDatabase('database.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class ServerConfig(BaseModel):
    serverid = peewee.TextField()
    name = peewee.TextField()
    value = peewee.TextField(default='')


db.create_table(ServerConfig, safe=True)


class ServerConfigMgr:
    """
    Gestiona la configuración por servidor almacenada en la base de datos, cacheada en memoria.
    """
    def __init__(self):
        """
        Inicializa y obtiene toda la configuración desde la base de datos y la almacena en memoria.
        """
        self.q = ServerConfig.select().execute()
        self.sv = {}

        for conf in list(self.q):
            if conf.serverid not in self.sv:
                self.sv[conf.serverid] = {}
            self.sv[conf.serverid][conf.name] = conf.value

    def get(self, svid, name, default=''):
        """
        Obtiene la configuración para un servidor. Si la configuración no existe, se inicializa con el valor
        por defecto y lo guarda en memoria.
        :param svid: El ID del servidor
        :param name: El nombre de la configuración a cargar
        :param default: Si no existe esta configuración, se guarda este valor y se retorna el mismo
        :return: La configuración necesitada.
        """
        if svid not in self.sv:
            self.sv[svid] = {}
        if name not in self.sv[svid]:
            q, _ = ServerConfig.get_or_create(serverid=svid, name=name, defaults={'value': str(default)})
            self.sv[svid][name] = q.value

        return self.sv[svid][name]

    def set(self, svid, name, value):
        """
        Guarda una configuración en la base de datos y la sincroniza en memoria. Si la configuración es igual
        a la almacenada en memoria, no se realizan transacciones en la base de datos.
        :param svid: El ID el servidor
        :param name: El nombre de la configuración a buscar
        :param value: El valor de configuración a almacenar
        :return: El valor guardado
        """
        value = str(value)
        if self.get(svid, name, value) == value:
            return value

        q, _ = ServerConfig.get_or_create(serverid=svid, name=name)
        q.value = value
        q.save()
        self._local_save(svid, name, value)

        return q.value

    def get_list(self, svid, name, separator=','):
        """
        Obtiene un valor de la configuración como una lista
        :param svid: El ID del servidor
        :param name: El nombre de la configuración
        :param separator: El separador que determinará la configuración de la lista
        :return: La lista desde la configuración
        """
        val = self.get(svid, name, '')
        return [] if val == '' else val.split(separator)

    def set_list(self, svid, name, elements, separator=','):
        """
        Guarda una lista en la configuración desde una lista como tal, sobreescribiendo el valor actual
        en la configuración
        :param svid: El ID del servidor
        :param name: El nombre de la configuración
        :param elements: La lista a guardar
        :param separator: El separador de la lista para generar un valor a guardar en la configuración
        """
        if not isinstance(elements, list):
            raise RuntimeError('elements argument only supports lists')

        result = separator.join(elements)
        self.set(svid, name, result)

    def add(self, svid, name, value, separator=','):
        """
        Interpretar valores como una lista dada por un separador, y agregar el valor pasado.
        :param svid: El ID del servidor
        :param name: El nombre del valor
        :param value: El valor del a agregar. No es agregado si ya está.
        :param separator: El separador que genera la lista.
        :return: La lista de con el valor agregado
        """
        values = self.get_list(svid, name, separator)
        if value not in values:
            values.append(value)
            self.set_list(svid, name, values, separator)

        return values

    def remove(self, svid, name, value, separator=','):
        """
        Elimina un valor de una lista en la configuración
        :param svid: El ID del servidor
        :param name: El nombre de la configuración
        :param value: El valor a eliminar de la lista
        :param separator: El separador que genera la lista desde el valor de la configuración
        :return: La lista con el valor eliminado
        """
        values = self.get_list(svid, name, separator)
        if value in values:
            values.remove(value)
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


class ServerConfigMgrSingle:
    """
    Shortcut para gestionar la configuración de un sólo servidor
    """
    def __init__(self, mgr, server):
        """
        :param mgr: El gestor de configuración global
        :param server: Una instancia de discord.Server o el ID del servidor específico
        """
        self.svid = server.id if isinstance(server, discord.Server) else server
        self.mgr = mgr

    def get(self, name, default=''):
        """
        Obtiene una configuración
        :param name: El nombre de la configuración
        :param default: El valor predeterminado de la configuración para cuando esta no exista
        :return: El valor de la configuración
        """
        return self.mgr.get(self.svid, name, default)

    def set(self, name, value):
        """
        Cambia el valor de una configuración
        :param name: El nombre de la configuración
        :param value: El nuevo valor de la configuración
        :return: El valor guardado de la configuración
        """
        return self.mgr.set(self.svid, name, value)

    def get_list(self, name, separator=','):
        """
        Genera una lista desde un valor de la configuración
        :param name: EL nombre de la configuración
        :param separator: El separador que genera la lista desde el valor
        :return: La lista generada desde el valor y el separador
        """
        return self.mgr.get_list(self.svid, name, separator)

    def set_list(self, name, elements, separator='.'):
        """
        Une una lista de elementos con un separador y los guarda en la base de datos
        :param name: El nombre de la configuración
        :param elements: La lista a ser guardada en la configuración
        :param separator: El separador que define la separación entre elementos de la lista
        """
        self.mgr.set_list(self.svid, name, elements, separator)

    def add(self, name, value, separator=','):
        """
        Agrega un elemento a una lista
        :param name: El nombre de la configuración
        :param value: El valor a agregar a la lista
        :param separator: El separador del valor que genera una lista
        :return: La lista final con el valor agregado
        """
        return self.mgr.add(self.svid, name, value, separator)

    def remove(self, name, value, separator=','):
        """
        Elimina un elemento de una lista en la configuración
        :param name: El nombre de la configuración
        :param value: El valor a eliminar de la lista
        :param separator: El separador que genera la lista del valor de la configuración
        :return: La lista final con el valor eliminado
        """
        return self.mgr.remove(self.svid, name, value, separator)
