#!/usr/bin/env python3
'''
   config file parsing/handling
'''

import os
import pathlib
import sys
import tempfile
import threading

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QSettings


class ConfigFile:  # pylint: disable=too-many-instance-attributes
    ''' read and write to config.ini '''

    _organization = 'com.github.em1ran'
    _application = 'NowPlaying'


    ## Qt doesn't appear to support re-entrant locks or mutexes so
    ## let's use boring old Python threading

    lock = threading.RLock()

    def __init__(self, bundledir=None):

        ConfigFile.lock.acquire()

        self.bundledir = bundledir
        self.cparser = QSettings(ConfigFile._organization,
                                 ConfigFile._application)
        self.interval = float(10)
        self.delay = float(0)
        self.notif = False
        self.local = True
        self.httpenabled = False
        self.httpport = 8899
        self.url = None
        self.file = None
        self.txttemplate = os.path.join(self.bundledir, "templates",
                                        "basic.txt")
        self.httpenabled = False
        self.httpdir = tempfile.gettempdir()
        self.htmltemplate = os.path.join(self.bundledir, "templates",
                                         "basic.htm")

        if sys.platform == "win32":
            self.libpath = os.path.join(pathlib.Path.home(), "My Music",
                                        "_Serato_")
        else:
            self.libpath = os.path.join(pathlib.Path.home(), "Music",
                                        "_Serato_")

        # Tell Qt to match the above

        self.defaults()
        self.get()

    def get(self):
        ''' refresh values '''
        ConfigFile.lock.acquire()

        try:
            self.interval = self.cparser.value('settings/interval', type=float)
        except TypeError:
            pass

        try:
            self.delay = self.cparser.value('settings/delay', type=float)
        except TypeError:
            pass

        try:
            self.notif = self.cparser.value('settings/notif', type=bool)
        except TypeError:
            pass

        try:
            self.local = self.cparser.value('serato/local', type=bool)
        except TypeError:
            pass

        self.libpath = self.cparser.value('serato/libpath')
        self.url = self.cparser.value('serato/url')
        self.file = self.cparser.value('textoutput/file')
        self.txttemplate = self.cparser.value('textoutput/txttemplate')

        try:
            self.httpenabled = self.cparser.value('weboutput/httpenabled',
                                                  type=bool)
        except TypeError:
            pass

        try:
            self.httpport = self.cparser.value('weboutput/httpport', type=int)
        except TypeError:
            pass

        self.httpdir = self.cparser.value('weboutput/httpdir')
        self.htmltemplate = self.cparser.value('weboutput/htmltemplate')
        ConfigFile.lock.release()

    def defaults(self):
        ''' default values for things '''

        settings = QSettings(QSettings.SystemScope,
                             ConfigFile._organization,
                             ConfigFile._application)
        settings.setValue('settings/interval', self.interval)
        settings.setValue('settings/delay', self.delay)
        settings.setValue('settings/notif', self.notif)
        settings.setValue('settings/handler', 'serato')
        settings.setValue('serato/local', self.local)
        settings.setValue('serato/libpath', self.libpath)
        settings.setValue('serato/url', self.url)
        settings.setValue('textoutput/file', self.file)
        settings.setValue('textoutput/txttemplate', self.txttemplate)
        settings.setValue('weboutput/httpenabled', self.httpenabled)
        settings.setValue('weboutput/httpport', self.httpport)
        settings.setValue('weboutput/httpdir', self.httpdir)
        settings.setValue('weboutput/htmltemplate', self.htmltemplate)

    # pylint: disable=too-many-locals, too-many-arguments
    def put(self, local, libpath, url, file, txttemplate, httpport, httpdir,
            httpenabled, htmltemplate, interval, delay, notif):
        ''' Save the configuration file '''

        ConfigFile.lock.acquire()

        self.local = bool(local)
        self.libpath = libpath
        self.url = url
        self.file = file
        self.txttemplate = txttemplate
        self.httpport = int(httpport)
        self.httpdir = httpdir
        self.httpenabled = bool(httpenabled)
        self.htmltemplate = htmltemplate
        self.interval = float(interval)
        self.delay = float(delay)
        self.notif = bool(notif)

        self.cparser.setValue('settings/interval', self.interval)
        self.cparser.setValue('settings/delay', self.delay)
        self.cparser.setValue('settings/notif', self.notif)
        self.cparser.setValue('settings/handler', 'serato')
        self.cparser.setValue('serato/local', self.local)
        self.cparser.setValue('serato/libpath', self.libpath)
        self.cparser.setValue('serato/url', self.url)
        self.cparser.setValue('textoutput/file', self.file)
        self.cparser.setValue('textoutput/txttemplate', self.txttemplate)
        self.cparser.setValue('weboutput/httpenabled', self.httpenabled)
        self.cparser.setValue('weboutput/httpport', self.httpport)
        self.cparser.setValue('weboutput/httpdir', self.httpdir)
        self.cparser.setValue('weboutput/htmltemplate', self.htmltemplate)

        ConfigFile.lock.release()
