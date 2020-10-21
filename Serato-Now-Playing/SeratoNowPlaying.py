#!/usr/bin/env python3


__author__ = "Ely Miranda"
__version__ = "1.4.0"
__license__ = "MIT"

'''
CHANGELOG:
* Fix for issue where Settings UI window did not fit on smaller resolution screens.
    The window is now re-sizeable and scrolling is enabled.
* Augmented the suffix and prefix functionality. The Artist and Song data chunks now
    can have independent suffixes and prefixes.
* Added version number to Settings window title bar.
'''

import requests
import configparser
from threading import Thread
from polling2 import poll
from lxml import html
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QLabel, QRadioButton, QScrollArea, \
    QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLineEdit, QFileDialog, QWidget, QFrame
from PyQt5.QtGui import QIcon, QFont
from time import sleep, time
import os
import sys

# define global variables
ini = paused = 0
track = ''

# set paths for bundled files
if getattr(sys, 'frozen', False) and sys.platform == "darwin":
    bundle_dir = os.path.dirname(sys.executable)  # sys._MEIPASS
    config_file = os.path.abspath(os.path.join(bundle_dir, "bin/config.ini"))
    ico = os.path.abspath(os.path.join(bundle_dir, "bin/icon.ico"))
else:
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin/config.ini"))
    ico = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin/icon.ico"))

# print(config_file)
# create needed object instances
config = configparser.ConfigParser()
app = QApplication([])
app.setQuitOnLastWindowClosed(False)


class ConfigFile:  # read and write to config.ini
    def __init__(self, cparser, cfile):
        self.cparser = cparser
        self.cfile = cfile

        try:
            self.cparser.read(self.cfile)
            self.cparser.sections()

            self.local = is_bool(config.get('Settings', 'local'))
            self.libpath = config.get('Settings', 'libpath')
            self.url = config.get('Settings', 'url')
            self.file = config.get('Settings', 'file')
            self.interval = config.get('Settings', 'interval')
            self.delay = config.get('Settings', 'delay')
            self.multi = is_bool(config.get('Settings', 'multi'))
            self.quote = is_bool(config.get('Settings', 'quote'))
            self.a_pref = config.get('Settings', 'a_pref').replace("|_0", " ")
            self.a_suff = config.get('Settings', 'a_suff').replace("|_0", " ")
            self.s_pref = config.get('Settings', 's_pref').replace("|_0", " ")
            self.s_suff = config.get('Settings', 's_suff').replace("|_0", " ")
            self.notif = is_bool(config.get('Settings', 'notif'))

            if is_number(self.interval) is False:
                self.interval = 10
            if is_number(self.delay) is False:
                self.delay = 0

            self.interval = float(self.interval)
            self.delay = float(self.delay)
        except configparser.NoOptionError:
            pass

    def put(self, local, libpath, url, file, interval, delay, multi, quote, a_pref, a_suff, s_pref, s_suff, notif):
        self.cparser.set('Settings', 'local', local)
        self.cparser.set('Settings', 'libpath', libpath)
        self.cparser.set('Settings', 'url', url)
        self.cparser.set('Settings', 'file', file)
        self.cparser.set('Settings', 'interval', interval)
        self.cparser.set('Settings', 'delay', delay)
        self.cparser.set('Settings', 'multi', str(multi))
        self.cparser.set('Settings', 'quote', str(quote))
        self.cparser.set('Settings', 'a_pref', a_pref)
        self.cparser.set('Settings', 'a_suff', a_suff)
        self.cparser.set('Settings', 's_pref', s_pref)
        self.cparser.set('Settings', 's_suff', s_suff)
        self.cparser.set('Settings', 'notif', str(notif))

        cf = open(self.cfile, 'w')
        self.cparser.write(cf)
        cf.close()


# settings UI
class SettingsUI:  # create settings form window
    def __init__(self, conf, conffile, icn):
        self.conf = conf
        self.conffile = conffile
        self.icon = icn
        self.scroll = QScrollArea()
        self.window = QWidget()
        self.separator = QFrame()
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
        self.fBold = QFont()
        self.fBold.setBold(True)
        self.scroll.setWindowTitle('Now Playing v1.4.0 - Settings')

        self.scroll.setWidgetResizable(True)
        self.scroll.setWindowFlag(Qt.CustomizeWindowHint, True)
        self.scroll.setWindowFlag(Qt.WindowCloseButtonHint, False)
        # self.scroll.setWindowFlag(Qt.WindowMinMaxButtonsHint, False)
        self.scroll.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.scroll.setWidget(self.window)
        self.scroll.setMinimumWidth(625)
        self.scroll.resize(625, 825)

        # error section
        self.errLabel = QLabel()
        self.errLabel.setStyleSheet('color: red')
        # remote
        self.localLabel = QLabel('Track Retrieval Mode')
        self.localLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.localLabel)
        self.remoteDesc = QLabel('Local mode (default) uses Serato\'s local history log for track data.\
\nRemote mode retrieves remote track data from Serato Live Playlists.')
        self.remoteDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.remoteDesc)
        # radios
        self.localRadio = QRadioButton('Local')
        self.localRadio.setChecked(True)
        self.localRadio.toggled.connect(lambda: self.on_radiobutton_select(self.localRadio))
        self.localRadio.setMaximumWidth(60)

        self.remoteRadio = QRadioButton('Remote')
        self.remoteRadio.toggled.connect(lambda: self.on_radiobutton_select(self.remoteRadio))
        self.layoutH0.addWidget(self.localRadio)
        self.layoutH0.addWidget(self.remoteRadio)
        self.layoutV.addLayout(self.layoutH0)

        # library path
        self.libLabel = QLabel('Serato Library Path')
        self.libLabel.setFont(self.fBold)
        self.libDesc = QLabel('Location of Serato library folder.\ni.e., \\THE_PATH_TO\\_Serato_')
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
        self.urlDesc = QLabel('Web address of your Serato Playlist.\ne.g., https://serato.com/playlists/USERNAME/live')
        self.urlDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.urlLabel)
        self.urlEdit = QLineEdit()
        self.layoutV.addWidget(self.urlDesc)
        self.layoutV.addWidget(self.urlEdit)
        self.urlLabel.setHidden(True)
        self.urlEdit.setHidden(True)
        self.urlDesc.setHidden(True)
        # separator line
        self.separator.setFrameShape(QFrame.HLine)
        # self.separator.setFrameShadow(QFrame.Sunken)
        self.layoutV.addWidget(self.separator)
        # file
        self.fileLabel = QLabel('File')
        self.fileLabel.setFont(self.fBold)
        self.fileDesc = QLabel('The file to which current track info is written. (Must be plain text: .txt)')
        self.fileDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.fileLabel)
        self.layoutV.addWidget(self.fileDesc)
        self.fileButton = QPushButton('Browse for file')
        self.layoutH1.addWidget(self.fileButton)
        self.fileButton.clicked.connect(self.on_filebutton_clicked)
        self.fileEdit = QLineEdit()
        self.layoutH1.addWidget(self.fileEdit)
        self.layoutV.addLayout(self.layoutH1)
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
        self.multiDesc = QLabel('Write Artist and Song \
data on separate lines.')
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
        self.quoteDesc = QLabel('Surround the song title \
with quotes.')
        self.quoteDesc.setStyleSheet('color: grey')
        self.layoutH3.addWidget(self.quoteDesc)
        self.layoutV.addLayout(self.layoutH3)
        # prefixes
        self.prefixLabel = QLabel('Prefixes')
        self.prefixLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.prefixLabel)
        self.a_prefixDesc = QLabel('Artist - String to be written before artist info.')
        self.a_prefixDesc.setStyleSheet('color: grey')
        self.s_prefixDesc = QLabel('Song - String to be written before song info.')
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
        self.a_suffixDesc = QLabel('Artist - String to be written after artist info.')
        self.a_suffixDesc.setStyleSheet('color: grey')
        self.s_suffixDesc = QLabel('Song - String to be written after song info.')
        self.s_suffixDesc.setStyleSheet('color: grey')
        self.layoutH6c.addWidget(self.a_suffixDesc)
        self.layoutH6c.addWidget(self.s_suffixDesc)
        self.a_suffixEdit = QLineEdit()
        self.s_suffixEdit = QLineEdit()
        self.layoutH6d.addWidget(self.a_suffixEdit)
        self.layoutH6d.addWidget(self.s_suffixEdit)
        self.layoutV.addLayout(self.layoutH6c)
        self.layoutV.addLayout(self.layoutH6d)
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
        self.intervalEdit.setText(str(c.interval))
        self.delayEdit.setText(str(c.delay))
        self.multiCbox.setChecked(c.multi)
        self.quoteCbox.setChecked(c.quote)
        self.a_prefixEdit.setText(c.a_pref)
        self.a_suffixEdit.setText(c.a_suff)
        self.s_prefixEdit.setText(c.s_pref)
        self.s_suffixEdit.setText(c.s_suff)
        self.notifCbox.setChecked(c.notif)

    def upd_conf(self):

        local = str(self.localRadio.isChecked())
        libpath = self.libEdit.text()
        url = self.urlEdit.text()
        file = self.fileEdit.text()
        interval = self.intervalEdit.text()
        delay = self.delayEdit.text()
        multi = str(self.multiCbox.isChecked())
        quote = str(self.quoteCbox.isChecked())
        a_pref = self.a_prefixEdit.text().replace(" ", "|_0")
        a_suff = self.a_suffixEdit.text().replace(" ", "|_0")
        s_pref = self.s_prefixEdit.text().replace(" ", "|_0")
        s_suff = self.s_suffixEdit.text().replace(" ", "|_0")
        notif = str(self.notifCbox.isChecked())

        c = ConfigFile(self.conf, self.conffile)
        c.put(local, libpath, url, file, interval, delay, multi, quote, a_pref, a_suff, s_pref, s_suff, notif)

    # radio button action
    def on_radiobutton_select(self, b):
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

    # file button action
    def on_filebutton_clicked(self):
        filename = QFileDialog.getOpenFileName(self.window, 'Open file', '.', '*.txt')
        if filename:
            self.fileEdit.setText(filename[0])

    # file button action
    def on_libbutton_clicked(self):
        libdir = QFileDialog.getExistingDirectory(self.window, 'Select directory')
        if libdir:
            self.libEdit.setText(libdir)

    # cancel button action
    def on_cancelbutton_clicked(self):
        tray.actConfig.setEnabled(True)
        self.upd_win()
        self.close()
        self.errLabel.setText('')

    # save button action
    def on_savebutton_clicked(self):
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
                self.errLabel.setText('* Serato Library Path is required.  Should point to "_Serato_" folder')
                self.window.hide()
                self.window.show()
                return

        if self.fileEdit.text() == "":
            self.errLabel.setText('* File is required')
            self.window.hide()
            self.window.show()
            return

        self.upd_conf()
        self.close()
        self.errLabel.setText('')

        global ini
        if ini == 0:
            ini = 1
            tray.actPause.setText('Pause')
            tray.actPause.setEnabled(True)
            main_thread.start()

    def show(self):
        tray.actConfig.setEnabled(False)
        self.upd_win()
        self.scroll.show()
        self.scroll.setFocus()

    def close(self):
        tray.actConfig.setEnabled(True)
        self.scroll.hide()

    def exit(self):
        self.scroll.close()


class Tray:  # create tray icon menu
    def __init__(self, ):
        # create systemtray UI
        self.icon = QIcon(ico)
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setToolTip("Now Playing ▶")
        self.tray.setVisible(True)
        self.menu = QMenu()

        # create systemtray options and actions
        self.actTitle = QAction("Now Playing v1.4")
        self.menu.addAction(self.actTitle)
        self.actTitle.setEnabled(False)

        self.actConfig = QAction("Settings")
        self.actConfig.triggered.connect(win.show)
        self.menu.addAction(self.actConfig)
        self.menu.addSeparator()

        self.actPause = QAction()
        self.actPause.triggered.connect(self.pause)
        self.menu.addAction(self.actPause)
        self.actPause.setEnabled(False)

        self.actExit = QAction("Exit")
        self.actExit.triggered.connect(self.cleanquit)
        self.menu.addAction(self.actExit)

        # add menu to the systemtray UI
        self.tray.setContextMenu(self.menu)

    def unpause(self):  # unpause polling
        global paused
        paused = 0
        self.actPause.setText('Pause')
        self.actPause.triggered.connect(self.pause)

    def pause(self):  # pause polling
        global paused
        paused = 1
        self.actPause.setText('Resume')
        self.actPause.triggered.connect(self.unpause)

    def cleanquit(self):  # quit app and cleanup
        self.tray.setVisible(False)
        file = ConfigFile(config, config_file).file
        if file:
            writetrack(file)
        sys.exit()


# create UI window object instance
win = SettingsUI(config, config_file, ico)

# create tray icon instance
tray = Tray()


# FUNCTIONS ####
def is_number(s):  # test for number type
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_bool(s):  # test for bool type
    if s == "False":
        return 0
    else:
        return 1


def init():  # initiate main processes
    conf = ConfigFile(config, config_file)
    if conf.file == '':
        win.show()
    else:
        global ini
        ini = 1
        tray.actPause.setText('Pause')
        tray.actPause.setEnabled(True)
        main_thread.start()


def main():  # track polling process
    global track
    conf = ConfigFile(config, config_file)

    # get poll interval and then poll
    if conf.local:
        interval = 1
    else:
        interval = conf.interval
    new = poll(lambda: gettrack(ConfigFile(config, config_file), track), step=interval, poll_forever=True)

    # display new track info in system notification
    track = new
    if conf.notif == 1:
        tip = new.replace("\n", " - ").replace("\"", "").replace(conf.a_pref, "").replace(conf.a_suff, "") \
            .replace(conf.s_pref, "").replace(conf.s_suff, "")
        tray.tray.showMessage('Now Playing ▶ ', tip, 0)

    # write new track info to file
    tinfo = new  # conf.pref + new + conf.suff
    if 'No Song Data' in tinfo:
        tinfo = ''
    sleep(conf.delay)
    writetrack(conf.file, tinfo)

    # recurse
    main()


main_thread = Thread(target=main, daemon=True)


def gettrack(c, t):  # get last played track
    global paused
    conf = c
    tk = t
    # check paused state
    while True:
        if not paused:
            break
    print("checking...")
    if conf.local:  # locally derived
        # paths for session history
        sera_dir = conf.libpath
        hist_dir = os.path.abspath(os.path.join(sera_dir, "History"))
        sess_dir = os.path.abspath(os.path.join(hist_dir, "Sessions"))
        tdat = getlasttrack(sess_dir)
        if tdat is False:
            return False
    else:  # remotely derived
        # get and parse playlist source code
        page = requests.get(conf.url)
        tree = html.fromstring(page.text)
        item = tree.xpath('(//div[@class="playlist-trackname"]/text())[last()]')
        tdat = item

    # cleanup
    tdat = str(tdat)
    tdat = tdat.replace("['", "").replace("']", "").replace("[]", "").replace("\\n", "").replace("\\t", "") \
        .replace("[\"", "").replace("\"]", "")
    tdat = tdat.strip()

    if tdat == "":
        return False

    t = tdat.split(" - ", 1)

    if t[0] == '.':
        artist = ''
    else:
        artist = c.a_pref + t[0] + c.a_suff

    if t[1] == '.':
        song = ''
    elif conf.quote == 1:  # handle quotes
        song = c.s_pref + "\"" + t[1] + "\"" + c.s_suff
    else:
        song = c.s_pref + t[1] + c.s_suff

    if artist == '' and song == '':
        return 'No Song Data'

    # handle multiline
    if conf.multi == 1:
        tdat = artist + "\n" + song
    elif song == '' or artist == '':
        tdat = artist + song
    else:
        tdat = artist + " - " + song

    if tdat != tk:
        return tdat
    else:
        return False


def getsessfile(directory, showlast=True):
    ds = os.path.abspath(os.path.join(directory, ".DS_Store"))

    if os.path.exists(ds):
        os.remove(ds)

    path = directory
    os.chdir(path)
    files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
    first = files[0]
    last = files[-1]

    if showlast:
        file = os.path.abspath(os.path.join(directory, last))
    else:
        file = os.path.abspath(os.path.join(directory, first))

    file_mod_age = time() - os.path.getmtime(file)

    if file_mod_age > 10:  # 2592000:
        return False
    else:
        sleep(0.5)
        return file


def getlasttrack(s):  # function to parse out last track from binary session file
    # get latest session file
    sess = getsessfile(s)
    if sess is False:
        return False

    # open and read session file
    while os.access(sess, os.R_OK) is False:
        sleep(0.5)

    with open(sess, "rb") as f:
        raw = f.read()

    # decode and split out last track of session file
    binstr = raw.decode('latin').rsplit('oent')  # split tracks
    byt = binstr[-1]  # last track chunk
    # print(byt)
    # determine if playing
    if (byt.find('\x00\x00\x00-') > 0 or  # ejected or is
            byt.find('\x00\x00\x00\x003') > 0):  # loaded, but not played
        return False

    # parse song
    sx = byt.find('\x00\x00\x00\x00\x06')  # field start

    if sx > 0:  # field end
        sy = byt.find('\x00\x00\x00\x00\x07')
        if sy == -1:
            sy = byt.find('\x00\x00\x00\x00\x08')
        if sy == -1:
            sy = byt.find('\x00\x00\x00\x00\t')
        if sy == -1:
            sy = byt.find('\x00\x00\x00\x00\x0f')

    # parse artist
    ax = byt.find('\x00\x00\x00\x00\x07')  # field start

    if ax > 0:
        ay = byt.find('\x00\x00\x00\x00\x08')  # field end
        if ay == -1:
            ay = byt.find('\x00\x00\x00\x00\t')
        if ay == -1:
            ay = byt.find('\x00\x00\x00\x00\x0f')

    # cleanup and return
    if ax > 0:
        bin_artist = byt[ax + 4:ay].replace('\x00', '')
        str_artist = bin_artist[2:]
    else:
        str_artist = '.'

    if sx > 0:
        bin_song = byt[sx + 4:sy].replace('\x00', '')
        str_song = bin_song[2:]
    else:
        str_song = '.'

    t_info = str(str_artist).strip() + " - " + str(str_song).strip()
    t_info = t_info

    return t_info


def writetrack(f, t=""):  # write new track info
    file = f
    with open(file, "w", encoding='utf-8') as f:
        print("writing...")
        f.write(t)


# END FUNCTIONS ####


if __name__ == "__main__":
    init()
    sys.exit(app.exec_())
