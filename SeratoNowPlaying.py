#!/usr/bin/env python3


__author__ = "Ely Miranda"
__version__ = "1.1.0"
__license__ = "MIT"

'''
CHANGELOG:
* Added support for Windows.
* Added additional error handling for missing config file and invalid config values.
* Replaced rumps library with PyQt5, since rumps was not cross-platform compatible.
* Added ability to stop and start the playlist polling from the system tray / menu bar.
* Changed from app name to icon in macOS menu bar, for uniformity with Windows.
'''

import requests
import configparser
import threading
from lxml import html
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
import tkinter
from tkinter import messagebox
import os
import sys


# error message pop-up
def alert(title, msg):
    root = tkinter.Tk()
    root.withdraw()

    messagebox.showerror(title, msg)
    root.destroy()

    return


# get variables from config.ini
config = configparser.ConfigParser()
config.sections()

# set paths for bundled files
if getattr(sys, 'frozen', False) and sys.platform == "darwin":
    bundle_dir = sys._MEIPASS
    working_dir = os.path.abspath(os.path.dirname(sys.executable))
    working_dir = working_dir.split("SeratoNowPlaying.app/Contents/MacOS")
    config_file = os.path.abspath(working_dir[0] + "config.ini")
    ico = os.path.abspath(os.path.join(bundle_dir, "icon.ico"))
else:
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.ini"))
    ico = os.path.abspath(os.path.join(os.path.dirname(__file__), "icon.ico"))

# read config and raise error if not found
if os.path.exists(config_file):
    config.read(config_file)
else:
    alert("Error", "The config file was not found.\n\nPlease place it in the same \
directory as the app.\n\nThe app will now exit.")
    sys.exit()

url = config['Settings']['url'].replace("\"", "")
file = config['Settings']['file'].replace("\"", "")
time = config['Settings']['time']
multi = config['Settings']['multi']
quote = config['Settings']['quote']
pref = config['Settings']['pref'].replace("\"", "")
suff = config['Settings']['suff'].replace("\"", "")

tmr = ""
track = ""
dun = 0

# CONFIG ERROR HANDLING
if bool(url) is False or bool(file) is False:
    alert("Error", "There is an error in your config file.\n\nYour config file is missing \
the URL or File settings.\n\nThe app will now exit.")
    sys.exit()

if "<<USERNAME>>" in url or "<<PATH>>" in file:
    alert("Error", "There is an error in your config file.\n\nPlease make sure the 'url' and \
'path' settings contain valid values.\n\nThe app will now exit.")
    sys.exit()

if not os.path.exists(file):
    alert("Error", "There is an error in the config file.\n\nThe provided text file path is \
not found.\n\nThe app will now exit.")
    sys.exit()

if bool(time) is False:
    time = 10

if bool(multi) is False or multi == "0":
    multi = 0
else:
    multi = 1

if bool(quote) is False or quote == "0":
    quote = 0
else:
    quote = 1

time = float(time)
multi = int(multi)
quote = int(quote)

app = QApplication([])
app.setQuitOnLastWindowClosed(False)


# FUNCTIONS BLOCK ####
# main code runner
def main():
    global tmr, track
    if dun == 0:
        tmr = threading.Timer(time, main)
        tmr.start()

    # get current track data
    print("checking...")
    new = gettrack()

    # compare current track data to previous and write to file if different
    if new != track:
        track = new
        writetrack(pref + track + suff)

    if dun == 1:
        tmr.cancel()


# get last played track
def gettrack():
    # get and parse playlist source code
    page = requests.get(url)
    tree = html.fromstring(page.text)
    item = tree.xpath('(//div[@class="playlist-trackname"]/text())[last()]')

    # clean-up
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
    if quote == 1:
        song = "\"" + song + "\""

    # handle multiline
    if multi == 1:
        tdat = artist + "\n" + song
    else:
        tdat = artist + " - " + song

    return tdat


def writetrack(t):
    # open text file, write, close
    f = open(file, "w", encoding='utf-8')
    print("writing...")
    f.write(t)
    f.close()


def starttmr():
    global dun
    dun = 0

    if actStart.isEnabled():
        actStart.setEnabled(False)

    if not actStop.isEnabled():
        actStop.setEnabled(True)

    if not actExit.isEnabled():
        actExit.setEnabled(True)
    main()


def stoptmr():
    global dun
    dun = 1

    if not actStart.isEnabled():
        actStart.setEnabled(True)

    if actStop.isEnabled():
        actStop.setEnabled(False)

    if not actExit.isEnabled():
        actExit.setEnabled(True)


def cleanquit():
    global dun
    dun = 1
    tray.setVisible(False)
    writetrack("")
    sys.exit()
# END FUNCTIONS BLOCK ####


# create systemtray UI
icon = QIcon(ico)

tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setToolTip("Now Playing ▶")
tray.setVisible(True)

menu = QMenu()

# create systemtray options and actions
actTitle = QAction("Now Playing v1.1")
menu.addAction(actTitle)
actTitle.setEnabled(False)
menu.addSeparator()

actStart = QAction("Start")
actStart.triggered.connect(starttmr)
actStart.setEnabled(False)
menu.addAction(actStart)

actStop = QAction("Stop")
actStop.triggered.connect(stoptmr)
actStop.setEnabled(True)
menu.addAction(actStop)

actExit = QAction("Exit")
actExit.triggered.connect(cleanquit)
actExit.setEnabled(True)
menu.addAction(actExit)

# add menu to the systemtray UI
tray.setContextMenu(menu)

# initiate main process
main()


if __name__ == "__main__":
    main()
    sys.exit(app.exec_())
