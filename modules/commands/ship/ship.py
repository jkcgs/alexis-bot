from io import BytesIO
from os import path
from PIL import Image
from modules.base.command import Command


class AltoEn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ship'
        self.help = 'Forma parejas entre dos usuarios'
        self.allow_pm = False

    async def handle(self, message, cmd):
        if len(cmd.args) != 2 or len(message.mentions) != 2:
            await cmd.answer('Formato: !ship @mención1 @mención2')
            return

        user1 = message.mentions[0].display_name
        user2 = message.mentions[1].display_name
        if user1 == user2:
            await cmd.answer('Sólo hago parejas con personas distintas, bueno? :3')
            return

        await cmd.typing()

        # Descargar avatares
        avatar1_url = message.mentions[0].avatar_url.replace('.webp', '.png')
        avatar2_url = message.mentions[1].avatar_url.replace('.webp', '.png')
        async with self.http.get(avatar1_url) as resp:
            user1_avatar = await resp.read()
        async with self.http.get(avatar2_url) as resp:
            user2_avatar = await resp.read()

        # Abrir avatares y cambiar su tamaño
        user1_img = Image.open(BytesIO(user1_avatar)).resize((512, 512), Image.ANTIALIAS)
        user2_img = Image.open(BytesIO(user2_avatar)).resize((512, 512), Image.ANTIALIAS)

        # Abrir el corazón
        heart_img = Image.open(path.join(path.dirname(path.realpath(__file__)), 'heart.png'))

        # Crear imagen resultante
        result = Image.new('RGBA', (1536, 512))
        result.paste(user1_img, (0, 0))
        result.paste(heart_img, (512, 0))
        result.paste(user2_img, (1024, 0))

        # Guardar imagen en un array
        temp = BytesIO()
        result.save(temp, format='PNG')
        temp = BytesIO(temp.getvalue())  # eliminar bytes nulos

        # Generar nombre del ship y enviar con la imagen
        ship_name = user1[0:int(len(user1) / 2)] + user2[int(len(user2) / 2):]
        await self.bot.send_file(message.channel, temp, filename='ship.png',
                                 content='Formando la pareja: **{}**'.format(ship_name))
