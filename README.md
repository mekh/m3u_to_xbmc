m3u_to_xbmc
===========

Converts the m3u-iptv list to the IPTV Simple file format and generates the xbmc-tvheadend files/folders structure.
It's not compatible with Tvheadend 3.9x! It also doesn't support channel tags (I don't use it).

Why is this done?
-----------------
My ISP changes the IPTV-channel list very often. It can change ip-addresses, add or remove some channels, etc.
Each time I had to change the Tvheadend settings manualy. I've finally had enough of that monkey job! :)

Usage
-----
The files m3u2xbmc.py, channels.py, iptv.m3u and xmltv.xml must be located in the same directory.
xmltv.xml can be downloaded here: http://www.teleguide.info/download/new3/xmltv.xml.gz (ungzip it first!)

Just run the m2u2xbmc.py in order to get the output.m3u (in IPTV Simple format) and the Tvheadend configuration files/folders.
To import the configuration to the Tvheadend you have to stop the tvheadend service, delete its configuration and remove cached epg database.
Example:

    $wget -O - http://www.teleguide.info/download/new3/xmltv.xml.gz |gunzip -c > xmltv.xml
    $cp iptv.m3u m3u2xbmc.py channels.py xmltv.xml ~/.hts/tvheadend
    $sudo service tvheadend stop
    $cd ~/.hts/tvheadend
    $rm epgdb.v2
    $rm iptvservices/* channels/* epggrab/xmltv/channels/*
    $python m3u2xbmc.py
    $sudo service tvheadend start

After that you have to go to Tvheadend configuration page (http://127.0.0.1:9981) and select your epg-grabber
(Configuration -> Channel/EPG -> EPG Grabber).

Files format
------------
Channel name and address are read from the M3U file (iptv.m3u):

    #EXTINF:-1 , Channel 1
    udp://@226.226.1.1:1234
    #EXTINF:-1 , Channel 2
    udp://@226.226.1.2:1234

File channels.py contains the ISP channel name ("Channel 1"), the correspondent xmltv.xml channel name ("Channel 1 (France)") and the additional
information about channel icon and its position in Tvheadend channel list.

    {'Provider's channel name : ['Corresponding xmltv name', 'Local icon (if it exists)', 'Channel number in the hts list']}

At first you have to fill up this file manually.

Output
------

The script generates the output.m3u file in the IPTV Simple format. 

    #EXTM3U

    #EXTINF:-1 tvg-id="11111" hts-number="1" tvg-shift=-1 tvg-logo="file:///home/user/channels/icon/Channel_1.png", Channel 1
    udp://@226.226.1.1:1234
    #EXTINF:-1 tvg-id="22222" hts-number="2" tvg-shift=-2 tvg-logo="http://www.icons.com/images/channel/22222.gif", Channel 2
    udp://@226.226.1.2:1234

You can easily change the output format by edititng the 'M3U_EXT_LINE' line in m3u2xbmc.py file.

Finally, the script generates the Tvheadend configuration files and folders.
