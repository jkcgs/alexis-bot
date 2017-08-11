from commands.base.command import Command
import re
from models import Redditor


class RedditorCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'redditor'

    async def handle(self, message):
        cmd = self.parse(message)
        user = cmd.args[0]

        if user.startswith('/u/'):
            user = user[3:]
        if not re.match('^[a-zA-Z0-9_-]*$', user):
            return

        redditor, _ = Redditor.get_or_create(name=user.lower())

        if redditor.posts > 0:
            suffix = 'post' if redditor.posts == 1 else 'posts'
            text = '**/u/{name}** ha creado **{num}** {suffix}.'
            text = text.format(name=user, num=redditor.posts, suffix=suffix)
            await cmd.answer(text)
        else:
            text = '**/u/{name}** no ha creado ningún post.'
            text = text.format(name=user)
            await cmd.answer(text)
