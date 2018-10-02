from io import BytesIO
from os import path
from PIL import Image
from bot import Command, categories
from bot.utils import parse_tag


class ShipperUwU(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ship'
        self.help = '$[ship-help]'
        self.format = '$[ship-format]'
        self.allow_pm = False
        self.category = categories.IMAGES

    async def handle(self, cmd):
        if cmd.argc != 2:
            await cmd.answer('$[format]: $[ship-format]')
            return

        # Get mentions in the same order as they were sent
        item1 = await get_details(cmd, cmd.args[0])
        item2 = await get_details(cmd, cmd.args[1])
        if item1 is None or item2 is None:
            await cmd.answer('$[format]: $[ship-format]')
            return

        item1_name, item1_url = item1
        item2_name, item2_url = item2

        # Check if users are not the same
        if item1_url == item2_url:
            await cmd.answer('$[ship-err-same]')
            return

        await cmd.typing()
        self.log.debug('Generating picture...')

        # Download profile pictures
        async with self.http.get(item1_url) as resp:
            self.log.debug('Downloading user1 avatar - %s', item1_url)
            user1_avatar = await resp.read()
        async with self.http.get(item2_url) as resp:
            self.log.debug('Downloading user2 avatar - %s', item2_url)
            user2_avatar = await resp.read()

        # Open and resize pictures
        user1_img = Image.open(BytesIO(user1_avatar)).resize((512, 512), Image.ANTIALIAS)
        user2_img = Image.open(BytesIO(user2_avatar)).resize((512, 512), Image.ANTIALIAS)

        # Open the heart <3
        heart_img = Image.open(path.join(path.dirname(path.realpath(__file__)), 'heart.png'))

        # Create picture
        result = Image.new('RGBA', (1536, 512))
        result.paste(user1_img, (0, 0))
        result.paste(heart_img, (512, 0))
        result.paste(user2_img, (1024, 0))

        # Save picture in memory
        temp = BytesIO()
        result.save(temp, format='PNG')
        temp = BytesIO(temp.getvalue())  # eliminar bytes nulos
        self.log.debug('Image ready!')

        # Create ship name and send picture
        ship_name = item1_name[0:int(len(item1_name) / 2)] + item2_name[int(len(item2_name) / 2):]
        msg = cmd.lang.format('$[ship-msg]', locales={'ship_name': ship_name})
        await self.bot.send_file(cmd.message.channel, temp, filename='ship.png', content=msg)


async def get_details(cmd, text):
    item = parse_tag(text)
    if item is None or item['type'] == 'user':
        user = await (cmd.get_user(text) if item is None else cmd.get_user(item['id']))
        return None if user is None else (user.display_name, (user.avatar_url or user.default_avatar_url))
    elif item['type'] == 'emoji':
        url = 'https://discordapp.com/api/emojis/{}.{}'
        return item['name'], url.format(item['id'], 'gif' if item['animated'] else 'png')
    else:
        return None
