#!/usr/bin/env python3
'''
    Titles for streaming for Serato
'''

# pylint: disable=no-name-in-module, global-statement
# pylint: disable=too-many-instance-attributes, too-few-public-methods
# pylint: disable=too-many-lines

import configparser
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from socketserver import ThreadingMixIn
import sys
import time
import urllib.parse

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
import nowplaying.utils

__author__ = "Ely Miranda"
__version__ = "1.5.0"
__license__ = "MIT"

# define global variables
INITIALIZED = PAUSED = False
CURRENTMETA = {'fetchedartist': None, 'fetchedtitle': None}
MIXMODE = 'active'

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
                                               BUNDLE_DIR, "templates",
                                               "basic.htm"))

            self.txttemplate = CONFIG.get('Settings',
                                          'txttemplate',
                                          fallback=os.path.join(
                                              BUNDLE_DIR, "templates",
                                              "basic.txt"))

            try:
                self.interval = CONFIG.getfloat('Settings', 'interval')
            except ValueError:
                self.interval = float(10)

            try:
                self.delay = CONFIG.getfloat('Settings', 'delay')
            except ValueError:
                self.delay = float(0)

            try:
                self.notif = CONFIG.getboolean('Settings', 'notif')
            except ValueError:
                self.notif = False

        except configparser.NoOptionError:
            pass

    # pylint: disable=too-many-locals, too-many-arguments
    def put(self, local, libpath, url, file, txttemplate, httpport, httpdir,
            httpenabled, htmltemplate, interval, delay, notif):
        ''' Save the configuration file '''
        self.cparser.set('Settings', 'local', local)
        self.cparser.set('Settings', 'libpath', libpath)
        self.cparser.set('Settings', 'url', url)
        self.cparser.set('Settings', 'file', file)
        self.cparser.set('Settings', 'txttemplate', txttemplate)
        self.cparser.set('Settings', 'httpenabled', str(httpenabled))
        self.cparser.set('Settings', 'httpport', str(httpport))
        self.cparser.set('Settings', 'httpdir', httpdir)
        self.cparser.set('Settings', 'htmltemplate', htmltemplate)
        self.cparser.set('Settings', 'interval', interval)
        self.cparser.set('Settings', 'delay', delay)
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
        self.layoutTxtTemplate = QHBoxLayout()
        self.layoutH4 = QHBoxLayout()
        self.layoutH5 = QHBoxLayout()
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
        self.scroll.setMinimumWidth(700)
        self.scroll.resize(700, 825)

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

        self.txttemplateLabel = QLabel('TXT Template')
        self.txttemplateLabel.setFont(self.fBold)
        self.txttemplateDesc = QLabel('Template file for text output')
        self.txttemplateDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.txttemplateLabel)
        self.layoutV.addWidget(self.txttemplateDesc)
        self.txttemplateButton = QPushButton('Browse for file')
        self.layoutTxtTemplate.addWidget(self.txttemplateButton)
        self.txttemplateButton.clicked.connect(
            self.on_txttemplatebutton_clicked)
        self.txttemplateEdit = QLineEdit()
        self.layoutTxtTemplate.addWidget(self.txttemplateEdit)
        self.layoutV.addLayout(self.layoutTxtTemplate)

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
        self.httpenabledDesc = QLabel('Enable HTTP Server')
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
        self.htmltemplateDesc = QLabel('Template file to format')
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
        self.txttemplateEdit.setText(c.txttemplate)
        self.httpenabledCbox.setChecked(c.httpenabled)
        self.httpportEdit.setText(str(c.httpport))
        self.httpdirEdit.setText(c.httpdir)
        self.htmltemplateEdit.setText(c.htmltemplate)
        self.intervalEdit.setText(str(c.interval))
        self.delayEdit.setText(str(c.delay))
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
        txttemplate = self.txttemplateEdit.text()
        httpenabled = self.httpenabledCbox.isChecked()
        httpport = int(self.httpportEdit.text())
        httpdir = self.httpdirEdit.text()
        htmltemplate = self.htmltemplateEdit.text()
        interval = self.intervalEdit.text()
        delay = self.delayEdit.text()
        notif = self.notifCbox.isChecked()

        conf = ConfigFile(self.conf, self.conffile)
        conf.put(local=local,
                 libpath=libpath,
                 url=url,
                 file=file,
                 txttemplate=txttemplate,
                 httpport=httpport,
                 httpdir=httpdir,
                 httpenabled=httpenabled,
                 htmltemplate=htmltemplate,
                 interval=interval,
                 delay=delay,
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
        startfile = self.fileEdit.text()
        if startfile:
            startdir = os.path.dirname(startfile)
        else:
            startdir = '.'
        filename = QFileDialog.getOpenFileName(self.window, 'Open file',
                                               startdir, '*.txt')
        if filename:
            self.fileEdit.setText(filename[0])

    def on_txttemplatebutton_clicked(self):
        ''' file button clicked action '''
        startfile = self.txttemplateEdit.text()
        if startfile:
            startdir = os.path.dirname(startfile)
        else:
            startdir = '.'
        filename = QFileDialog.getOpenFileName(self.window, 'Open file',
                                               startdir, '*.txt')
        if filename:
            self.txttemplateEdit.setText(filename[0])

    def on_libbutton_clicked(self):
        ''' lib button clicked action'''
        startdir = self.httpdirEdit.text()
        if not startdir:
            startdir = '.'
        libdir = QFileDialog.getExistingDirectory(self.window,
                                                  'Select directory', startdir)
        if libdir:
            self.libEdit.setText(libdir)

    def on_httpdirbutton_clicked(self):
        ''' file button clicked action '''
        startdir = self.httpdirEdit.text()
        if not startdir:
            startdir = '.'
        dirname = QFileDialog.getExistingDirectory(self.window,
                                                   'Select directory',
                                                   startdir)
        if dirname:
            self.httpdirEdit.setText(dirname)

    def on_htmltemplatebutton_clicked(self):
        ''' file button clicked action '''
        startfile = self.htmltemplateEdit.text()
        if startfile:
            startdir = os.path.dirname(startfile)
        else:
            startdir = '.'
        filename = QFileDialog.getOpenFileName(self.window, 'Open file',
                                               startdir, '*.htm *.html')
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
        global PAUSED, TRAY, MIXMODE

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
        TRAY.action_mixmode.setText('Active')
        TRAY.action_mixmode.setEnabled(True)
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

        self.action_mixmode = QAction()
        self.action_mixmode.triggered.connect(self.passivemixmode)
        self.menu.addAction(self.action_mixmode)
        self.action_mixmode.setEnabled(False)

        self.menu.addSeparator()

        self.action_pause = QAction()
        self.action_pause.triggered.connect(self.pause)
        self.menu.addAction(self.action_pause)
        self.action_pause.setEnabled(False)

        self.menu.addSeparator()


        self.action_exit = QAction("Exit")
        self.action_exit.triggered.connect(self.cleanquit)
        self.menu.addAction(self.action_exit)

        # add menu to the systemtray UI
        self.tray.setContextMenu(self.menu)

        if not self.conf.file:
            self.settingswindow.show()
        else:
            self.action_mixmode.setText('Active')
            self.action_mixmode.setEnabled(True)
            self.action_pause.setText('Pause')
            self.action_pause.setEnabled(True)


        self.error_dialog = QErrorMessage()

        # Start the polling thread
        self.trackthread = TrackPoll()
        self.trackthread.currenttrack[dict].connect(self.tracknotify)
        self.trackthread.start()

        # Start the webserver
        self.webthread = WebServer()
        self.webthread.webenable[bool].connect(self.webenable)
        self.webthread.start()

    def tracknotify(self, metadata):
        ''' signal handler to update the tooltip '''
        if self.conf.notif:
            if 'artist' in metadata:
                artist = metadata['artist']
            else:
                artist = ''

            if 'title' in metadata:
                title = metadata['title']
            else:
                title = ''

            tip = f'{artist} - {title}'
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

    def activemixmode(self):
        ''' enable active mixing '''

        global MIXMODE
        MIXMODE = 'active'
        self.action_mixmode.setText('Active')
        self.action_mixmode.triggered.connect(self.passivemixmode)

    def passivemixmode(self):
        ''' enable passive mixing '''

        global MIXMODE
        MIXMODE = 'passive'
        self.action_mixmode.setText('Passive')
        self.action_mixmode.triggered.connect(self.activemixmode)

    def cleanquit(self):
        ''' quit app and cleanup '''
        self.tray.setVisible(False)
        file = ConfigFile(CONFIG, CONFIG_FILE).file
        if file:
            nowplaying.utils.writetxttrack(filename=file)
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

            Note that there is very specific path information
            handling here.  So any chdir() that happens MUST
            be this directory.

            Also, doing it this way means the webserver can only ever
            share specific content.
        '''

        global ICONFILE

        # see what was asked for
        parsedrequest = urllib.parse.urlparse(self.path)

        if parsedrequest.path in ['/favicon.ico']:
            self.send_response(200)
            self.send_header('Content-type', 'image/x-icon')
            self.end_headers()
            with open(ICONFILE, 'rb') as iconfh:
                self.wfile.write(iconfh.read())
            return

        if parsedrequest.path in ['/', 'index.html', 'index.htm']:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if os.path.isfile('index.htm'):
                with open('index.htm', 'rb') as indexfh:
                    self.wfile.write(indexfh.read())
                os.unlink('index.htm')
                return

            self.wfile.write(b'<!doctype html><html lang="en">')
            self.wfile.write(
                b'<head><meta http-equiv="refresh" content="5" ></head>')
            self.wfile.write(b'<body></body></html>\n')
            return

        if parsedrequest.path in ['/cover.jpg']:
            if os.path.isfile('cover.jpg'):
                self.send_response(200, 'OK')
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                with open('cover.jpg', 'rb') as indexfh:
                    self.wfile.write(indexfh.read())
                os.unlink('cover.jpg')
                return

        if parsedrequest.path in ['/cover.png']:
            if os.path.isfile('cover.png'):
                self.send_response(200, 'OK')
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                with open('cover.png', 'rb') as indexfh:
                    self.wfile.write(indexfh.read())
                os.unlink('cover.png')
                return

        self.send_error(404)
        return


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

    currenttrack = pyqtSignal(dict)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.endthread = False

    def run(self):
        ''' track polling process '''

        global CONFIG, CONFIG_FILE

        previoustxttemplate = None
        previoushtmltemplate = None

        # sleep until we have something to write
        conf = ConfigFile(CONFIG, CONFIG_FILE)
        while not conf.file and not self.endthread:
            time.sleep(5)
            conf = ConfigFile(CONFIG, CONFIG_FILE)

        while not self.endthread:
            conf = ConfigFile(CONFIG, CONFIG_FILE)

            if not previoustxttemplate or previoustxttemplate != conf.txttemplate:
                txttemplatehandler = nowplaying.utils.TemplateHandler(
                    filename=conf.txttemplate)
                previoustxttemplate = conf.txttemplate

            # get poll interval and then poll
            if conf.local:
                interval = 1
            else:
                interval = conf.interval

            time.sleep(interval)
            newmeta = gettrack(ConfigFile(CONFIG, CONFIG_FILE))
            if not newmeta:
                continue
            time.sleep(conf.delay)
            nowplaying.utils.writetxttrack(filename=conf.file,
                                           templatehandler=txttemplatehandler,
                                           metadata=newmeta)
            self.currenttrack.emit(newmeta)
            if conf.httpenabled:

                if not previoushtmltemplate or previoushtmltemplate != conf.htmltemplate:
                    htmltemplatehandler = nowplaying.utils.TemplateHandler(
                        filename=conf.htmltemplate)
                    previoushtmltemplate = conf.htmltemplate

                nowplaying.utils.update_javascript(
                    serverdir=conf.httpdir,
                    templatehandler=htmltemplatehandler,
                    metadata=newmeta)

    def __del__(self):
        self.endthread = True
        self.wait()


# FUNCTIONS ####


def gettrack(configuration):  # pylint: disable=too-many-branches
    ''' get currently playing track, returns None if not new or not found '''
    global CURRENTMETA, PAUSED, MIXMODE

    conf = configuration

    # check paused state
    while True:
        if not PAUSED:
            break
    #print("checking...")
    if conf.local:  # locally derived
        # paths for session history
        sera_dir = conf.libpath
        hist_dir = os.path.abspath(os.path.join(sera_dir, "History"))
        sess_dir = os.path.abspath(os.path.join(hist_dir, "Sessions"))
        if os.path.isdir(sess_dir):
            serato = nowplaying.serato.SeratoHandler(seratodir=sess_dir, mixmode=MIXMODE)
            serato.process_sessions()

    else:  # remotely derived

        serato = nowplaying.serato.SeratoHandler(seratourl=conf.url)

    if not serato:
        return None

    (artist, song) = serato.getplayingtrack()

    if not artist and not song:
        return None

    if artist == CURRENTMETA['fetchedartist'] and \
       song == CURRENTMETA['fetchedtitle']:
        return None

    nextmeta = serato.getplayingmetadata()
    nextmeta['fetchedtitle'] = song
    nextmeta['fetchedartist'] = artist

    if 'filename' in nextmeta:
        nextmeta = nowplaying.utils.getmoremetadata(nextmeta)

    CURRENTMETA = nextmeta

    return CURRENTMETA


# END FUNCTIONS ####

if __name__ == "__main__":
    TRAY = Tray()
    sys.exit(QAPP.exec_())
