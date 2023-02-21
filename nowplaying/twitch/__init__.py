#!/usr/bin/env python3
''' handle twitch '''

import asyncio
import logging
import threading
import signal
import sys
import time
import traceback

import requests

from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.types import AuthScope
from twitchAPI.oauth import UserAuthenticator, validate_token

import nowplaying.bootstrap
import nowplaying.config
import nowplaying.db
from nowplaying.exceptions import PluginVerifyError
import nowplaying.metadata
import nowplaying.version

import nowplaying.twitch.chat
import nowplaying.twitch.redemptions
import nowplaying.twitch.utils

USER_SCOPE = [
    AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.CHAT_READ,
    AuthScope.CHAT_EDIT
]


class TwitchSupport:  # pylint: disable=too-many-instance-attributes
    ''' handle twitch  '''

    def __init__(self, config=None, stopevent=None):
        self.config = config
        if stopevent:
            self.stopevent = stopevent
        else:
            self.stopevent = threading.Event()
        self.widgets = None
        self.chat = None
        self.redemptions = None
        self.loop = None
        self.twitchlogin = nowplaying.twitch.utils.TwitchLogin(self.config)
        self.tasks = set()

    async def bootstrap(self):
        ''' Authenticate twitch and launch related tasks '''

        signal.signal(signal.SIGINT, self.forced_stop)

        # Now launch the actual tasks...
        if not self.loop:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
        await asyncio.sleep(5)
        task = self.loop.create_task(self.chat.run_chat(self.twitchlogin))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        await asyncio.sleep(5)
        task = self.loop.create_task(
            self.redemptions.run_redemptions(self.twitchlogin, self.chat))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _watch_for_exit(self):
        while not self.stopevent.is_set():
            await asyncio.sleep(1)
        await self.stop()

    def start(self):
        ''' start twitch support '''
        try:
            self.chat = nowplaying.twitch.chat.TwitchChat(
                config=self.config, stopevent=self.stopevent)
            self.redemptions = nowplaying.twitch.redemptions.TwitchRedemptions(
                config=self.config, stopevent=self.stopevent)
            if not self.loop:
                try:
                    self.loop = asyncio.get_running_loop()
                except RuntimeError:
                    self.loop = asyncio.new_event_loop()
            task = self.loop.create_task(self.bootstrap())
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
            task = self.loop.create_task(self._watch_for_exit())
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
            self.loop.run_forever()
        except:  #pylint: disable=bare-except:
            for line in traceback.format_exc().splitlines():
                logging.error(line)
            logging.error('Twitch support crashed')

    def forced_stop(self, signum, frame):  # pylint: disable=unused-argument
        ''' caught an int signal so tell the world to stop '''
        self.stopevent.set()

    async def stop(self):
        ''' stop the twitch support '''
        if self.redemptions:
            await self.redemptions.stop()
        if self.chat:
            await self.chat.stop()
        await asyncio.sleep(1)
        await self.twitchlogin.api_logout()
        self.loop.stop()
        logging.debug('twitchbot stopped')


class TwitchSettings:
    ''' for settings UI '''

    def __init__(self):
        self.widget = None
        self.token = None

    def connect(self, uihelp, widget):  # pylint: disable=unused-argument
        '''  connect twitch '''
        self.widget = widget
        widget.chatbot_username_line.setBuddy(widget.token_lineedit)
        self.widget.token_lineedit.editingFinished.connect(
            self.update_token_name)

    def load(self, config, widget):
        ''' load the settings window '''
        self.widget = widget
        widget.enable_checkbox.setChecked(
            config.cparser.value('twitchbot/enabled', type=bool))
        widget.clientid_lineedit.setText(
            config.cparser.value('twitchbot/clientid'))
        widget.channel_lineedit.setText(
            config.cparser.value('twitchbot/channel'))
        #widget.username_lineedit.setText(
        #    config.cparser.value('twitchbot/username'))
        widget.token_lineedit.setText(
            config.cparser.value('twitchbot/chattoken'))
        widget.secret_lineedit.setText(
            config.cparser.value('twitchbot/secret'))
        self.update_token_name()

    @staticmethod
    def save(config, widget, subprocesses):
        ''' update the twitch settings '''
        oldchannel = config.cparser.value('twitchbot/channel')
        newchannel = widget.channel_lineedit.text()
        oldclientid = config.cparser.value('twitchbot/clientid')
        newclientid = widget.clientid_lineedit.text()
        oldsecret = config.cparser.value('twitchbot/secret')
        newsecret = widget.secret_lineedit.text()
        oldchattoken = config.cparser.value('twitchbot/chattoken')
        newchattoken = widget.token_lineedit.text()
        newchattoken = newchattoken.replace('oauth:', '')

        config.cparser.setValue('twitchbot/enabled',
                                widget.enable_checkbox.isChecked())
        config.cparser.setValue('twitchbot/channel', newchannel)
        config.cparser.setValue('twitchbot/clientid', newclientid)
        config.cparser.setValue('twitchbot/secret', newsecret)

        config.cparser.setValue('twitchbot/chattoken', newchattoken)

        if (oldchannel != newchannel) or (oldclientid != newclientid) or (
                oldsecret != newsecret) or (oldchattoken != newchattoken):
            subprocesses.stop_twitchbot()
            config.cparser.remove('twitchbot/oldusertoken')
            config.cparser.remove('twitchbot/oldrefreshtoken')
            config.cparser.sync()
            time.sleep(5)
            subprocesses.start_twitchbot()

        #config.cparser.setValue('twitchbot/username',
        #                        widget.username_lineedit.text())

    @staticmethod
    def verify(widget):
        ''' verify the settings are good '''
        if not widget.enable_checkbox.isChecked():
            return

        if token := widget.token_lineedit.text():
            if not nowplaying.twitch.utils.qtsafe_validate_token(token):
                raise PluginVerifyError('Twitch bot token is invalid')

    def update_token_name(self):
        ''' update the token name in the UI '''
        token = self.widget.token_lineedit.text()
        if self.token == token:
            return
        if token := token.replace('oauth:', ''):
            if username := nowplaying.twitch.utils.qtsafe_validate_token(
                    token):
                self.widget.chatbot_username_line.setText(username)
            else:
                self.widget.chatbot_username_line.setText('(Invalid token?)')
