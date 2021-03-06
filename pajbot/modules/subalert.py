import logging
import re

from pajbot.modules import BaseModule, ModuleSetting
from pajbot.models.command import Command
from pajbot.models.handler import HandlerManager

log = logging.getLogger(__name__)


class SubAlertModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Subscription Alert (text)'
    DESCRIPTION = 'Prints a message in chat for someone who subscribed'
    CATEGORY = 'Feature'
    ENABLED_DEFAULT = True
    SETTINGS = [
            ModuleSetting(
                key='new_sub',
                label='New sub',
                type='text',
                required=True,
                placeholder='Sub hype! {username} just subscribed PogChamp',
                default='Sub hype! {username} just subscribed PogChamp',
                constraints={
                    'min_str_len': 10,
                    'max_str_len': 400,
                    }),
            ModuleSetting(
                key='resub',
                label='Resub',
                type='text',
                required=True,
                placeholder='Resub hype! {username} just subscribed, {num_months} months in a row PogChamp <3 PogChamp',
                default='Resub hype! {username} just subscribed, {num_months} months in a row PogChamp <3 PogChamp',
                constraints={
                    'min_str_len': 10,
                    'max_str_len': 400,
                    }),
                ]

    def __init__(self):
        super().__init__()
        self.new_sub_regex = re.compile('^(\w+) just subscribed!')
        self.resub_regex = re.compile('^(\w+) subscribed for (\d+) months in a row!')

    def on_new_sub(self, user):
        """
        A new user just subscribed.
        Send the event to the websocket manager, and send a customized message in chat.
        Also increase the number of active subscribers in the database by one.
        """

        self.bot.kvi['active_subs'].inc()

        payload = {'username': user.username_raw}
        self.bot.websocket_manager.emit('new_sub', payload)

        self.bot.say(self.get_phrase('new_sub', **payload))

    def on_resub(self, user, num_months):
        """
        A user just re-subscribed.
        Send the event to the websocket manager, and send a customized message in chat.
        """

        payload = {'username': user.username_raw, 'num_months': num_months}
        self.bot.websocket_manager.emit('resub', payload)

        self.bot.say(self.get_phrase('resub', **payload))

    def on_message(self, source, message, emotes, whisper, urls, event):
        if whisper is False and source.username == 'twitchnotify':
            # Did twitchnotify tell us about a new sub?
            m = self.new_sub_regex.search(message)
            if m:
                username = m.group(1)
                self.on_new_sub(self.bot.users[username])
            else:
                # Did twitchnotify tell us about a resub?
                m = self.resub_regex.search(message)
                if m:
                    username = m.group(1)
                    num_months = m.group(2)
                    self.on_resub(self.bot.users[username], int(num_months))

    def enable(self, bot):
        HandlerManager.add_handler('on_message', self.on_message)
        self.bot = bot

    def disable(self, bot):
        HandlerManager.remove_handler('on_message', self.on_message)
