#!/usr/bin/env python3
'''
CHANGELOG:
* Fix for issue where Settings UI window did not fit on smaller resolution screens.
    The window is now re-sizeable and scrolling is enabled.
* Augmented the suffix and prefix functionality. The Artist and Song data chunks now
    can have independent suffixes and prefixes.
* Added version number to Settings window title bar.
'''

# pylint: disable=no-name-in-module, global-statement
# pylint: disable=too-many-instance-attributes, too-few-public-methods
# pylint: disable=too-many-lines

import configparser
import os
import html
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from socketserver import ThreadingMixIn
from string import Template
import sys
import time

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import \
                            QAction, \
                            QApplication, \
                            QCheckBox, \
                            QErrorMessage, \
                            QFileDialog, \
                            QFrame, \
                            QHBoxLayout, \
                            QLabel, \
                            QLineEdit, \
                            QMenu, \
                            QPushButton, \
                            QRadioButton, \
                            QScrollArea,\
                            QSystemTrayIcon,\
                            QVBoxLayout, \
                            QWidget
from PyQt5.QtGui import QIcon, QFont

import nowplaying.serato

__author__ = "Ely Miranda"
__version__ = "1.5.0"
__license__ = "MIT"

# define global variables
INITIALIZED = PAUSED = False
CURRENTARTIST = ''
CURRENTSONG = ''

# set paths for bundled files
if getattr(sys, 'frozen', False) and sys.platform == "darwin":
    BUNDLE_DIR = os.path.abspath(os.path.dirname(
        sys.executable))  # sys._MEIPASS
else:
    BUNDLE_DIR = os.path.abspath(os.path.dirname(__file__))

CONFIG_FILE = os.path.abspath(os.path.join(BUNDLE_DIR, "bin", "config.ini"))
ICONFILE = os.path.abspath(os.path.join(BUNDLE_DIR, "bin", "icon.ico"))

# print(CONFIG_FILE)
# create needed object instances
CONFIG = configparser.ConfigParser()
QAPP = QApplication([])
QAPP.setQuitOnLastWindowClosed(False)

TRAY = None


class ConfigFile:
    ''' read and write to config.ini '''
    def __init__(self, cparser, cfile):
        self.cparser = cparser
        self.cfile = cfile

        try:
            self.cparser.read(self.cfile)
            self.cparser.sections()

            try:
                self.local = CONFIG.getboolean('Settings', 'local')
            except ValueError:
                self.local = True

            self.libpath = CONFIG.get('Settings', 'libpath')
            self.url = CONFIG.get('Settings', 'url')
            self.file = CONFIG.get('Settings', 'file')

            try:
                self.httpenabled = CONFIG.getboolean('Settings',
                                                     'httpenabled',
                                                     fallback=False)
            except ValueError:
                self.httpenabled = False

            try:
                self.httpport = CONFIG.getint('Settings',
                                              'httpport',
                                              fallback=8899)
            except ValueError:
                self.httpport = 8899

            self.httpdir = CONFIG.get('Settings',
                                      'httpdir',
                                      fallback=os.path.sep + 'tmp')

            self.htmltemplate = CONFIG.get('Settings',
                                           'htmltemplate',
                                           fallback=os.path.join(
                                               BUNDLE_DIR, "bin",
                                               "template.htm"))

            try:
                self.interval = CONFIG.getfloat('Settings', 'interval')
            except ValueError:
                self.interval = float(10)

            try:
                self.delay = CONFIG.getfloat('Settings', 'delay')
            except ValueError:
                self.delay = float(0)

            try:
                self.multi = CONFIG.getboolean('Settings', 'multi')
            except ValueError:
                self.multi = False

            try:
                self.quote = CONFIG.getboolean('Settings', 'quote')
            except ValueError:
                self.quote = False

            self.a_pref = CONFIG.get('Settings', 'a_pref').replace("|_0", " ")
            self.a_suff = CONFIG.get('Settings', 'a_suff').replace("|_0", " ")
            self.s_pref = CONFIG.get('Settings', 's_pref').replace("|_0", " ")
            self.s_suff = CONFIG.get('Settings', 's_suff').replace("|_0", " ")

            try:
                self.notif = CONFIG.getboolean('Settings', 'notif')
            except ValueError:
                self.notif = False

        except configparser.NoOptionError:
            pass

    # pylint: disable=too-many-locals, too-many-arguments
    def put(self, local, libpath, url, file, httpport, httpdir, httpenabled,
            htmltemplate, interval, delay, multi, quote, a_pref, a_suff,
            s_pref, s_suff, notif):
        ''' Save the configuration file '''
        self.cparser.set('Settings', 'local', local)
        self.cparser.set('Settings', 'libpath', libpath)
        self.cparser.set('Settings', 'url', url)
        self.cparser.set('Settings', 'file', file)
        self.cparser.set('Settings', 'httpenabled', str(httpenabled))
        self.cparser.set('Settings', 'httpport', str(httpport))
        self.cparser.set('Settings', 'httpdir', httpdir)
        self.cparser.set('Settings', 'htmltemplate', htmltemplate)
        self.cparser.set('Settings', 'interval', interval)
        self.cparser.set('Settings', 'delay', delay)
        self.cparser.set('Settings', 'multi', str(multi))
        self.cparser.set('Settings', 'quote', str(quote))
        self.cparser.set('Settings', 'a_pref', a_pref)
        self.cparser.set('Settings', 'a_suff', a_suff)
        self.cparser.set('Settings', 's_pref', s_pref)
        self.cparser.set('Settings', 's_suff', s_suff)
        self.cparser.set('Settings', 'notif', str(notif))

        cffh = open(self.cfile, 'w')
        self.cparser.write(cffh)
        cffh.close()


# settings UI
class SettingsUI:
    ''' create settings form window '''

    # pylint: disable=too-many-statements, invalid-name
    def __init__(self, conf, conffile, icn):
        self.conf = conf
        self.conffile = conffile
        self.icon = icn
        self.scroll = QScrollArea()
        self.window = QWidget()
        self.separator1 = QFrame()
        self.separator2 = QFrame()
        self.separator3 = QFrame()
        self.scroll.setWindowIcon(QIcon(icn))
        self.layoutV = QVBoxLayout()
        self.layoutH0 = QHBoxLayout()
        self.layoutH0a = QHBoxLayout()
        self.layoutH1 = QHBoxLayout()
        self.layoutH2 = QHBoxLayout()
        self.layoutH3 = QHBoxLayout()
        self.layoutH4 = QHBoxLayout()
        self.layoutH5 = QHBoxLayout()
        self.layoutH6a = QHBoxLayout()
        self.layoutH6b = QHBoxLayout()
        self.layoutH6c = QHBoxLayout()
        self.layoutH6d = QHBoxLayout()
        self.layoutHttpEnableCheckbox = QHBoxLayout()
        self.layoutHttpPort = QHBoxLayout()
        self.layoutHttpHtmlTemplate = QHBoxLayout()
        self.layoutHttpServerPath = QHBoxLayout()

        self.fBold = QFont()
        self.fBold.setBold(True)
        self.scroll.setWindowTitle(f'Now Playing v{__version__} - Settings')

        self.scroll.setWidgetResizable(True)
        self.scroll.setWindowFlag(Qt.CustomizeWindowHint, True)
        self.scroll.setWindowFlag(Qt.WindowCloseButtonHint, False)
        # self.scroll.setWindowFlag(Qt.WindowMinMaxButtonsHint, False)
        self.scroll.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.scroll.setWidget(self.window)
        self.scroll.setMinimumWidth(825)
        self.scroll.resize(825, 1024)

        # error section
        self.errLabel = QLabel()
        self.errLabel.setStyleSheet('color: red')
        # remote
        self.localLabel = QLabel('Track Retrieval Mode')
        self.localLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.localLabel)
        self.remoteDesc = QLabel(
            'Local mode (default) uses Serato\'s local history log for track data.\
\nRemote mode retrieves remote track data from Serato Live Playlists.')
        self.remoteDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.remoteDesc)
        # radios
        self.localRadio = QRadioButton('Local')
        self.localRadio.setChecked(True)
        self.localRadio.toggled.connect(
            lambda: self.on_radiobutton_select(self.localRadio))
        self.localRadio.setMaximumWidth(60)

        self.remoteRadio = QRadioButton('Remote')
        self.remoteRadio.toggled.connect(
            lambda: self.on_radiobutton_select(self.remoteRadio))
        self.layoutH0.addWidget(self.localRadio)
        self.layoutH0.addWidget(self.remoteRadio)
        self.layoutV.addLayout(self.layoutH0)

        # library path
        self.libLabel = QLabel('Serato Library Path')
        self.libLabel.setFont(self.fBold)
        self.libDesc = QLabel(
            'Location of Serato library folder.\ni.e., \\THE_PATH_TO\\_Serato_'
        )
        self.libDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.libLabel)
        self.layoutV.addWidget(self.libDesc)
        self.libButton = QPushButton('Browse for folder')
        self.layoutH0a.addWidget(self.libButton)
        self.libButton.clicked.connect(self.on_libbutton_clicked)
        self.libEdit = QLineEdit()
        self.layoutH0a.addWidget(self.libEdit)
        self.layoutV.addLayout(self.layoutH0a)
        # url
        self.urlLabel = QLabel('URL')
        self.urlLabel.setFont(self.fBold)
        self.urlDesc = QLabel(
            'Web address of your Serato Playlist.\ne.g., https://serato.com/playlists/USERNAME/live'
        )
        self.urlDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.urlLabel)
        self.urlEdit = QLineEdit()
        self.layoutV.addWidget(self.urlDesc)
        self.layoutV.addWidget(self.urlEdit)
        self.urlLabel.setHidden(True)
        self.urlEdit.setHidden(True)
        self.urlDesc.setHidden(True)
        # separator line
        self.separator1.setFrameShape(QFrame.HLine)
        # self.separator.setFrameShadow(QFrame.Sunken)
        self.layoutV.addWidget(self.separator1)

        # interval
        self.intervalLabel = QLabel('Polling Interval')
        self.intervalLabel.setFont(self.fBold)
        self.intervalDesc = QLabel('Amount of time, in seconds, \
that must elapse before checking for new track info. (Default = 10.0)')
        self.intervalDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.intervalLabel)
        self.layoutV.addWidget(self.intervalDesc)
        self.intervalEdit = QLineEdit()
        self.intervalEdit.setMaximumSize(40, 35)
        self.layoutV.addWidget(self.intervalEdit)
        self.intervalLabel.setHidden(True)
        self.intervalDesc.setHidden(True)
        self.intervalEdit.setHidden(True)

        # notify
        self.notifLabel = QLabel('Notification Indicator')
        self.notifLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.notifLabel)
        self.notifCbox = QCheckBox()
        self.notifCbox.setMaximumWidth(25)
        self.layoutH5.addWidget(self.notifCbox)
        self.notifDesc = QLabel('Show OS system notification \
when new song is retrieved.')
        self.notifDesc.setStyleSheet('color: grey')
        self.layoutH5.addWidget(self.notifDesc)
        self.layoutV.addLayout(self.layoutH5)

        # separator line
        self.separator2.setFrameShape(QFrame.HLine)
        # self.separator.setFrameShadow(QFrame.Sunken)
        self.layoutV.addWidget(self.separator2)

        # file
        self.fileLabel = QLabel('File')
        self.fileLabel.setFont(self.fBold)
        self.fileDesc = QLabel(
            'The file to which current track info is written. (Must be plain text: .txt)'
        )
        self.fileDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.fileLabel)
        self.layoutV.addWidget(self.fileDesc)
        self.fileButton = QPushButton('Browse for file')
        self.layoutH1.addWidget(self.fileButton)
        self.fileButton.clicked.connect(self.on_filebutton_clicked)
        self.fileEdit = QLineEdit()
        self.layoutH1.addWidget(self.fileEdit)
        self.layoutV.addLayout(self.layoutH1)

        # delay
        self.delayLabel = QLabel('Write Delay')
        self.delayLabel.setFont(self.fBold)
        self.delayDesc = QLabel('Amount of time, in seconds, \
to delay writing the new track info once it\'s retrieved. (Default = 0)')
        self.delayDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.delayLabel)
        self.layoutV.addWidget(self.delayDesc)
        self.delayEdit = QLineEdit()
        self.delayEdit.setMaximumWidth(40)
        self.layoutV.addWidget(self.delayEdit)
        # multi-line
        self.multiLabel = QLabel('Multiple Line Indicator')
        self.multiLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.multiLabel)
        self.multiCbox = QCheckBox()
        self.multiCbox.setMaximumWidth(25)
        self.layoutH2.addWidget(self.multiCbox)
        self.multiDesc = QLabel(
            'Write Artist and Song data on separate lines.')
        self.multiDesc.setStyleSheet('color: grey')
        self.layoutH2.addWidget(self.multiDesc)
        self.layoutV.addLayout(self.layoutH2)
        # quotes
        self.quoteLabel = QLabel('Song Quote Indicator')
        self.quoteLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.quoteLabel)
        self.quoteCbox = QCheckBox()
        self.quoteCbox.setMaximumWidth(25)
        self.layoutH3.addWidget(self.quoteCbox)
        self.quoteDesc = QLabel('Surround the song title with quotes.')
        self.quoteDesc.setStyleSheet('color: grey')
        self.layoutH3.addWidget(self.quoteDesc)
        self.layoutV.addLayout(self.layoutH3)
        # prefixes
        self.prefixLabel = QLabel('Prefixes')
        self.prefixLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.prefixLabel)
        self.a_prefixDesc = QLabel(
            'Artist - String to be written before artist info.')
        self.a_prefixDesc.setStyleSheet('color: grey')
        self.s_prefixDesc = QLabel(
            'Song - String to be written before song info.')
        self.s_prefixDesc.setStyleSheet('color: grey')
        self.layoutH6a.addWidget(self.a_prefixDesc)
        self.layoutH6a.addWidget(self.s_prefixDesc)
        self.a_prefixEdit = QLineEdit()
        self.s_prefixEdit = QLineEdit()
        self.layoutH6b.addWidget(self.a_prefixEdit)
        self.layoutH6b.addWidget(self.s_prefixEdit)
        self.layoutV.addLayout(self.layoutH6a)
        self.layoutV.addLayout(self.layoutH6b)
        # suffixes
        self.suffixLabel = QLabel('Suffixes')
        self.suffixLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.suffixLabel)
        self.a_suffixDesc = QLabel(
            'Artist - String to be written after artist info.')
        self.a_suffixDesc.setStyleSheet('color: grey')
        self.s_suffixDesc = QLabel(
            'Song - String to be written after song info.')
        self.s_suffixDesc.setStyleSheet('color: grey')
        self.layoutH6c.addWidget(self.a_suffixDesc)
        self.layoutH6c.addWidget(self.s_suffixDesc)
        self.a_suffixEdit = QLineEdit()
        self.s_suffixEdit = QLineEdit()
        self.layoutH6d.addWidget(self.a_suffixEdit)
        self.layoutH6d.addWidget(self.s_suffixEdit)
        self.layoutV.addLayout(self.layoutH6c)
        self.layoutV.addLayout(self.layoutH6d)

        # separator line
        self.separator3.setFrameShape(QFrame.HLine)
        # self.separator.setFrameShadow(QFrame.Sunken)
        self.layoutV.addWidget(self.separator3)

        # HTTP Server Support
        self.httpenabledLabel = QLabel('HTTP Server Support')
        self.httpenabledLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.httpenabledLabel)
        self.httpenabledCbox = QCheckBox()
        self.httpenabledCbox.setMaximumWidth(25)
        self.layoutHttpEnableCheckbox.addWidget(self.httpenabledCbox)
        self.httpenabledDesc = QLabel('Enable HTTP Server [REQUIRES RESTART!]')
        self.httpenabledDesc.setStyleSheet('color: grey')
        self.layoutHttpEnableCheckbox.addWidget(self.httpenabledDesc)
        self.layoutV.addLayout(self.layoutHttpEnableCheckbox)

        try:
            hostname = socket.gethostname()
            hostip = socket.gethostbyname(hostname)
        except:  # pylint: disable = bare-except
            hostname = 'Unknown Hostname'
            hostip = 'Unknown IP'

        self.connectionLabel = QLabel('Networking Info')
        self.connectionLabel.setFont(self.fBold)
        self.connectionDesc = QLabel(
            f'Hostname: {hostname} / IP Address:{hostip}')
        self.connectionDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.connectionLabel)
        self.layoutV.addWidget(self.connectionDesc)

        self.httpportLabel = QLabel('Port')
        self.httpportLabel.setFont(self.fBold)
        self.httpportDesc = QLabel('TCP Port to run the server on')
        self.httpportDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.httpportLabel)
        self.layoutV.addWidget(self.httpportDesc)
        self.httpportEdit = QLineEdit()
        self.httpportEdit.setMaximumWidth(60)
        self.layoutV.addWidget(self.httpportEdit)

        self.htmltemplateLabel = QLabel('HTML Template')
        self.htmltemplateLabel.setFont(self.fBold)
        self.htmltemplateDesc = QLabel('Location to write data')
        self.htmltemplateDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.htmltemplateLabel)
        self.layoutV.addWidget(self.htmltemplateDesc)
        self.htmltemplateButton = QPushButton('Browse for file')
        self.layoutHttpHtmlTemplate.addWidget(self.htmltemplateButton)
        self.htmltemplateButton.clicked.connect(
            self.on_htmltemplatebutton_clicked)
        self.htmltemplateEdit = QLineEdit()
        self.layoutHttpHtmlTemplate.addWidget(self.htmltemplateEdit)
        self.layoutV.addLayout(self.layoutHttpHtmlTemplate)

        self.httpdirLabel = QLabel('Server Path')
        self.httpdirLabel.setFont(self.fBold)
        self.httpdirDesc = QLabel('Location to write data')
        self.httpdirDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.httpdirLabel)
        self.layoutV.addWidget(self.httpdirDesc)
        self.httpdirButton = QPushButton('Browse for folder')
        self.layoutHttpServerPath.addWidget(self.httpdirButton)
        self.httpdirButton.clicked.connect(self.on_httpdirbutton_clicked)
        self.httpdirEdit = QLineEdit()
        self.layoutHttpServerPath.addWidget(self.httpdirEdit)
        self.layoutV.addLayout(self.layoutHttpServerPath)

        # error area
        self.layoutV.addWidget(self.errLabel)
        # cancel btn
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.setMaximumSize(80, 35)
        self.layoutH4.addWidget(self.cancelButton)
        self.cancelButton.clicked.connect(self.on_cancelbutton_clicked)
        # save btn
        self.saveButton = QPushButton('Save')
        self.saveButton.setMaximumSize(80, 35)
        self.layoutH4.addWidget(self.saveButton)
        self.saveButton.clicked.connect(self.on_savebutton_clicked)
        self.layoutV.addLayout(self.layoutH4)

        self.window.setLayout(self.layoutV)

    def upd_win(self):
        ''' update the settings window '''
        c = ConfigFile(self.conf, self.conffile)
        if c.local:
            self.localRadio.setChecked(True)
            self.remoteRadio.setChecked(False)
        else:
            self.localRadio.setChecked(False)
            self.remoteRadio.setChecked(True)
        self.libEdit.setText(c.libpath)
        self.urlEdit.setText(c.url)
        self.fileEdit.setText(c.file)
        self.httpenabledCbox.setChecked(c.httpenabled)
        self.httpportEdit.setText(str(c.httpport))
        self.httpdirEdit.setText(c.httpdir)
        self.htmltemplateEdit.setText(c.htmltemplate)
        self.intervalEdit.setText(str(c.interval))
        self.delayEdit.setText(str(c.delay))
        self.multiCbox.setChecked(c.multi)
        self.quoteCbox.setChecked(c.quote)
        self.a_prefixEdit.setText(c.a_pref)
        self.a_suffixEdit.setText(c.a_suff)
        self.s_prefixEdit.setText(c.s_pref)
        self.s_suffixEdit.setText(c.s_suff)
        self.notifCbox.setChecked(c.notif)

    def disable_web(self):
        ''' if the web server gets in trouble, this gets called '''
        self.errLabel.setText(
            'HTTP Server settings are invalid. Bad port? Wrong directory?')
        self.httpenabledCbox.setChecked(False)
        self.upd_win()
        self.upd_conf()

    # pylint: disable=too-many-locals
    def upd_conf(self):
        ''' update the configuration '''
        local = str(self.localRadio.isChecked())
        libpath = self.libEdit.text()
        url = self.urlEdit.text()
        file = self.fileEdit.text()
        httpenabled = self.httpenabledCbox.isChecked()
        httpport = int(self.httpportEdit.text())
        httpdir = self.httpdirEdit.text()
        htmltemplate = self.htmltemplateEdit.text()
        interval = self.intervalEdit.text()
        delay = self.delayEdit.text()
        multi = self.multiCbox.isChecked()
        quote = self.quoteCbox.isChecked()
        a_pref = self.a_prefixEdit.text().replace(" ", "|_0")
        a_suff = self.a_suffixEdit.text().replace(" ", "|_0")
        s_pref = self.s_prefixEdit.text().replace(" ", "|_0")
        s_suff = self.s_suffixEdit.text().replace(" ", "|_0")
        notif = self.notifCbox.isChecked()

        conf = ConfigFile(self.conf, self.conffile)
        conf.put(local=local,
                 libpath=libpath,
                 url=url,
                 file=file,
                 httpport=httpport,
                 httpdir=httpdir,
                 httpenabled=httpenabled,
                 htmltemplate=htmltemplate,
                 interval=interval,
                 delay=delay,
                 multi=multi,
                 quote=quote,
                 a_pref=a_pref,
                 a_suff=a_suff,
                 s_pref=s_pref,
                 s_suff=s_suff,
                 notif=notif)

    def on_radiobutton_select(self, b):
        ''' radio button action '''
        if b.text() == 'Local':
            self.urlLabel.setHidden(True)
            self.urlEdit.setHidden(True)
            self.urlDesc.setHidden(True)
            self.intervalLabel.setHidden(True)
            self.intervalDesc.setHidden(True)
            self.intervalEdit.setHidden(True)
            self.libLabel.setHidden(False)
            self.libEdit.setHidden(False)
            self.libDesc.setHidden(False)
            self.libButton.setHidden(False)
            self.window.hide()
            self.errLabel.setText('')
            self.window.show()
        else:
            self.urlLabel.setHidden(False)
            self.urlEdit.setHidden(False)
            self.urlDesc.setHidden(False)
            self.intervalLabel.setHidden(False)
            self.intervalDesc.setHidden(False)
            self.intervalEdit.setHidden(False)
            self.libLabel.setHidden(True)
            self.libEdit.setHidden(True)
            self.libDesc.setHidden(True)
            self.libButton.setHidden(True)
            self.window.hide()
            self.errLabel.setText('')
            self.window.show()

    def on_filebutton_clicked(self):
        ''' file button clicked action '''
        filename = QFileDialog.getOpenFileName(self.window, 'Open file', '.',
                                               '*.txt')
        if filename:
            self.fileEdit.setText(filename[0])

    def on_libbutton_clicked(self):
        ''' lib button clicked action'''
        libdir = QFileDialog.getExistingDirectory(self.window,
                                                  'Select directory')
        if libdir:
            self.libEdit.setText(libdir)

    def on_httpdirbutton_clicked(self):
        ''' file button clicked action '''
        dirname = QFileDialog.getExistingDirectory(self.window,
                                                   'Select directory')
        if dirname:
            self.httpdirEdit.setText(dirname)

    def on_htmltemplatebutton_clicked(self):
        ''' file button clicked action '''
        filename = QFileDialog.getOpenFileName(self.window, 'Open file', '.',
                                               '*.htm *.html')
        if filename:
            self.htmltemplateEdit.setText(filename[0])

    def on_cancelbutton_clicked(self):
        ''' cancel button clicked action '''
        global TRAY

        if TRAY:
            TRAY.action_config.setEnabled(True)
        self.upd_win()
        self.close()
        self.errLabel.setText('')

    def on_savebutton_clicked(self):
        ''' save button clicked action '''
        global PAUSED, TRAY

        if self.remoteRadio.isChecked():
            if 'https://serato.com/playlists' not in self.urlEdit.text() and \
                    'https://www.serato.com/playlists' not in self.urlEdit.text() or \
                    len(self.urlEdit.text()) < 30:
                self.errLabel.setText('* URL is invalid')
                self.window.hide()
                self.window.show()
                return

        if self.localRadio.isChecked():
            if '_Serato_' not in self.libEdit.text():
                self.errLabel.setText(
                    '* Serato Library Path is required.  Should point to "_Serato_" folder'
                )
                self.window.hide()
                self.window.show()
                return

        if self.fileEdit.text() == "":
            self.errLabel.setText('* File is required')
            self.window.hide()
            self.window.show()
            return

        PAUSED = False
        self.upd_conf()
        self.close()
        self.errLabel.setText('')
        TRAY.action_pause.setText('Pause')
        TRAY.action_pause.setEnabled(True)

    def show(self):
        ''' show the system tram '''
        global TRAY
        if TRAY:
            TRAY.action_config.setEnabled(False)
        self.upd_win()
        self.scroll.show()
        self.scroll.setFocus()

    def close(self):
        ''' close the system tray '''
        global TRAY

        TRAY.action_config.setEnabled(True)
        self.scroll.hide()

    def exit(self):
        ''' exit the tray '''
        self.scroll.close()


class Tray:  # create tray icon menu
    ''' System Tray object '''
    def __init__(self):

        self.settingswindow = SettingsUI(CONFIG, CONFIG_FILE, ICONFILE)
        self.conf = ConfigFile(CONFIG, CONFIG_FILE)
        ''' create systemtray UI '''
        self.icon = QIcon(ICONFILE)
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setToolTip("Now Playing ▶")
        self.tray.setVisible(True)
        self.menu = QMenu()

        # create systemtray options and actions
        self.action_title = QAction(f'Now Playing v{__version__}')
        self.menu.addAction(self.action_title)
        self.action_title.setEnabled(False)

        self.action_config = QAction("Settings")
        self.action_config.triggered.connect(self.settingswindow.show)
        self.menu.addAction(self.action_config)
        self.menu.addSeparator()

        self.action_pause = QAction()
        self.action_pause.triggered.connect(self.pause)
        self.menu.addAction(self.action_pause)
        self.action_pause.setEnabled(False)

        self.action_exit = QAction("Exit")
        self.action_exit.triggered.connect(self.cleanquit)
        self.menu.addAction(self.action_exit)

        # add menu to the systemtray UI
        self.tray.setContextMenu(self.menu)

        if not self.conf.file:
            self.settingswindow.show()
        else:
            self.action_pause.setText('Pause')
            self.action_pause.setEnabled(True)

        self.error_dialog = QErrorMessage()

        # Start the polling thread
        self.trackthread = TrackPoll()
        self.trackthread.currenttrack[str].connect(self.tracknotify)
        self.trackthread.start()

        # Start the webserver
        self.webthread = WebServer()
        self.webthread.webenable[bool].connect(self.webenable)
        self.webthread.start()

    def tracknotify(self, track):
        ''' signal handler to update the tooltip '''
        if self.conf.notif:
            tip = track.replace("\n", " - ")\
                       .replace("\"", "")\
                       .replace(self.conf.a_pref, "")\
                       .replace(self.conf.a_suff, "")\
                       .replace(self.conf.s_pref, "")\
                       .replace(self.conf.s_suff, "")
            self.tray.showMessage('Now Playing ▶ ', tip, 0)

    def webenable(self, status):
        ''' If the web server gets in trouble, we need to tell the user '''
        if not status:
            self.settingswindow.disable_web()
            self.settingswindow.show()
            self.pause()

    def unpause(self):
        ''' unpause polling '''

        global PAUSED
        PAUSED = False
        self.action_pause.setText('Pause')
        self.action_pause.triggered.connect(self.pause)

    def pause(self):
        ''' pause polling '''

        global PAUSED
        PAUSED = True
        self.action_pause.setText('Resume')
        self.action_pause.triggered.connect(self.unpause)

    def cleanquit(self):
        ''' quit app and cleanup '''
        self.tray.setVisible(False)
        file = ConfigFile(CONFIG, CONFIG_FILE).file
        if file:
            writetxttrack(file)
        # calling exit should call __del__ on all of our QThreads
        QAPP.exit(0)
        sys.exit(0)


class WebHandler(BaseHTTPRequestHandler):
    ''' Custom handler for built-in webserver '''
    def do_GET(self):  # pylint: disable=invalid-name
        '''
            HTTP GET
                - if there is an index.htm file to read, give it out
                  then delete it
                - if not, have our reader check back in 5 seconds

            Note that there is NO path information here.  So any
            chdir() that happens MUST be this directory.

            Also, doing it this way means the webserver can only ever
            share two types of content.  Note that browsers might ask
            for favicon.ico.  That should probably be handled here but
            is not currently.
        '''
        self.send_response(200)
        self.end_headers()

        if os.path.isfile("index.htm"):
            with open("index.htm", "rb") as indexfh:
                self.wfile.write(indexfh.read())
            os.unlink("index.htm")
            return

        self.wfile.write(b'<!doctype html><html lang="en">')
        self.wfile.write(
            b'<head><meta http-equiv="refresh" content="5" ></head>')
        self.wfile.write(b'<body></body></html>\n')


class ThreadingWebServer(ThreadingMixIn, HTTPServer):
    ''' threaded webserver object '''
    pass  # pylint: disable=unnecessary-pass


class WebServer(QThread):
    ''' Now Playing built-in web server using custom handler '''

    webenable = pyqtSignal(bool)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.server = None
        self.prevport = 0
        self.prevdir = None
        self.endthread = False

    def run(self):  # pylint: disable=too-many-branches
        '''
            Configure a webserver.

            The sleeps are here to make sure we don't
            tie up a CPU constantly checking on
            status.  If we cannot open the port or
            some other situation, we bring everything
            to a halt by triggering pause.

        '''
        global CONFIG, CONFIG_FILE, PAUSED

        conf = ConfigFile(CONFIG, CONFIG_FILE)
        while not conf.httpenabled and not self.endthread:
            time.sleep(5)
            conf = ConfigFile(CONFIG, CONFIG_FILE)

        while not self.endthread:
            while PAUSED:
                time.sleep(1)

            resetserver = False
            time.sleep(1)
            conf = ConfigFile(CONFIG, CONFIG_FILE)

            if conf.httpdir != self.prevdir:
                os.chdir(conf.httpdir)
                self.prevdir = conf.httpdir
                resetserver = True

            if conf.httpport != self.prevport:
                self.prevport = conf.httpport

            if not conf.httpenabled:
                self.stop()
                continue

            if resetserver:
                self.stop()
                time.sleep(5)

            if not self.server:
                try:
                    self.server = ThreadingWebServer(
                        ('0.0.0.0', conf.httpport), WebHandler)
                except Exception as error:  # pylint: disable=broad-except
                    print(f'webserver error: {error}')
                    self.webenable.emit(False)

            try:
                if self.server:
                    self.server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                if self.server:
                    self.server.shutdown()

    def stop(self):
        ''' method to stop the thread '''
        if self.server:
            self.server.shutdown()

    def __del__(self):
        self.endthread = True
        self.stop()
        self.wait()


class TrackPoll(QThread):
    '''
        QThread that runs the main polling work.
        Uses a signal to tell the Tray when the
        song has changed for notification
    '''

    currenttrack = pyqtSignal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.endthread = False
        self.previoustrack = None

    def run(self):
        ''' track polling process '''

        global CONFIG, CONFIG_FILE

        # sleep until we have something to write
        conf = ConfigFile(CONFIG, CONFIG_FILE)
        while not conf.file and not self.endthread:
            time.sleep(5)
            conf = ConfigFile(CONFIG, CONFIG_FILE)

        while not self.endthread:
            conf = ConfigFile(CONFIG, CONFIG_FILE)

            # get poll interval and then poll
            if conf.local:
                interval = 1
            else:
                interval = conf.interval

            time.sleep(interval)
            new = gettrack(ConfigFile(CONFIG, CONFIG_FILE))
            if not new or new == self.previoustrack:
                continue
            self.previoustrack = new
            time.sleep(conf.delay)
            writetxttrack(conf.file, new)
            if new:
                self.currenttrack.emit(new)
            if conf.httpenabled:
                update_javascript(serverdir=conf.httpdir)

    def __del__(self):
        self.endthread = True
        self.wait()


# FUNCTIONS ####


def gettrack(configuration):  # pylint: disable=too-many-branches
    ''' get last played track '''
    global PAUSED, CURRENTARTIST, CURRENTSONG

    conf = configuration
    tdat = None

    # check paused state
    while True:
        if not PAUSED:
            break
    print("checking...")
    if conf.local:  # locally derived
        # paths for session history
        sera_dir = conf.libpath
        hist_dir = os.path.abspath(os.path.join(sera_dir, "History"))
        sess_dir = os.path.abspath(os.path.join(hist_dir, "Sessions"))
        if os.path.isdir(sess_dir):
            serato = nowplaying.serato.SeratoSessionHandler(sess_dir)
            serato.process_sessions()

    else:  # remotely derived

        serato = nowplaying.serato.SeratoLivePlaylistHandler(conf.url)

    (artist, song) = serato.getplayingtrack()

    if not artist and not song:
        return None

    if artist:
        artist = artist.strip()
    else:
        artist = ''

    if song:
        song = song.strip()
    else:
        song = ''

    if artist == '' and song == '':
        return None

    if artist == '.':
        artist = ''
    else:
        artist = configuration.a_pref + artist + configuration.a_suff

    if song == '.':
        song = ''
    elif conf.quote:  # handle quotes
        song = configuration.s_pref + "\"" + song + "\"" + configuration.s_suff
    else:
        song = configuration.s_pref + song + configuration.s_suff

    if song == CURRENTSONG and artist == CURRENTARTIST:
        return None


    if not conf.local:
        CURRENTARTIST = artist
        CURRENTSONG = song

    # handle multiline
    if conf.multi:
        tdat = artist + "\n" + song
    elif song == '' or artist == '':
        tdat = artist + song
    else:
        tdat = artist + " - " + song

    return tdat


def writetxttrack(filename, track=""):
    ''' write new track info '''
    with open(filename, "w", encoding='utf-8') as textfh:
        print("writing...")
        textfh.write(track)


def update_javascript(serverdir='/tmp'):
    ''' update the image with the new info '''

    # This should really use a better templating engine,
    # but let us keep it simple for now

    conf = ConfigFile(CONFIG, CONFIG_FILE)

    indexhtm = os.path.join(serverdir, "index.htm")

    with open(conf.htmltemplate, "r") as templatefh:
        rawtemplate = templatefh.read()

    template = Template(rawtemplate)

    titlecardhtml = template.substitute(
        dict(artiststring=html.escape(CURRENTARTIST),
             songstring=html.escape(CURRENTSONG)))
    with open(indexhtm, "w") as indexfh:
        indexfh.write(titlecardhtml)


# END FUNCTIONS ####

if __name__ == "__main__":
    TRAY = Tray()
    sys.exit(QAPP.exec_())
