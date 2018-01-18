from ruamel.yaml import YAML

yaml = YAML(typ='safe')
yaml.default_flow_style = False


class StaticConfig:
    """
    Administra un archivo de configuración YAML
    """
    def __init__(self, path, autoload=False):
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
