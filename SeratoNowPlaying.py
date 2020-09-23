#!/usr/bin/env python3


__author__ = "Ely Miranda"
__version__ = "1.0.0"
__license__ = "MIT"

from lxml import html
import tkinter
from tkinter import messagebox
import requests
import configparser
import threading
import rumps
import sys

# hide main window
root = tkinter.Tk()
root.withdraw()


# get variables from config.ini
config = configparser.ConfigParser()
config.sections()
config.read('../../../config.ini')

url = config['Settings']['url'].replace("\"", "")
file = config['Settings']['file'].replace("\"", "")
time = config['Settings']['time']
multi = config['Settings']['multi']
quote = config['Settings']['quote']
pref = config['Settings']['pref'].replace("\"", "")
suff = config['Settings']['suff'].replace("\"", "")
track = ""


# CONFIG ERROR HANDLING
if bool(url) is False or bool(file) is False:
    messagebox.showerror("Error Message", "There is an error in your config file.\n\nYour config file is missing \
the URL or File settings\n\nThe app will now exit.")
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


# FUNCTIONS BLOCK ####

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


# main code runner
def main():
    threading.Timer(time, main).start()
    # get current track data
    global track
    print("checking...")
    new = gettrack()

    # compare current track data to previous and write to file if different
    if new != track:
        track = new
        writetrack(pref + track + suff)

    return
# END FUNCTIONS BLOCK ####


# execute code
main()


# statusbar
@rumps.clicked('Quit')
def clean_up_before_quit(_):
    writetrack("")
    print("closing...")
    rumps.quit_application()


app = rumps.App("SeratoNowPlaying", "Now Playing ▶", quit_button=None)
app.run()


if __name__ == "__main__":
    main()
