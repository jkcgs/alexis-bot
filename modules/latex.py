from io import BytesIO
from PIL import Image, ImageOps

from bot import Command, categories
from discord import File

api_url = 'https://www.quicklatex.com/latex3.f'


class LaTeX(Command):
    __author__ = 'makzk'
    __version__ = '0.0.1'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'latex'
        self.aliases = ['tex']
        self.category = categories.UTILITY

    async def handle(self, cmd):
        if cmd.text == '':
            return await cmd.answer('$[latex-format]')

        formula = cmd.text.replace(' ', '')
        params = {
            'fsize': '24px', 'fcolor': '000000', 'mode': 0, 'out': 1, 'bcolor': 'ffffff',
            'formula': '\\begin{align*}\n%s\n\\end{align*}' % formula
        }

        await cmd.typing()
        async with self.http.post(api_url, data=params) as r:
            if r.status != 200:
                return await cmd.answer('$[latex-error-status] ({})'.format(r.status))

            result = (await r.text()).split('\n')
            if len(result) > 2:
                return await cmd.answer('$[latex-error-server]', locales={'error': result[2]})

            result_url = result[1].split(' ')[0]
            async with self.http.get(result_url) as image_r:
                if image_r.status != 200:
                    return await cmd.answer('$[latex-error-image]')

                image_border_data = BytesIO()
                image_data = Image.open(BytesIO(await image_r.read()))
                image_border = ImageOps.expand(image_data, border=10, fill='white')
                image_border.save(image_border_data, format='PNG')
                image_border_data = BytesIO(image_border_data.getvalue())

                return await cmd.answer(file=File(image_border_data, filename='formula.png'))
