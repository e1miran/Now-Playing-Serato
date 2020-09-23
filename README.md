# __Now Playing__ in Serato
__Now Playing__ is a tool written in Python to retrieve the current/last played song in Serato DJ.  It uses the Serato Live Playlists functionality and scrapes the data from the user's Live page on the Serato website.  The data is written to a plain text file which can be fed to streaming services and apps like OBS Studio. 

Initial release supports __MacOS only__, but a Windows release is being developed.

# Pre-requisites
* Active internet connection
* Serato account with Live Playlists enabled

For more info on Serato Live Playlists: https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists
  
# Installation
* Dowload the latest release zip package
* Unzip the package and copy the entire unzipped folder containing both the app and config file to your "Applications" folder
* Open the config file in a text editor, such as TextEdit, and configure the settings as indicated in the Configuration section below.
* Create a new, blank text file with the TextEdit app or similar text editor. Name and save this text file anywhere you like on your mac and close the text editor.

That's it.  Upon startup, the applicaton does not open a window.  However, you will see a "Now Playing" indicator in your menu bar.  Click on this indicator for a prompt to quit the application.

![Menu Bar Image](https://github.com/e1miran/Now-Playing-Serato/blob/master/menu-bar.png?raw=true)

# Configuration
Open the config file in a text editor and configure the settings as needed.  See the examples below:

```
# URL address of your Serato Live Playlist (use quotes)
url = "https://serato.com/playlists/<<USERNAME>>/9-21-20"

# Path to the file where current track info is written (use quotes)
file = "/Users/MacBook/Music/NowPlaying.txt"

# Time (seconds) that needs to elapse before rechecking for new song (default is 10)
time = 7.5

# Multiple Line flag - 0 = all data written on one line, 1 = artist on first line and song on second line
multi = 1

# Quotes around song name - 0 = no quotes, 1 = quotes
quote = 1

# Prefix - characters to be written before data (use quotes)
pref = "Now Playing "

# Suffix - characters to be written after data (use quotes)
suff = ""
```

# Usage
1. In Serato, make sure you enable Live Playlists and start a new session. From the [Serato website](https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists):

>"To enable the Live Playlists feature go to the Expansion Pack tab on the Setup screen and check the Enable Live Playlists option. Once enabled, the Start Live Playlist button is now displayed in the History panel. Click this to start and stop your Live Playlist session."

2. Once a new playlist session is started, Serato will automatically open your web browser to your Live Playlist. __IMPORTANT:__ You will need to select "Edit Details" on the Live Playlist webpage and change your playlist to "Public", or else the __Now Playing__ app will not be able to retrieve any song data.

3. Start the __Now Playing__ app.  You can check the target text file to see what is being written.
