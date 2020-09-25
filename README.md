# __Now Playing__ in Serato ![Menu Bar Image](https://github.com/e1miran/Now-Playing-Serato/blob/master/seratoPlaying.png?raw=true) 
__Now Playing__ is a tool written in Python to retrieve the current/last played song in Serato DJ.  It uses the Serato Live Playlists functionality and scrapes the data from the user's Live page on the Serato website.  The data is written to a plain text file which can be fed to streaming services and apps like OBS Studio. 

It runs on the latest versions of macOS and Windows.

## Pre-requisites
* Active internet connection
* Serato account with Live Playlists enabled

For more info on Serato Live Playlists: https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists
  
## Installation
### Mac
* Dowload the latest macOS release zip package here: https://github.com/e1miran/Now-Playing-Serato/releases/latest
* Unzip the package and copy the entire unzipped folder containing both the app and config file to your "Applications" folder.
* From that location, open the config file in a text editor, such as TextEdit, and configure the settings as indicated in the Configuration section below.
* Create a new, blank text file with the TextEdit app or similar text editor. Name and save this text file anywhere you like on your mac and close the text editor.

### Windows
* Dowload the latest Windows release zip package here: https://github.com/e1miran/Now-Playing-Serato/releases/latest
* Unzip the package and copy the entire unzipped folder containing all files to the directory you'd like the app to run from (i.e.: C:\Program Files).
* From that location, open the config file in a text editor, such as Notepad, and configure the settings as indicated in the Configuration section below.
* Create a new, blank text file with the Notepad app or similar text editor. Name and save this text file anywhere you like on your pc and close the text editor.

That's it.  Upon startup, the applicaton does not open a window. However, on Windows you'll see the app's icon in the system task tray at the bottom right. For Mac, the app icon will be added to the menu bar at the top right of your screen. Right-click on this icon for a menu of actions.

macOS  ![Menu Bar GIF](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/snpMac.gif?raw=true)  Windows  ![Task Tray GIF](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/snpWin.gif?raw=true)

### Uninstallation
The process for uninstalling the app is the same on both platforms.  Simply delete the entire folder from the location to where you pasted it.

## Configuration
Open the config file in a text editor and configure the settings as needed.  See the examples below:

```
# URL address of your Serato Live Playlist (use quotes)
url = "https://serato.com/playlists/<<USERNAME>>/live"

# Path to the file where current track info is written (use quotes)
file = "C:\<<PATH>>\NowPlaying.txt"

# Time (seconds) that needs to elapse before polling for a new song
time = 7.5

# Multiple Line flag:  0 = all data written on one line, 1 = artist on first line and song on second line
multi = 1

# Quotes Around Song Name flag:  0 = no quotes, 1 = quotes
quote = 1

# Prefix:  characters to be written before data (use quotes). i.e.: "Now Playing: "
pref = ""

# Suffix:  characters to be written after data (use quotes). Can be used for blank space at the end of scrolling text. i.e.: "                       "
suff = ""
```

## Usage
1. In Serato, make sure you enable Live Playlists and start a new session. From the [Serato website](https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists):

>"To enable the Live Playlists feature go to the Expansion Pack tab on the Setup screen and check the Enable Live Playlists option. Once enabled, the Start Live Playlist button is now displayed in the History panel. Click this to start and stop your Live Playlist session."

2. Once a new playlist session is started, Serato will automatically open your web browser to your Live Playlist. __IMPORTANT:__ You will need to select "Edit Details" on the Live Playlist webpage and change your playlist to "Public", or else the __Now Playing__ app will not be able to retrieve any song data.

3. Start the __Now Playing__ app.  You can check the target text file to see what is being written.
