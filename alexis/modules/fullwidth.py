from alexis import Command


class Fullwidth(Command):
    supported = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&()+,-./:;<=>?@[\\]^`{|}'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'fullwidth'
        self.aliases = ['full']
        self.help = 'Convierte los carácteres soportados a fullwidth y responde con el texto resultante'

    async def handle(self, message, cmd):
        text = [cmd.text, 'QUE WEA COXINO KLO'][int(cmd.text == '')].replace(' ', '   ')
        converted = [chr(0xFEE0 + ord(i)) if i in Fullwidth.supported else i for i in list(text)]
        await cmd.answer(''.join(converted))
