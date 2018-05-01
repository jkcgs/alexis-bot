from io import BytesIO
from os import path
from PIL import Image, ImageFont, ImageDraw
from bot import Command
from bot.utils import pat_usertag

furl = 'https://raw.githubusercontent.com/caarlos0-graveyard/msfonts/master/fonts/impact.ttf'


class Meme(Command):
    __author__ = 'makzk'
    __version__ = '1.0.2'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'meme'
        self.help = 'Genera un meme en base a la imagen de un usuario'
        self.format = 'formatos:\n' \
                      '```' \
                      '$CMD <texto_abajo> (usará tu avatar)\n' \
                      '$CMD [usuario] | <texto_abajo>\n' \
                      '$CMD <usuario> | <texto_arriba> | <texto_abajo>\n' \
                      '$CMD <@mención> [|] <texto_abajo>\n' \
                      '$CMD <@mención> [|] <texto_arriba> | <texto_abajo>' \
                      '```'
        self.isize = 512
        self.mpath = path.join(path.dirname(path.realpath(__file__)), 'impact.ttf')
        self.font = None
        self.font_smaller = None

    async def on_ready(self):
        if not path.exists(self.mpath):
            self.log.info('No se encontró la fuente Impact, descargando...')
            try:
                async with self.http.get(furl) as resp:
                    self.log.info('Fuente Impact descargada')
                    data = await resp.read()
                    with open(self.mpath, 'wb') as f:
                        f.write(data)
                        f.close()
                        self.log.info('Fuente Impact guardada')
            except OSError as e:
                self.log.error('No fue posible guardar el archivo')
                self.log.exception(e)

        self.font = ImageFont.truetype(self.mpath, size=int(self.isize/8))
        self.font_smaller = ImageFont.truetype(self.mpath, size=int(self.isize/14))

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer(self.format)
            return

        if pat_usertag.match(cmd.args[0]):
            args = [f.strip() for f in ' '.join(cmd.no_tags().split(' ')[1:]).split('|')]
            if args[0] == '':
                del args[0]
            args.insert(0, cmd.args[0])
        else:
            args = [f.strip() for f in cmd.no_tags().split('|')]

        if len(args) > 1:
            user = await cmd.get_user(args[0].strip())

            if user is None:
                await cmd.answer('usuario no encontrado')
                return
            upper = args[1].upper() if len(args) > 2 else None
            lower = (args[2] if len(args) > 2 else args[1]).upper()
        else:
            user = cmd.author
            upper = None
            lower = args[0].upper()

        avatar_url = user.avatar_url or user.default_avatar_url
        await cmd.typing()
        async with self.http.get(avatar_url) as resp:
            self.log.debug('Descargando avatar de usuario: %s', avatar_url)
            avatar_data = await resp.read()

        avatar_data = Image.open(BytesIO(avatar_data)).resize((self.isize, self.isize), Image.ANTIALIAS)
        im = Image.new('RGBA', (self.isize, self.isize))
        im.paste(avatar_data, (0, 0))

        self.meme_draw(im, lower, upper=False)
        if upper is not None:
            self.meme_draw(im, upper)

        temp = BytesIO()
        im.save(temp, format='PNG')
        temp = BytesIO(temp.getvalue())  # eliminar bytes nulos

        self.log.debug('Meme generado!')
        await self.bot.send_file(cmd.channel, temp, filename='meme.png', content=cmd.author_name)

    def meme_draw(self, im, text, upper=True):
        draw = ImageDraw.Draw(im)
        selfont = self.font
        sep = int(self.isize / 23)

        # Determine font size
        if len(self.text_splitter(draw, text, self.isize - sep, selfont)) > 2:
            selfont = self.font_smaller

        # Determine text position
        text = '\n'.join(self.text_splitter(draw, text, self.isize - sep, selfont))
        w, h = draw.multiline_textsize(text, selfont)
        xy = (int(self.isize/2)) - int(w/2), (15 if upper else self.isize - sep - h)

        # Draw shadow
        i = 2
        x, y = xy
        draw.multiline_text((x+i, y+i), text, font=selfont, align='center', fill='black')
        draw.multiline_text((x+i, y-i), text, font=selfont, align='center', fill='black')
        draw.multiline_text((x-i, y-i), text, font=selfont, align='center', fill='black')
        draw.multiline_text((x-i, y+i), text, font=selfont, align='center', fill='black')

        # Draw text itself
        draw.multiline_text(xy, text, font=selfont, align='center')

    def text_splitter(self, draw, text, max_width, font):
        lines = []
        words = [f.strip() for f in text.split(' ')]

        line = []
        for word in words:
            w, h = draw.multiline_textsize(' '.join(line) + word, font)
            if w > max_width and len(line) > 0:
                lines.append(' '.join(line))
                line = [word]
            else:
                line.append(word)

        if len(line) > 0:
            lines.append(' '.join(line))

        return lines
