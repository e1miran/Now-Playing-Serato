#!/usr/bin/env python3


__author__ = "Ely Miranda"
__version__ = "1.2.0"
__license__ = "MIT"

'''
CHANGELOG:
* Added UI for settings configuration. No more user accessible config.ini file.
* Added ability to delay writing newly retrieved track info to the text file.
* Added ability to pause/resume from the system tray menu. This allows the user 
  to suspend retrieval of new track info.
* Added ability to show system notification when new track is detected. This can
  be turned on/off in settings. Default is 'off'.
* Multiple code enhancements due to new functionality.
'''

import requests
import configparser
import threading
from lxml import html
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QLabel, \
    QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLineEdit, QFileDialog, QWidget
from PyQt5.QtGui import QIcon, QFont
from time import sleep
import os
import sys


# define global variables
tmr = track = ""
ini = paused = xit = 0

# set paths for bundled files
if getattr(sys, 'frozen', False) and sys.platform == "darwin":
    bundle_dir = sys._MEIPASS
    config_file = os.path.abspath(os.path.join(bundle_dir, "config.ini"))
    ico = os.path.abspath(os.path.join(bundle_dir, "icon.ico"))
else:
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin/config.ini"))
    ico = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin/icon.ico"))

# create needed object instances
config = configparser.ConfigParser()
app = QApplication([])
app.setQuitOnLastWindowClosed(False)


class ConfigFile:  # read and write to config.ini 
    def __init__(self, cparser, cfile):
        self.cparser = cparser
        self.cfile = cfile

        try:
            self.cparser.read(config_file)
            self.cparser.sections()

            self.url = config.get('Settings', 'url')
            self.file = config.get('Settings', 'file')
            self.interval = config.get('Settings', 'interval')
            self.delay = config.get('Settings', 'delay')
            self.multi = is_bool(config.get('Settings', 'multi'))
            self.quote = is_bool(config.get('Settings', 'quote'))
            self.pref = config.get('Settings', 'pref').replace("|_0", " ")
            self.suff = config.get('Settings', 'suff').replace("|_0", " ")
            self.notif = is_bool(config.get('Settings', 'notif'))

            if is_number(self.interval) is False:
                self.interval = 10
            if is_number(self.delay) is False:
                self.delay = 0

            self.interval = float(self.interval)
            self.delay = float(self.delay)
        except configparser.NoOptionError:
            pass

    def put(self, url, file, interval, delay, multi, quote, pref, suff, notif):
        self.cparser.set('Settings', 'url', url)
        self.cparser.set('Settings', 'file', file)
        self.cparser.set('Settings', 'interval', interval)
        self.cparser.set('Settings', 'delay', delay)
        self.cparser.set('Settings', 'multi', str(multi))
        self.cparser.set('Settings', 'quote', str(quote))
        self.cparser.set('Settings', 'pref', pref)
        self.cparser.set('Settings', 'suff', suff)
        self.cparser.set('Settings', 'notif', str(notif))

        cf = open(self.cfile, 'w')
        self.cparser.write(cf)
        cf.close()


# settings UI
class SettingsUI:  # create settings form window
    def __init__(self, conf, conffile):
        self.conf = conf
        self.conffile = conffile
        self.window = QWidget()
        self.window.setWindowFlag(Qt.CustomizeWindowHint, True)
        self.window.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.window.setWindowFlag(Qt.WindowMinMaxButtonsHint, False)
        self.window.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.window.setWindowTitle('Now Playing - Settings')
        self.layoutV = QVBoxLayout()
        self.layoutH1 = QHBoxLayout()
        self.layoutH2 = QHBoxLayout()
        self.layoutH3 = QHBoxLayout()
        self.layoutH4 = QHBoxLayout()
        self.layoutH5 = QHBoxLayout()
        self.fBold = QFont()
        self.fBold.setBold(True)

        # error section
        self.errLabel = QLabel()
        self.errLabel.setStyleSheet('color: red')
        # url
        self.urlLabel = QLabel('URL')
        self.urlLabel.setFont(self.fBold)
        self.urlDesc = QLabel('Web address of your Serato Playlist\ne.g., https://serato.com/playlists/USERNAME/live')
        self.urlDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.urlLabel)
        self.urlEdit = QLineEdit()
        self.layoutV.addWidget(self.urlDesc)
        self.layoutV.addWidget(self.urlEdit)
        # file
        self.fileLabel = QLabel('\nFile')
        self.fileLabel.setFont(self.fBold)
        self.fileDesc = QLabel('The file to which current track info is written.')
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
that must elapse before checking for new track info.\n(Default = 10.0)')
        self.intervalDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.intervalLabel)
        self.layoutV.addWidget(self.intervalDesc)
        self.intervalEdit = QLineEdit()
        self.intervalEdit.setMaximumSize(40, 35)
        self.layoutV.addWidget(self.intervalEdit)
        # delay
        self.delayLabel = QLabel('Write Delay')
        self.delayLabel.setFont(self.fBold)
        self.delayDesc = QLabel('Amount of time, in seconds, \
to delay writing the new track info once it\'s retrieved.\n(Default = 0)')
        self.delayDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.delayLabel)
        self.layoutV.addWidget(self.delayDesc)
        self.delayEdit = QLineEdit()
        self.delayEdit.setMaximumSize(40, 35)
        self.layoutV.addWidget(self.delayEdit)
        # multi-line
        self.multiLabel = QLabel('Multiple Line Indicator')
        self.multiLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.multiLabel)
        self.multiCbox = QCheckBox()
        self.multiCbox.setMaximumSize(30, 35)
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
        self.quoteCbox.setMaximumSize(30, 35)
        self.layoutH3.addWidget(self.quoteCbox)
        self.quoteDesc = QLabel('Surround the song title \
with quotes.')
        self.quoteDesc.setStyleSheet('color: grey')
        self.layoutH3.addWidget(self.quoteDesc)
        self.layoutV.addLayout(self.layoutH3)
        # prefix
        self.prefixLabel = QLabel('Prefix')
        self.prefixLabel.setFont(self.fBold)
        self.prefixDesc = QLabel('Characters to be written before track info.')
        self.prefixDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.prefixLabel)
        self.layoutV.addWidget(self.prefixDesc)
        self.prefixEdit = QLineEdit()
        self.layoutV.addWidget(self.prefixEdit)
        # suffix
        self.suffixLabel = QLabel('Suffix')
        self.suffixLabel.setFont(self.fBold)
        self.suffixDesc = QLabel('Characters to be written after track info.')
        self.suffixDesc.setStyleSheet('color: grey')
        self.layoutV.addWidget(self.suffixLabel)
        self.layoutV.addWidget(self.suffixDesc)
        self.suffixEdit = QLineEdit()
        self.layoutV.addWidget(self.suffixEdit)
        # notify
        self.notifLabel = QLabel('Notification Indicator')
        self.notifLabel.setFont(self.fBold)
        self.layoutV.addWidget(self.notifLabel)
        self.notifCbox = QCheckBox()
        self.notifCbox.setMaximumSize(30, 35)
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
        self.urlEdit.setText(c.url)
        self.fileEdit.setText(c.file)
        self.intervalEdit.setText(str(c.interval))
        self.delayEdit.setText(str(c.delay))
        self.multiCbox.setChecked(c.multi)
        self.quoteCbox.setChecked(c.quote)
        self.prefixEdit.setText(c.pref)
        self.suffixEdit.setText(c.suff)
        self.notifCbox.setChecked(c.notif)

    def upd_conf(self):
        url = self.urlEdit.text()
        file = self.fileEdit.text()
        interval = self.intervalEdit.text()
        delay = self.delayEdit.text()
        multi = str(self.multiCbox.isChecked())
        quote = str(self.quoteCbox.isChecked())
        pref = self.prefixEdit.text().replace(" ", "|_0")
        suff = self.suffixEdit.text().replace(" ", "|_0")
        notif = str(self.notifCbox.isChecked())

        c = ConfigFile(self.conf, self.conffile)
        c.put(url, file, interval, delay, multi, quote, pref, suff, notif)

    # file button action
    def on_filebutton_clicked(self):
        filename = QFileDialog.getOpenFileName(self.window, 'Open file', '.', '*.txt')
        if filename:
            self.fileEdit.setText(filename[0])

    # cancel button action
    def on_cancelbutton_clicked(self):
        actConfig.setEnabled(True)
        self.close()
        self.upd_win()
        self.errLabel.setText('')

    # save button action
    def on_savebutton_clicked(self):
        if 'https://serato.com/playlists' not in self.urlEdit.text() and \
                'https://www.serato.com/playlists' not in self.urlEdit.text():
            self.errLabel.setText('* URL is invalid or missing')
            return

        if self.fileEdit.text() == "":
            self.errLabel.setText('* File is required')
            return

        self.upd_conf()
        self.close()
        self.errLabel.setText('')

        global ini
        if ini == 0:
            ini = 1
            actPause.setText('Pause')
            actPause.setEnabled(True)
            main()

    def show(self):
        actConfig.setEnabled(False)
        self.upd_win()
        self.window.show()
        self.window.setFocus()

    def close(self):
        actConfig.setEnabled(True)
        self.window.hide()

    def exit(self):
        self.window.close()


# create window object instance
win = SettingsUI(config, config_file)


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
    if not os.path.exists(config_file):
        # create config.ini
        config.add_section('Settings')
        url = file = interval = delay = pref = suff = ''
        multi = quote = notif = False
        conf = ConfigFile(config, config_file)
        conf.put(url, file, interval, delay, multi, quote, pref, suff, notif)

        win.show()
    else:
        global ini
        ini = 1
        actPause.setText('Pause')
        actPause.setEnabled(True)
        main()


def main():  # track polling process
    global tmr, track
    conf = ConfigFile(config, config_file)

    tmr = threading.Timer(conf.interval, main)

    if xit == 0:
        tmr.start()

    if paused == 0:
        # get current track data
        print("checking...")
        new = gettrack(conf)
        # compare current track data to previous and write to file if different
        if new != track:
            track = new

            # display new track info in system notification
            if conf.notif == 1:
                tip = new.replace("\n", " - ").replace("\"", "")
                # tip = (tip[:50] + '...') if len(tip) > 50 else tip
                tray.showMessage("Now Playing ▶ ", tip, 1000)

            sleep(conf.delay)
            tinfo = conf.pref + new + conf.suff
            writetrack(conf.file, tinfo)


def gettrack(c):  # get last played track
    conf = c
    # get and parse playlist source code
    page = requests.get(conf.url)
    tree = html.fromstring(page.text)
    item = tree.xpath('(//div[@class="playlist-trackname"]/text())[last()]')

    # cleanup
    tdat = str(item)
    tdat = tdat.replace("['", "").replace("']", "").replace("[]", "").replace("\\n", "").replace("\\t", "") \
        .replace("[\"", "").replace("\"]", "")
    tdat = tdat.strip()

    if tdat == "":
        return tdat

    t = tdat.split(" - ", 1)
    artist = t[0]
    song = t[1]

    # handle quotes
    if conf.quote == 1:
        song = "\"" + song + "\""

    # handle multiline
    if conf.multi == 1:
        tdat = artist + "\n" + song
    else:
        tdat = artist + " - " + song

    return tdat


def writetrack(f, t=""):  # write new track info
    file = f
    f = open(file, "w", encoding='utf-8')
    print("writing...")
    f.write(t)
    f.close()


def unpause():  # unpause polling
    global paused
    paused = 0

    actPause.setText('Pause')
    actPause.triggered.connect(pause)


def pause():  # pause polling
    global paused
    paused = 1

    actPause.setText('Resume')
    actPause.triggered.connect(unpause)


def cleanquit():  # quit app and cleanup
    global xit
    xit = 1
    tray.setVisible(False)
    file = ConfigFile(config, config_file).file
    writetrack(file)
    sys.exit()
# END FUNCTIONS ####


# create settings UI window
configWin = QWidget()
layout = QVBoxLayout()

# create systemtray UI
icon = QIcon(ico)
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setToolTip("Now Playing ▶")
tray.setVisible(True)
menu = QMenu()

# create systemtray options and actions
actTitle = QAction("Now Playing v1.2")
menu.addAction(actTitle)
actTitle.setEnabled(False)

actConfig = QAction("Settings")
actConfig.triggered.connect(win.show)
menu.addAction(actConfig)
menu.addSeparator()

actPause = QAction()
actPause.triggered.connect(pause)
menu.addAction(actPause)
actPause.setEnabled(False)

actExit = QAction("Exit")
actExit.triggered.connect(cleanquit)
menu.addAction(actExit)

# add menu to the systemtray UI
tray.setContextMenu(menu)


if __name__ == "__main__":
    init()
    sys.exit(app.exec_())
