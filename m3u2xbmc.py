#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import os
import json
import linecache
from channels import channel_list

IFACE = 'eth1'
CHANNELS_PY = 'channels.py'
SUNLINE_M3U = 'iptv.m3u'
XMLTV_FILE = 'xmltv.xml'
IPTVSIMPLE_M3U = 'output.m3u'
BASE_ICONS_PATH = 'file:///home/user/channel/logo'
M3U_EXT_LINE = '#EXTINF:-1 tvg-id="TVG_ID" hts-number="HTS_NUMBER" tvg-shift=-1 tvg-logo="CHANNEL_ICON", CHANNEL_NAME'

chlist = dict()


def get_channel_data(chname):
    
    xmlfile = open(XMLTV_FILE)
    channel_id = ''
    channel_icon = ''
    line_counter = 0

    if channel_list.get(chname)[1]: #Is there an icon name in the channels.py list?
        channel_icon = os.path.join(BASE_ICONS_PATH, channel_list.get(chname)[1])

    xml_chname = channel_list.get(chname)[0]
                
    xml_chname = re.sub('\+', '\+', xml_chname) #Backslacshing some simbols in order to find the 
    xml_chname = re.sub('\(', '\(', xml_chname) #channel names that includes '+', '(' or ')' in
    xml_chname = re.sub('\)', '\)', xml_chname) #the xmlvtv.xml file.
    xml_chname = ">" + xml_chname + "<"

    for line in xmlfile:
        line_counter += 1

        if re.match('<programme', line): #Interrupt the search once the channel list is ended.
            break

        if re.search(xml_chname, line): #Searching for channel name in xmltv.xml file.
            channel_id = linecache.getline(XMLTV_FILE, line_counter - 1) #The string with the channel ID is a one line above the current. 
            channel_id = re.compile('.*"(.*)".*').match(channel_id).group(1) #Get the channel ID.

            if not channel_icon: #If there was no icon found in the channels.py before, trying to find it in the xmltv.xml
                channel_icon = linecache.getline(XMLTV_FILE, line_counter + 1) #A string with the icon is the one line below the current.
                if re.match("<icon src", channel_icon): #Is there the icon-field?
                    channel_icon = re.split('"', channel_icon)[-2] #Get the icon url.

            xmlfile.close()
            return(channel_id, channel_icon)

    xmlfile.close()
    return(channel_id, channel_icon)


def write_m3u(chlist):
    iptvsimple_m3u = open(IPTVSIMPLE_M3U, 'w')
    iptvsimple_m3u.write('#EXTM3U' + '\n\n')

    for channel in chlist.values():
        ext_line = re.sub('CHANNEL_NAME', channel['name'], M3U_EXT_LINE)
        ext_line = re.sub('TVG_ID', channel['id'], ext_line)
        ext_line = re.sub('CHANNEL_ICON', channel['icon'], ext_line)
        ext_line = re.sub('HTS_NUMBER', channel['number'], ext_line)
        iptvsimple_m3u.write(ext_line + '\n')
        iptvsimple_m3u.write('udp://@' + channel['address'] + ':' + channel['port'] + '\n')

    iptvsimple_m3u.close()


def read_m3u(m3u):
    m3ufile = open(m3u)
    chcnt = 0

    for line in m3ufile:
        if re.search('V.I.P', line): #Skip the VIP channels
            m3ufile.close()
            break

        if re.match('#EXTINF', line):
            chname = re.compile('.*, (.*)').match(line).group(1) #Get the channel name

            if channel_list.get(chname):
                channel_data = get_channel_data(chname)
                chid = channel_data[0]
                chicon = channel_data[1]
                chnumber = channel_list.get(chname)[2]
                chname = channel_list.get(chname)[0]
                newchannel = False
            else:
                print 'The "' + chname + '" channel is not in list. Please add it first to channels.py list.'
                newchannel = True

        if re.match('udp', line) and newchannel == False:
            chaddr = line[7:].split(':')[0]
            chport = re.compile('.*:(.*)$').match(line).group(1)
            chcnt += 1
            chaddress = line

            chlist[chname] = {'num': chcnt, 'name': chname, 'number': chnumber, 'address': chaddr, 'port': chport, 'id': chid, 'icon': chicon}
    return(chlist)
    m3ufile.close()

def writejson(filename, data):
    output = open(filename, 'w')
    json.dump(data, output, indent=8, ensure_ascii=False)
    output.close()

def writehts(chlist):
    iptvpath = 'iptvservices'
    chpath = 'channels'
    xmltvpath = "epggrab/xmltv/channels"
    if not os.path.exists(iptvpath):
        os.mkdir(iptvpath)
    if not os.path.exists(chpath):
        os.mkdir(chpath)
    if not os.path.exists(xmltvpath):
        os.makedirs(xmltvpath)

    for channel in chlist.values():
        
        #iptvservices/iptv_?
        jssvc = {'pmt': 0,
                'pcr': 0,
                'group': channel['address'],
                'disabled': 0,
                'mapped': 1,
                'interface': IFACE,
                'port': channel['port'],
                'channelname': channel['name'],}
        writejson(os.path.join(iptvpath, "iptv_" + str(channel['num'])), jssvc)

        #channels/?
        jschan = {'name': channel['name'],
                'dvr_extra_time_pre': 0,
                'dvr_extra_time_post': 0,
                'tags': [ ]}
        if channel['number'] is not None:
            jschan['channel_number'] = int(channel['number'])
        if channel['icon'] is not None:
            jschan['icon'] = channel['icon']
        writejson(os.path.join(chpath, str(channel['num'])), jschan)

        #epggrab/xmltv/channels/?   
        if channel['id']:
            jsepg = {
                    'name': channel['name'],
                    'icon': channel['icon'],
                    'channels': [int(channel['number'])]
                    }
            writejson(os.path.join(xmltvpath, channel['id']), jsepg)

def generate(m3u):
    m3ufile = open(m3u)
    chpy = open(CHANNELS_PY, 'w')
    chlist = dict()
    chcount = 0

    chpy.write('#!/usr/bin/python\n# -*- coding: utf-8 -*-\n\n\nchannel_list = {\n')

    for line in m3ufile:
        if re.match('#EXTINF', line):
            chcount +=1
            chname = re.compile('.*, (.*)').match(line).group(1)
            chpy.write("'%s': %30s', '', '%d'],\n" % (chname, "['"+chname, chcount))
    chpy.write('}')
    chpy.close()

def main():
    chlist = read_m3u(SUNLINE_M3U)
    write_m3u(chlist)
    writehts(chlist)
    #generate(SUNLINE_M3U)
    print "\n\n Done!"

if __name__ == '__main__':
    main()
