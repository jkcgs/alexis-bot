## Alexis Bot

Para la instalación y uso del bot, creación de comandos y otros detalles, referirse a la [Wiki](https://github.com/jkcgs/alexis-bot/wiki).

### ¿Qué es este bot y qué puedo hacer con el?
Mejor dicho, ¿qué puede hacer el bot por ti?

Actualmente tiene más de 30 comandos, ya sean de diversión, de moderación, y otros.
Algunos comandos de moderación pueden ser encontrados en la lista de [comandos de owner](https://github.com/jkcgs/alexis-bot/wiki/Comandos-de-owner).

Este es un bot modular y programable, puedes crear comandos fácilmente gracias a la estructura simple que ofrece el "framework" creado con el bot.

Por ejemplo, para hacer un comando `ping` sería así:

```python
from alexis import Command

class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'
        self.help = 'Responde al comando *ping*'

    async def handle(self, cmd):
       await cmd.answer('Pong!')
```

En la siguiente imagen se puede ver el resultado del comando, pero más elaborado, en la
forma del script [`ping.py`](https://github.com/jkcgs/alexis-bot/blob/dev/alexis/modules/ping.py)

![](https://i.imgur.com/NX94fva.jpg)

Puedes hacer que el bot responda a un comando, interactuar con una base de datos,
y activar funciones con eventos del bot, por ejemplo, cuando un usuario se une a
un servidor, y darle una bienvenida.

```python
from alexis import Command

class Welcome(Command):
    def __init__(self, bot):
        super().__init__(bot)

    async def on_member_join(self, member):
        chan = self.bot.get_channel('<id_canal>')
        await self.bot.send_message(chan, 'Bienvenido a nuestro servidor, {}!'.format(member.display_name))
```

Esto está ya mucho más elaborado en el script [`welcome.py`](https://github.com/jkcgs/alexis-bot/blob/dev/alexis/modules/owners/welcome.py)
(responde al comando !welcome, y permite cambiar el canal de la bienvenida, y colocar distintos
mensajes aleatorios para enviar).