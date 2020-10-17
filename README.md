# __Now Playing__ in Serato ![Menu Bar Image](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/seratoPlaying.png?raw=true) 
__Now Playing__ is a tool written in Python to retrieve the current/last played song in Serato DJ.  

Starting with the current version, __Now Playing__ retrieves the current track from Serato's local history log and writes it to a plain text file which can be fed to streaming services and apps like OBS Studio. 

Previous versions of __Now Playing__ could only use a remote method of retrieving song data by leveraging the Serato Live Playlists functionality and scraping the data from the user's Live page on the Serato website. This legacy method remains an option for when the user requires streaming from a PC that is not the same on which Serato is running. 

It runs on the latest versions of macOS and Windows. 
[*__IMPORTANT__ note for macOS users*](#important-note)

#### New in version 1.3.0
* Added ability to read latest track info from Serato library history log. User now can choose  between local or remote (Serato Live Playlists) polling methods.
* Fix for issue where app would not launch on Windows due to not being able to create config.ini.
* Changed polling method for increased efficiency.
* Other enhancements due to new code and functionality.

## Considerations
__Now Playing__ was developed and tested in an environment using a Serato DJ compatible controller.  While it can be used with Serato DJ in DVS mode, this has not been tested. Therefore, behavior regarding the timing of song updates is not known. If song updates occur too quickly with DVS, try the Remote mode.

## Pre-requisites
__Only applies when using the Remote Mode to retrieve track data:__
* Active internet connection 
* Serato account with Live Playlists enabled

For more info on Serato Live Playlists: https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists
  
## Installation
### Mac
* Dowload the latest macOS release zip package here: https://github.com/e1miran/Now-Playing-Serato/releases/latest
* Unzip the package and place the unzipped 'SeratoNowPlaying.app' file in your "Applications" folder or any other location that you desire.
* Create a new, blank text file with the TextEdit app or similar text editor. Name it as you please, and save this text file anywhere you like on your mac and close the text editor.

#### *Important note for macOS users*
Due to security measures in macOS Sierra and later, apps downloaded from outside of the Mac App Store that are unsigned may have limitations placed on them that will prevent them from operating correctly, or even opening at all.  To prevent this from happening:

* Do not unzip the downloaded zip package directly to the folder from where you will be running it. Instead unzip it in a location such as the "Downloads" folder and then move the 'SeratoNowPlaying.app' to your destination folder (e.g., "Applications"). Then run the app from the destination folder.
* If after following the step above the app does not open, or you tried running it before moving the app, open Terminal and type: ```sudo xattr -r -d com.apple.quarantine /path/to/MyApp.app``` (replace with the correct path to the app).

### Windows
* Dowload the latest Windows release zip package here: https://github.com/e1miran/Now-Playing-Serato/releases/latest
* Unzip the package and copy the entire unzipped folder containing the 'SeratoNowPlaying.exe' file and supporting files to the directory you'd like the app to run from (i.e.: C:\Program Files).
* Create a new, blank text file with the Notepad app or similar text editor. Name it as you please, and save this text file anywhere you like on your pc and close the text editor.

### First time running the app
That's it. Execute the app from the location where you placed it. On Windows, you may need to right-click and select "Run as Administrator'. 

The first time you run the app a settings window will appear. Populate the fields accordingly and press save. Once saved, the app will start polling for new songs. The app can be controlled and exited from the system task tray on Windows or the menu bar icon on macOS.

![Task Tray GIF](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/snpWin.gif?raw=true) Windows

![Menu Bar GIF](https://github.com/e1miran/Now-Playing-Serato/blob/master/git-images/snpMac.gif?raw=true) macOS

### Uninstallation
The process for uninstalling the app is the same on both platforms.  Simply delete the file or folder from the location to where you pasted it.

## Settings
Upon initial execution of the app, a settings window will appear. Subsequently, the settings can be accessed from the icon in the Windows task tray or Mac menu bar.  The available configuration settings are:

* __Track Retrieval Mode__ - Select either Local or Remote mode.  Local is the preferred method of retrieval and the default.
    * Local mode uses Serato's local history log to acquire the track data.
    * Remote mode retrieves remote track data from Serato Live Playlists.  This mode requires constant connection to the internet and a Serato account with Live Playlists enabled. [How to use Remote Mode](#remote-mode)

* __Serato Library Path__ - (_Local Mode Only_) Location of the folder that contains Serato library and history data.  This folder named "\_Serato\_" is created and used by Serato DJ. If you keep your library on an external drive, you will have two "\_Serato\_" folders - one on the external drive and the other in the "Music" folder of your internal drive.  You must select the internal drive folder, as it is the one that contains the history folder and log files.

* __URL__ - (_Remote Mode Only_) The web address of your Serato Live Playlist
    * This should be something like: ```https://serato.com/playlists/<<USERNAME>>/live```
    
* __File__ - This is the file to which the current track info is written

* __Polling Interval__ - (_Remote Mode Only_) The amount of time, in seconds, that must elapse before the app checks for a new track.  If not populated, it will default to 10 seconds.
    * The goal is to retrieve the new track info immediately as it's updated to the Serato website.  However, too short of an interval could affect the website's performance.

* __Write Delay__ - The amount of time, in seconds to delay writing the new track info once it's retrieved. If not populated, it will default to 0 seconds.
    * A setting of zero will update the track info on screen immediately as a new track is detected.  This may be too soon for some DJ's mixing style, so a delay can be added.
    
* __Multiple Line Indicator__ - Selecting this option will write the song information on separate lines.
    * If selected, Artist will be written on the first line and Song on the second.  Otherwise it is written on one line, with Artist and song separated by a hyphen.

* __Song Quote Indicator__ - Selecting this option will surround the song title with quotes.

* __Prefix__ - Allows to specify characters to be written before the track info. 
    * e.g., "Now Playing: "

* __Suffix__ - Allows to specify characters to be written after the track info.

* __Notification Indicator__ - Selecting this option will show a system notification when new track info is detected.
    * This is useful for verifying that the app is actually polling and retrieving data.
    * The track info will be displayed in the notification.

## Usage
### Local Mode
1. Start the __Now Playing__ app.  The app is controlled and configured by accessing the menu from the icon in the windows system tray or Mac menu bar.

### Remote Mode
Remote mode can be used when the streaming PC is not the same as the PC on which Serato DJ is playing.
1. In Serato, make sure you enable Live Playlists and start a new session. From the [Serato website](https://support.serato.com/hc/en-us/articles/228019568-Live-Playlists):

>"To enable the Live Playlists feature go to the Expansion Pack tab on the Setup screen and check the Enable Live Playlists option. Once enabled, the Start Live Playlist button is now displayed in the History panel. Click this to start and stop your Live Playlist session."

2. Once a new playlist session is started, Serato will automatically open your web browser to your Live Playlist. __IMPORTANT:__ You will need to select "Edit Details" on the Live Playlist webpage and change your playlist to "Public", or else the __Now Playing__ app will not be able to retrieve any song data. The webpage does not need to remain open.  So you can close it once you ensure that the playlist has been made public.

3. Start the __Now Playing__ app.  The app can be controlled and configured by accessing the menu from the icon in the Windows system tray or Mac menu bar.
