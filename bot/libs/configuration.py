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
    Administra un archivo de configuración YAML
    """
    def __init__(self, path='config.yml', autoload=False):
        """
        Inicializa la clase.
        :param path: Ubicación del archivo YAML a gestionar
        :param autoload: Cargar dentro de __init__ el archivo
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
        Carga el archivo determinado en el constructor
        :param defaults: Parámetros predeterminados a cargar en el archivo
        :return: Un dict con los datos del archivo y los parámetros predeterminados, de haber sido entregados.
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
        Carga valores por defecto al archivo de configuración
        :param defaults: Un dict con los valores a pasar
        """
        if not isinstance(defaults, dict):
            raise RuntimeError('defaults argument must be a dict instance')

        self.config = {**defaults, **self.config}
        self.save()

    def save(self, reload=False):
        """
        Guarda la configuración actual al archivo y la recarga
        """
        with open(self.path, 'w') as f:
            yaml.dump(self.config, f)

        if reload:
            self.load()

    def get(self, name, default=None):
        """
        Obtiene un valor de la confguración
        :param name: El nombre de la configuración
        :param default: El valor por defecto entregado, de no estar la configuración deseada disponible
        :return: El valor de la configuración deseada
        """
        if name not in self.config and default is None:
            raise KeyError('Key {} not found'.format(name))

        return self.config.get(name, default)

    def set(self, name, val):
        """
        Define y guarda el valor de una configuración y la recarga
        :param name: El nombre del valor a cambiar
        :param val: El valor a guardar
        :return: El valor guardado
        """
        self.config[name] = val
        self.save(reload=True)
        return self.config[name]

    @staticmethod
    def get_config(name, defaults=None):
        """
        Carga de manera simple un archivo en una carpeta llamada "config" en la ubicación actual de ejecución
        :param name: El nombre del archivo
        :param defaults: Valores por defecto a cargar en la configuración
        :return: Una instancia de StaticConfig del archivo cargado
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

    def remove_index(self, svid, name, idx, separator):
        """
        Elimina un valor de una lista en la configuración
        :param svid: El ID del servidor
        :param name: El nombre de la configuración
        :param idx: El índice (partiendo desde cero) del valor de la lista
        :param separator: El separador que genera la lista desde el valor de la configuración
        :return: La lista con el valor eliminado
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

    def remove_index(self, name, idx, separator=','):
        """
        Elimina un elemento de una lista en la configuración
        :param name: El nombre de la configuración
        :param idx: El índice del valor a eliminar de la lista
        :param separator: El separador que genera la lista del valor de la configuración
        :return: La lista final con el valor eliminado
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
