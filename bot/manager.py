import asyncio
import glob
import inspect
import sys
from os import path

from bot import CommandEvent, BotMentionEvent
from bot.utils import get_bot_root
from .logger import log
from .events import parse_event
from .command import Command


class Manager:
    def __init__(self, bot):
        self.bot = bot

        self.cmds = {}
        self.tasks = []
        self.swhandlers = {}
        self.cmd_instances = []
        self.mention_handlers = []

    def load_instances(self):
        """Carga las instancias de las clases de comandos cargadas"""
        self.cmd_instances = []
        for c in Manager.get_mods(self.bot.config.get('ext_modpath', '')):
            self.cmd_instances.append(self.load_module(c))
        self.sort_instances()

        log.info('Se cargaron %i módulos', len(self.cmd_instances))
        log.debug('Comandos cargados: ' + ', '.join(self.cmds.keys()))
        log.debug('Módulos cargados: ' + ', '.join([i.__class__.__name__ for i in self.cmd_instances]))

    def unload_instance(self, name):
        """
        Saca de la memoria una instancia de un módulo, desactivando todos sus comandos y event handlers.
        :param name: El nombre del módulo.
        """
        instance = None
        for i in self.cmd_instances:
            if i.__class__.__name__ == name:
                instance = i

        if instance is None:
            return

        log.debug('Desactivando módulo %s...', name)

        # Unload commands
        cmd_names = [n for n in [instance.name] + instance.aliases if n != '']
        for cmd_name in cmd_names:
            if cmd_name not in self.cmds:
                continue
            else:
                del self.cmds[cmd_name]

        # Unload startswith handlers
        for swname in instance.swhandler:
            if swname not in self.swhandlers:
                continue
            else:
                del self.swhandlers[swname]

        # Unload mention handlers
        for mhandler in self.mention_handlers:
            if mhandler.__class__.__name__ == name:
                self.mention_handlers.remove(mhandler)

        # Hackily unload task
        for task in self.tasks:
            if 'coro=<{}.task()'.format(name) in str(task):
                log.debug('Cancelling task %s', str(task))
                task.cancel()
                self.tasks.remove(task)

        # Remove from instances list
        self.cmd_instances.remove(instance)
        log.info('Módulo "%s" desactivado', name)

    def sort_instances(self):
        self.cmd_instances = sorted(self.cmd_instances, key=lambda i: i.priority)

    def load_module(self, cls):
        """
        Carga un módulo de comando en el bot
        :param cls: Clase-módulo a cargar
        :return: La instancia del módulo cargado
        """

        instance = cls(self.bot)
        if len(instance.db_models) > 0:
            self.bot.db.create_tables(instance.db_models, safe=True)

        if isinstance(instance.default_config, dict):
            self.bot.config.load_defaults(instance.default_config)

        # Comandos
        for name in [instance.name] + instance.aliases:
            if name != '':
                self.cmds[name] = instance

        # Handlers startswith
        for swtext in instance.swhandler:
            if swtext != '':
                log.debug('Registrando sw_handler "%s"', swtext)
                self.swhandlers[swtext] = instance

        # Comandos que se activan con una mención
        if isinstance(instance.mention_handler, bool) and instance.mention_handler:
            self.mention_handlers.append(instance)

        # Call task
        if callable(getattr(instance, 'task', None)):
            loop = asyncio.get_event_loop()
            self.tasks.append(loop.create_task(instance.task()))

        return instance

    def get_handlers(self, name):
        return [getattr(c, name, None) for c in self.cmd_instances if callable(getattr(c, name, None))]

    async def dispatch(self, event_name, **kwargs):
        """
        Llama a funciones de eventos en los módulos cargados.
        :param event_name: El nombre del handler
        :param kwargs: Los parámetros del evento
        """
        if not self.bot.initialized:
            return

        event = None
        if event_name == 'on_message':
            event = parse_event(kwargs.get('message'), self.bot)

        for x in self.get_handlers('pre_' + event_name):
            y = await x(event=event, **kwargs)

            if y is not None and isinstance(y, bool) and not y:
                return

        if event_name == 'on_message':
            await self.handle_message(kwargs.get('message'), event)

        for z in self.get_handlers(event_name):
            await z(**kwargs)

    def dispatch_sync(self, name, force=False, **kwargs):
        """
        Llama a funciones "handlers" en los módulos cargados.
        :param name: El nombre del handler
        :param force: Llamar a los handlers aunque no se haya inicializado al bot
        :param kwargs: Los parámetros del evento
        """
        if not self.bot.initialized and not force:
            return

        for z in self.get_handlers(name):
            z(**kwargs)

    def dispatch_ref(self, name, kwargs):
        if not self.bot.initialized:
            return

        for z in self.get_handlers(name):
            z(kwargs)

    async def handle_message(self, message, event):
        if not self.bot.initialized:
            return

        # Mandar PMs al log
        if event.is_pm and message.content != '':
            if event.self:
                log.info('[PM] (-> %s): %s', message.channel.user, event.text)
            else:
                log.info('[PM] %s: %s', event.author, event.text)

        # Command handler
        try:
            # Comando válido
            if isinstance(event, (CommandEvent, BotMentionEvent)):
                if isinstance(event, CommandEvent):
                    # Actualizar id del último que usó un comando (omitir al mismo bot)
                    if not event.self:
                        self.bot.last_author = message.author.id
                    log.debug('[command] %s: %s', event.author, str(event))

                await event.handle()

            # 'startswith' handlers
            for swtext in self.swhandlers.keys():
                swtextrep = swtext.replace('$PX', event.prefix)
                if message.content.startswith(swtextrep):
                    swhandler = self.swhandlers[swtext]
                    if swhandler.bot_owner_only and not event.bot_owner:
                        continue
                    if swhandler.owner_only and not (event.owner or event.bot_owner):
                        continue
                    if not swhandler.allow_pm and event.is_pm:
                        continue

                    await swhandler.handle(event)
                    if swhandler.swhandler_break:
                        break

        except Exception as e:
            log.exception(e)

    def has_cmd(self, name):
        return name in self.cmds

    def get_cmd(self, name):
        return None if not self.has_cmd(name) else self.cmds[name]

    def get_mod_names(self):
        names = [i.__class__.__name__ for i in self.cmd_instances]
        names.sort()
        return names

    def get_mod(self, name):
        for i in self.cmd_instances:
            if i.__class__.__name__ == name:
                return i

        return None

    def has_mod(self, name):
        return self.get_mod(name) is not None

    def get_by_cmd(self, cmdname):
        for i in self.cmd_instances:
            if i.name == cmdname or cmdname in i.aliases:
                return i

        return None

    async def activate_mod(self, name):
        classes = Manager.get_mods(self.bot.config.get('ext_modpath', ''))
        for cls in classes:
            if cls.__name__ == name:
                log.debug('Cargando módulo "%s"...', name)
                ins = self.load_module(cls)
                if hasattr(ins, 'on_loaded'):
                    log.debug('Llamando on_loaded para "%s"', name)
                    ins.on_loaded()
                if hasattr(ins, 'on_ready'):
                    log.debug('Llamando on_ready para "%s"', name)
                    await ins.on_ready()

                self.cmd_instances.append(ins)
                self.sort_instances()
                log.debug('Módulo "%s" cargado', name)
                return True

        return False

    def cancel_tasks(self):
        if not self.bot.loop.is_closed():
            for task in self.tasks:
                task.cancel()

    def close_http(self):
        loop = asyncio.get_event_loop()
        for i in self.cmd_instances:
            loop.create_task(i.http.close())

    def __getitem__(self, item):
        return self.get_cmd(item)

    def __contains__(self, item):
        return self.has_cmd(item)

    @staticmethod
    def get_mods(ext_path=''):
        """
        Carga los módulos disponibles
        :param ext_path: Una carpeta de módulos externos
        :return: Una lista de instancias de los módulos de comandos
        """
        classes = []

        # Listar módulos internos
        mods_path = path.join(get_bot_root(), 'modules')
        _all = ['modules.' + f for f in Manager.get_mod_files(mods_path)]

        local_ext = path.join(get_bot_root(), 'external_modules')
        if path.isdir(local_ext):
            _all += ['external_modules.' + f for f in Manager.get_mod_files(local_ext)]

        # Listar módulos externos
        if ext_path != '' and path.isdir(ext_path):
            ext_mods = Manager.get_mod_files(ext_path)
            sys.path.append(ext_path)
            _all += ext_mods

        # Cargar todos los módulos
        for imod in _all:
            try:
                mod = __import__(imod, fromlist=[''])
            except ImportError as e:
                log.error('No se pudo cargar un módulo')
                log.exception(e)
                continue

            # Instanciar módulos disponibles
            for name, obj in inspect.getmembers(mod):
                if obj in classes:
                    continue

                if inspect.isclass(obj) and name != 'Command' and issubclass(obj, Command):
                    classes.append(obj)

        return classes

    @staticmethod
    def get_mod_files(fpath):
        """
        Carga una lista de archivos script
        :param fpath: El directorio a analizar
        :return: La lista de ubicaciones de los script, como nombre de módulo
        """
        result = []
        mod_files = glob.iglob(fpath + "/**/*.py", recursive=True)

        for mod_file in mod_files:
            if not path.isfile(mod_file) or not mod_file.endswith('.py') or mod_file.endswith('__init__.py'):
                continue
            result.append(mod_file.replace(fpath + path.sep, '')[:-3].replace(path.sep, '.'))

        return result
