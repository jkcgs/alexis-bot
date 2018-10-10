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
        self.tasks = {}
        self.swhandlers = {}
        self.cmd_instances = []
        self.mention_handlers = []

    def load_instances(self):
        """Loads instances for the command classes loaded"""
        self.cmd_instances = []
        for c in Manager.get_mods(self.bot.config.get('ext_modpath', '')):
            self.cmd_instances.append(self.load_module(c))
        self.sort_instances()

        log.info('%i modules were loaded', len(self.cmd_instances))
        log.debug('Commands loaded: ' + ', '.join(self.cmds.keys()))
        log.debug('Modules loaded: ' + ', '.join([i.__class__.__name__ for i in self.cmd_instances]))

    def unload_instance(self, name):
        """
        Removes from memory a module instance, and disabling its commands and event handlers.
        :param name: Module's name.
        """
        instance = None
        for i in self.cmd_instances:
            if i.__class__.__name__ == name:
                instance = i

        if instance is None:
            return

        log.debug('Disabling %s module...', name)

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
        for task_name in list(self.tasks.keys()):
            if task_name.startswith(name+'.'):
                log.debug('Cancelling task %s', task_name)
                self.tasks[task_name].cancel()
                del self.tasks[task_name]

        # Remove from instances list
        self.cmd_instances.remove(instance)
        log.info('"%s" module disabled', name)

    def sort_instances(self):
        self.cmd_instances = sorted(self.cmd_instances, key=lambda i: i.priority)

    def load_module(self, cls):
        """
        Loads a command module into the bot
        :param cls: The module class to load
        :return: A module class' instance
        """

        instance = cls(self.bot)
        if len(instance.db_models) > 0:
            self.bot.db.create_tables(instance.db_models, safe=True)

        if isinstance(instance.default_config, dict):
            self.bot.config.load_defaults(instance.default_config)

        # Commands
        for name in [instance.name] + instance.aliases:
            if name != '':
                self.cmds[name] = instance

        # Startswith handlers
        for swtext in instance.swhandler:
            if swtext != '':
                log.debug('Registering starts-with handler "%s"', swtext)
                self.swhandlers[swtext] = instance

        # Commands activated with mentions
        if isinstance(instance.mention_handler, bool) and instance.mention_handler:
            self.mention_handlers.append(instance)

        if self.bot.user:
            self.create_tasks(instance)

        return instance

    def create_tasks(self, instance=None):
        instances = self.cmd_instances if instance is None else [instance]

        for instance in instances:
            # Scheduled (repetitive) tasks
            if isinstance(instance.schedule, list):
                for (task, seconds) in instance.schedule:
                    self.bot.schedule(task, seconds)
            elif isinstance(instance.schedule, tuple):
                task, seconds = instance.schedule
                self.bot.schedule(task, seconds)

    async def run_task(self, task, time=0):
        """
        Runs a task on a given interval
        :param task: The task function
        :param time: The time in seconds to repeat the task
        """
        while 1:
            try:
                await task()
            except Exception as e:
                log.exception(e)
            finally:
                if time == 0 or self.bot.is_closed:
                    break
                await asyncio.sleep(time)
                if self.bot.is_closed:
                    break

    def schedule(self, task, time=0, force=False):
        """
        Adds a task to the loop to be run every *time* seconds.
        :param task: The task function
        :param time: The time in seconds to repeat the task
        :param force: What to do if the task was already created. If True, the task is cancelled and created again.
        """
        if time < 0:
            raise RuntimeError('Task interval time must be positive')

        task_name = '{}.{}'.format(task.__self__.__class__.__name__, task.__name__)
        if task_name in self.tasks:
            if not force:
                return
            self.tasks[task_name].cancel()

        task_ins = self.bot.loop.create_task(self.run_task(task, time))
        self.tasks[task_name] = task_ins

        if time > 0:
            log.debug('Task "%s" created, repeating every %i seconds', task_name, time)
        else:
            log.debug('Task "%s" created, running once', task_name)

        return task_ins

    def get_handlers(self, name):
        return [getattr(c, name, None) for c in self.cmd_instances if callable(getattr(c, name, None))]

    async def dispatch(self, event_name, **kwargs):
        """
        Calls event methods on loaded methods.
        :param event_name: Event handler name
        :param kwargs: Event parameters
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
        Synchronously (without event loop) calls "handlers" methods on loaded modules.
        :param name: Handler name
        :param force: Call handlers even if the bot is not initialized
        :param kwargs: Event parameters
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

        # Log PMs
        if event.is_pm and message.content != '':
            if event.self:
                log.info('[PM] (-> %s): %s', message.channel.user, event.text)
            else:
                log.info('[PM] %s: %s', event.author, event.text)

        # Command handler
        try:
            # Valid command
            if isinstance(event, (CommandEvent, BotMentionEvent)):
                if isinstance(event, CommandEvent):
                    # Update ID of the last one who used a command (omitting the bot)
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
                log.debug('Loading "%s" module...', name)
                ins = self.load_module(cls)
                if hasattr(ins, 'on_loaded'):
                    log.debug('Calling on_loaded for "%s"', name)
                    ins.on_loaded()
                if hasattr(ins, 'on_ready'):
                    log.debug('Calling on_ready for "%s"', name)
                    await ins.on_ready()

                self.cmd_instances.append(ins)
                self.sort_instances()
                log.debug('"%s" module loaded', name)
                return True

        return False

    def cancel_tasks(self):
        for task_name in list(self.tasks.keys()):
            self.tasks[task_name].cancel()
            del self.tasks[task_name]

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
        Loads available modules
        :param ext_path: An external modules folder
        :return: An instances list of command modules
        """
        classes = []

        # List internal modules
        mods_path = path.join(get_bot_root(), 'modules')
        _all = ['modules.' + f for f in Manager.get_mod_files(mods_path)]

        local_ext = path.join(get_bot_root(), 'external_modules')
        if path.isdir(local_ext):
            _all += ['external_modules.' + f for f in Manager.get_mod_files(local_ext)]

        # List external modules
        if ext_path != '' and path.isdir(ext_path):
            ext_mods = Manager.get_mod_files(ext_path)
            sys.path.append(ext_path)
            _all += ext_mods

        # Load all modules
        for imod in _all:
            try:
                mod = __import__(imod, fromlist=[''])
            except ImportError as e:
                log.error('Could not load a module')
                log.exception(e)
                continue

            # Instantiate loaded modules
            for name, obj in inspect.getmembers(mod):
                if obj in classes:
                    continue

                if inspect.isclass(obj) and name != 'Command' and issubclass(obj, Command):
                    classes.append(obj)

        return classes

    @staticmethod
    def get_mod_files(fpath):
        """
        Loads a script files list
        :param fpath: The directory to scan
        :return: The list of script paths, as a module name
        """
        result = []
        mod_files = glob.iglob(fpath + "/**/*.py", recursive=True)

        for mod_file in mod_files:
            if not path.isfile(mod_file) or not mod_file.endswith('.py') or mod_file.endswith('__init__.py'):
                continue
            result.append(mod_file.replace(fpath + path.sep, '')[:-3].replace(path.sep, '.'))

        return result
