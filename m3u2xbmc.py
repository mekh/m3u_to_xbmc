#!/usr/bin/python
# -*- coding: utf-8 -*-
#===============================================================================
# m3u2xbmc.py - Converts the m3u-iptv list to the IPTV Simple file format and 
# generates the xbmc-tvheadend files/folders structure.
#  
# (c) 2015 Alexandr V.Mekh
# (c) 2012 Gregor Rudolf
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license.php
#===============================================================================
import re
import os
import sys
import json
import argparse
import linecache

IFACE = 'eth1'
CHANNELS_PY = 'channels.lst'
SOURCE_M3U = 'iptv.m3u'
XMLTV_FILE = 'xmltv.xml'
IPTVSIMPLE_M3U = 'output.m3u'
BASE_ICONS_PATH = 'file:///home/user/channels/logo'
M3U_EXT_LINE = '#EXTINF:-1 tvg-id="TVG_ID" hts-number="HTS_NUMBER" tvg-shift=-1 tvg-logo="CHANNEL_ICON", CHANNEL_NAME'

chlist = dict()


def get_channel_data(chname, xmltv, channel_list):
  with open(xmltv, 'r') as xmlfile:
      channel_id = ''
      channel_icon = ''
      line_counter = 0

      if channel_list.get(chname)[1]:  # Is there an icon name in the channels.py list?
          channel_icon = os.path.join(BASE_ICONS_PATH, channel_list.get(chname)[1])

      xml_chname = channel_list.get(chname)[0]

      xml_chname = re.sub('\+', '\+', xml_chname)  # Backslacshing some symbols in order to find the
      xml_chname = re.sub('\(', '\(', xml_chname)  # channel names that includes '+', '(' or ')' in
      xml_chname = re.sub('\)', '\)', xml_chname)  # the xmlvtv.xml file.
      xml_chname = ">" + xml_chname + "<"

      for line in xmlfile:
          line_counter += 1

          if "<programme" in line: #Interrupt the search once the channel list is ended.
              break

          if re.search(xml_chname, line): #Searching for channel name in xmltv.xml file.
              channel_id = linecache.getline(xmltv, line_counter - 1) #The string with the channel ID is a one line above the current.
              channel_id = re.compile('.*"(.*)".*').match(channel_id).group(1) #Get the channel ID.

              if not channel_icon: #If there was no icon found in the channels.py before, trying to find it in the xmltv.xml
                  channel_icon = linecache.getline(xmltv, line_counter + 1) #A string with the icon is the one line below the current.
                  if re.match("<icon src", channel_icon): #Is there the icon-field?
                      channel_icon = re.split('"', channel_icon)[-2] #Get the icon url.
                  else:
                      channel_icon = ''
              return channel_id, channel_icon
  return channel_id, channel_icon


def write_m3u(chlist, output):
  with open(output, 'w') as iptvsimple_m3u:
      iptvsimple_m3u.write('#EXTM3U' + '\n\n')

      for channel in chlist.values():
          ext_line = re.sub('CHANNEL_NAME', channel['name'], M3U_EXT_LINE)
          ext_line = re.sub('TVG_ID', channel['id'], ext_line)
          ext_line = re.sub('CHANNEL_ICON', channel['icon'], ext_line)
          ext_line = re.sub('HTS_NUMBER', channel['number'], ext_line)
          iptvsimple_m3u.write(ext_line + '\n')
          iptvsimple_m3u.write('udp://@' + channel['address'] + ':' + channel['port'] + '\n')


def read_m3u(m3u, xmltv, channels):
  chcnt = 0
  channel_list = dict()
  chdata = list()

  with open(channels, 'r') as chfile:
      for line in chfile:
          chname = re.compile('(.*):.*').match(line).group(1) #Get channel name
          chdata = re.compile('.*:\s+(.*)$').match(line).group(1).split(',') #Get channel data
          channel_list.update([(chname, chdata)])
  with open(m3u, 'r') as m3ufile:
      for line in m3ufile:
          if 'V.I.P' in line: #Skip VIP channels
              break

          if re.match('#EXTINF', line):
              chname = re.compile('.*, (.*)').match(line).group(1) #Get channel name

              if channel_list.get(chname):
                  channel_data = get_channel_data(chname, xmltv, channel_list)
                  chid = channel_data[0]
                  chicon = channel_data[1]
                  chnumber = channel_list.get(chname)[2]
                  chname = channel_list.get(chname)[0]
                  newchannel = False
              else:
                  print 'The "' + chname + '" channel is not in list. Please add it first to channels.lst.'
                  newchannel = True

          if re.match('udp', line) and newchannel == False:
              chaddr = line[7:].split(':')[0]
              chport = re.compile('.*:(.*)$').match(line).group(1)
              chcnt += 1
              chaddress = line

              chlist[chname] = {'num': chcnt, 'name': chname, 'number': chnumber, 'address': chaddr, 'port': chport, 'id': chid, 'icon': chicon}
      return chlist


def writejson(filename, data):
  with open(filename, 'w') as output:
      json.dump(data, output, indent=8, ensure_ascii=False)


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


def generate(m3u, output):
  chcount = 0
  with open(m3u, 'r') as m3ufile:
      with open(output, 'w') as chpy:
          for line in m3ufile:
              if re.match('#EXTINF', line):
                  chcount +=1
                  chname = re.compile('.*, (.*)').match(line).group(1)
                  chpy.write("%s: %30s,,%d\n" % (chname, chname, chcount))

          print ('\nFile %s succesfuly generated!\nTo generate the IPTV Simple M3U list, run:\n\
                  python m3u2xbmc.py -c %s') % (str(output), str(output))


def opt_parser():
  parser = argparse.ArgumentParser(
      prog='m3u2xbmc', 
      description='Converts the m3u-iptv list to the IPTV Simple file format and generates the xbmc-tvheadend files/folders structure',
      epilog='(c) Alexandr Mekh, 2015')
  parser.add_argument('-s', '--source', default=SOURCE_M3U, metavar='', help='Source IPTV M3U file name')
  parser.add_argument('-o', '--output', default=IPTVSIMPLE_M3U, metavar='', help='Output IPTV Simple M3U file name')
  parser.add_argument('-c', '--channels', default=CHANNELS_PY, metavar='', help='Channel list file')
  parser.add_argument('-x', '--xmltv', default=XMLTV_FILE, metavar='', help='Source xmlvtv file')
  parser.add_argument('-g', '--generate', action='store_true', default=False, help='Generate new "channels" file using source M3U')

  return parser


def main():
  parser = opt_parser()
  args = parser.parse_args(sys.argv[1:])

  if args.generate:
      generate(args.source, args.channels)
  elif not args.generate:
      chlist = read_m3u(args.source, args.xmltv, args.channels)
      write_m3u(chlist, args.output)
      writehts(chlist)
  else:
      parser.print_help()

if __name__ == '__main__':
  main()
