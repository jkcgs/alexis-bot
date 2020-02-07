from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from discord import File

from bot import Command, categories
from bot.regex import pat_usertag

furl = 'https://github.com/sophilabs/macgifer/raw/master/static/font/impact.ttf'


class Meme(Command):
    __author__ = 'makzk'
    __version__ = '1.0.3'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'meme'
        self.help = '$[memes-help]'
        self.category = categories.IMAGES
        self.format = '$[format]:```$[memes-format-1]\n$[memes-format-2]\n$[memes-format-3]\n' \
                      '$[memes-format-4]\n$[memes-format-5]```'
        self.isize = 512
        self.mpath = None
        self.font = None
        self.font_smaller = None

    async def on_ready(self):
        self.mpath = await self.mgr.download('impact.ttf', furl)
        if self.mpath is None:
            self.log.warn('Could not retrieve the font')
            return

        try:
            self.font = ImageFont.truetype(self.mpath, size=int(self.isize/8))
            self.font_smaller = ImageFont.truetype(self.mpath, size=int(self.isize/14))
        except OSError as e:
            if str(e) == 'unknown file format':
                self.log.warn('The cached or downloaded font is invalid. '
                              'Try deleting "cache/impact.ttf" and running the bot again.')

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer(self.format)
            return

        if self.font is None:
            await cmd.answer('$[memes-disabled]')
            return

        if pat_usertag.match(cmd.args[0]):
            args = [f.strip() for f in ' '.join(cmd.no_tags().split(' ')[1:]).split('|')]
            if args[0] == '':
                del args[0]
            args.insert(0, cmd.args[0])
        else:
            args = [f.strip() for f in cmd.no_tags().split('|')]

        if len(args) > 1:
            user = cmd.get_member_or_author(args[0].strip())

            if user is None:
                await cmd.answer('$[user-not-found]')
                return
            upper = args[1].upper() if len(args) > 2 else None
            lower = (args[2] if len(args) > 2 else args[1]).upper()
        else:
            user = cmd.author
            upper = None
            lower = args[0].upper()

        await cmd.typing()
        self.log.debug('Downloading user avatar: %s', str(user.avatar_url))
        avatar_data = await user.avatar_url.read()

        avatar_data = Image.open(BytesIO(avatar_data)).resize((self.isize, self.isize), Image.ANTIALIAS)
        im = Image.new('RGBA', (self.isize, self.isize))
        im.paste(avatar_data, (0, 0))

        self.meme_draw(im, lower, upper=False)
        if upper is not None:
            self.meme_draw(im, upper)

        temp = BytesIO()
        im.save(temp, format='PNG')
        temp = BytesIO(temp.getvalue())  # eliminar bytes nulos

        self.log.debug('Meme generated!')
        await cmd.channel.send(cmd.author_name, file=File(temp, filename='meme.png'))

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
