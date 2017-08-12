from commands.base.command import Command
from models import Meme


class MemesSet(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'set'
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) < 2:
            await cmd.answer('Formato: !set <nombre> <contenido>')
            return

        meme_name = cmd.args[0]
        meme_value = ' '.join(cmd.args[1:])

        meme, created = Meme.get_or_create(name=meme_name)
        meme.content = meme_value
        meme.save()

        if created:
            msg = 'Valor **{name}** creado'.format(name=meme_name)
            self.bot.log.info('Meme %s creado con valor: "%s"', meme_name, meme_value)
        else:
            msg = 'Valor **{name}** actualizado'.format(name=meme_name)
            self.bot.log.info('Meme %s actualizado a: "%s"', meme_name, meme_value)

        await cmd.answer(msg)


class MemesUnset(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'unset'
        self.owner_only = True

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: !unset <nombre>')
            return

        meme_name = cmd.args[0]

        try:
            meme = Meme.get(name=meme_name)
            meme.delete_instance()
            msg = 'Valor **{name}** eliminado'.format(name=meme_name)
            await cmd.answer(msg)
            self.bot.log.info('Meme %s eliminado', meme_name)
        except Meme.DoesNotExist:
            msg = 'El valor con nombre {name} no existe'.format(name=meme_name)
            await cmd.answer(msg)

        await cmd.answer(msg)


class MemeList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'list'

    async def handle(self, message, cmd):
        namelist = []
        for item in Meme.select().iterator():
            namelist.append(item.name)

        word = 'valor' if len(namelist) == 1 else 'valores'
        resp = 'Hay {} {}: {}'.format(len(namelist), word, ', '.join(namelist))
        await cmd.answer(resp)


class MemeSuperList(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = '!list'
        self.owner_only = True

    async def handle(self, message, cmd):
        memelist = []
        for item in Meme.select().iterator():
            memelist.append("- {}: {}".format(item.name, item.content))

        num_memes = len(memelist)
        if num_memes == 0:
            await cmd.answer('No hay valores disponibles')
            return

        word = 'valor' if num_memes == 1 else 'valores'
        resp = 'Hay {} {}:'.format(num_memes, word)
        await cmd.answer(resp)

        # Separar lista de memes en mensajes con menos de 2000 carácteres
        resp_list = ''
        for meme in memelist:
            if len('```{}\n{}```'.format(resp_list, meme)) > 2000:
                await cmd.answer('```{}```'.format(resp_list))
                resp_list = ''
            else:
                resp_list = '{}\n{}'.format(resp_list, meme)

        # Enviar lista restante
        if resp_list != '':
            await cmd.answer('```{}```'.format(resp_list))