from bot import Command
import random
import hashlib


class Rate(Command):
    special1 = ['31a43824ffc1d22d81918aedae1f53ed', 'f25581a8349563f80b4f9c19451a00d0',
                '958c8a5c697109ff5445fabe10dfe3bb', 'aaf5fd9b00bc749fc816f749cd0d40ef']
    special2 = ['db9db76c7fc568c338b0c8a88714f969', 'fe2940df414d84256c4c2d01f8bf3a61',
                '7a6ad21630ced6b3073ccb28cf18db04', 'cf96adbe2c7e8ddbbc8008148283b26c']

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'rate'
        self.help = 'Evalúa algo'

    async def handle(self, cmd):
        text = [cmd.text, cmd.author_name][int(cmd.text == '')]
        t_user = await cmd.get_user(text)

        if random.random() > .90:
            if cmd.argc == 1 and t_user is not None:
                m = cmd.message.mentions[0]
                hashi = hashlib.md5()
                hashi.update(m.id.encode('utf-8'))
                hid = hashi.hexdigest()
                # no si no es niuna weá transfuga wn sólo estoy ocultando los ids de los locos especiales jaj
                if hid in Rate.special1:
                    await cmd.answer('a {} de un 1 a un 100, le doy :$'.format(text))
                elif hid in Rate.special2:
                    await cmd.answer('uff men gr8 i r8 8/8')
                elif m.id == self.bot.user.id:
                    await cmd.answer('lo mejor del mundo, obvio')
                else:
                    await cmd.answer('no me mandis weas xfa')
            else:
                await cmd.answer('penca tu weá xd')
        else:
            rating = '{:.1f}'.format(random.random()*100)
            await cmd.answer('a {} le doy {}/100'.format(text, rating))
