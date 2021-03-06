import logging

from pajbot.modules import QuestModule
from pajbot.modules.quests import BaseQuest
from pajbot.managers import RedisManager
from pajbot.models.handler import HandlerManager
from pajbot.streamhelper import StreamHelper

from numpy import random

log = logging.getLogger(__name__)

class TypeEmoteQuestModule(BaseQuest):

    ID = 'quest-' + __name__.split('.')[-1]
    NAME = 'Type X emote Y times'
    DESCRIPTION = 'A user needs to type a specific emote Y times to complete this quest.'
    PARENT_MODULE = QuestModule

    LIMIT = 100
    REWARD = 5

    def __init__(self):
        super().__init__()
        self.current_emote_key = '{streamer}:current_quest_emote'.format(streamer=StreamHelper.get_streamer())
        self.current_emote = '???'
        self.progress = {}

    def on_message(self, source, message, emotes, whisper, urls, event):
        for emote in emotes:
            if emote['code'] == self.current_emote:
                user_progress = self.get_user_progress(source.username, default=0) + 1

                if user_progress > self.LIMIT:
                    log.debug('{} has already complete the quest. Moving along.'.format(source.username))
                    # no need to do more
                    return

                redis = RedisManager.get()

                if user_progress == self.LIMIT:
                    source.award_tokens(self.REWARD, redis=redis)

                self.set_user_progress(source.username, user_progress, redis=redis)
                return

    def start_quest(self):
        HandlerManager.add_handler('on_message', self.on_message)

        redis = RedisManager.get()

        self.load_progress(redis=redis)
        self.load_data(redis=redis)

    def load_data(self, redis=None):
        if redis is None:
            redis = RedisManager.get()

        self.current_emote = redis.get(self.current_emote_key)
        if self.current_emote is None:
            # randomize an emote
            global_twitch_emotes = self.bot.emotes.get_global_emotes()
            self.current_emote = random.choice(global_twitch_emotes)
            redis.set(self.current_emote_key, self.current_emote)
        else:
            self.current_emote = self.current_emote

    def stop_quest(self):
        HandlerManager.remove_handler('on_message', self.on_message)

        redis = RedisManager.get()

        self.reset_progress(redis=redis)
        redis.delete(self.current_emote_key)

    def get_objective(self):
        return 'Use the {} emote {} times'.format(self.current_emote, self.LIMIT)

    def enable(self, bot):
        self.bot = bot
