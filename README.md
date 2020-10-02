# __Now Playing__ in Serato ![Menu Bar Image](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/seratoPlaying.png?raw=true) 
__Now Playing__ is a tool written in Python to retrieve the current/last played song in Serato DJ.  It uses the Serato Live Playlists functionality and scrapes the data from the user's Live page on the Serato website.  The data is written to a plain text file which can be fed to streaming services and apps like OBS Studio. 

It runs on the latest versions of macOS and Windows. 
[__IMPORTANT__ note for macOS Mojave users](#important-note-for-macos-mojave-users)

## Pre-requisites
* Active internet connection
* Serato account with Live Playlists enabled

For more info on Serato Live Playlists: https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists
  
## Installation
### Mac
* Dowload the latest macOS release zip package here: https://github.com/e1miran/Now-Playing-Serato/releases/latest
* Unzip the package and place the unzipped 'SeratoNowPlaying.app' file in your "Applications" folder or any other location that you desire.
* Create a new, blank text file with the TextEdit app or similar text editor. Name and save this text file anywhere you like on your mac and close the text editor. You can name it whatever you like.

[__IMPORTANT__ note for macOS Mojave users](#important-note-for-macos-mojave-users)

### Windows
* Dowload the latest Windows release zip package here: https://github.com/e1miran/Now-Playing-Serato/releases/latest
* Unzip the package and copy the entire unzipped folder containing the 'SeratoNowPlaying.exe' file and supporting files to the directory you'd like the app to run from (i.e.: C:\Program Files).
* Create a new, blank text file with the Notepad app or similar text editor. Name and save this text file anywhere you like on your pc and close the text editor. You can name it whatever you like.

That's it. Execute the app from the location where you placed it. The first time you run the app a settings window will appear. Populate the fields accordingly and press save. Once saved, the app will start polling for new songs. The app can be controlled and exited from the system task tray on Windows or the menu bar icon on macOS.

![Task Tray GIF](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/snpWin.gif?raw=true) Windows

![Menu Bar GIF](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/snpMac.gif?raw=true) macOS

### Uninstallation
The process for uninstalling the app is the same on both platforms.  Simply delete the file or folder from the location to where you pasted it.

## Settings
Upon initial execution of the app, a settings window will appear. Subsequently, the settings can also be accessed from the icon in the Windows task tray or Mac menu bar.  The available configuration settings are:

* URL - The web address of your Serato Live Playlist
    * This should be something like: ```https://serato.com/playlists/<<USERNAME>>/live```
    
* File - This is the file to which the current track info is written

* Polling Interval - The amount of time, in seconds, that must elapse before the app checks for a new track.  If not populated, it will default to 10 seconds.
    * The goal is to retrieve the new track info immediately as it's updated to the Serato website.  However, too short of an interval could affect the website's performance.

* Write Delay - The amount of time, in seconds to delay writing the new track info once it's retrieved. If not populated, it will default to 0 seconds.
    * A setting of zero will update the track info on screen immediately as a new track is detected.  This may be too soon for some DJ's mixing style, so a delay can be added.
    
* Multiple Line Indicator - Selecting this option will write the song information on separate lines.
    * If selected, Artist will be written on the first line and Song on the second.  Otherwise it is written on one line, with Artist and song separated by a hyphen.

* Song Quote Indicator - Selecting this option will surround the song title with quotes.

* Prefix - Allows to specify characters to be written before the track info. 
    * e.g., "Now Playing: "

* Suffix - Allows to specify characters to be written after the track info.

* Notification Indicator - Selecting this option will show a system notification when new track info is detected.
    * This is useful for verifying that the app is actually polling and retrieving data.
    * The track info will be displayed in the notification.

## Usage
1. In Serato, make sure you enable Live Playlists and start a new session. From the [Serato website](https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists):

>"To enable the Live Playlists feature go to the Expansion Pack tab on the Setup screen and check the Enable Live Playlists option. Once enabled, the Start Live Playlist button is now displayed in the History panel. Click this to start and stop your Live Playlist session."

2. Once a new playlist session is started, Serato will automatically open your web browser to your Live Playlist. __IMPORTANT:__ You will need to select "Edit Details" on the Live Playlist webpage and change your playlist to "Public", or else the __Now Playing__ app will not be able to retrieve any song data. The webpage does not need to remain open.  So you can close it once you ensure that the playlist has been made public.

3. Start the __Now Playing__ app.  The app can be controlled and configured by accessing the menu from the icon in the Windows system tray or Mac menu bar.

###IMPORTANT Note For macOS Mojave users
Mojave users may encounter that the app will not open on the initial execution even after allowing it permission in the system security settings.  This is not a direct issue with the app, instead it's due to an Apple security measure for unsigned apps called [App Translocation](https://lapcatsoftware.com/articles/app-translocation.html).
Before attempting to execute the app for the first time, you may follow one of these solutions:

1. Simply move the app from its current directory to a different directory. Then move it back.

2. Open Terminal and type: ```sudo xattr -r -d com.apple.quarantine /path/to/MyApp.app``` (replace with the correct path).
