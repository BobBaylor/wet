
""" wetbin.py water log timestamp binning script
    This can be run from any of my 4 locations and it will make sure the waterlog.txt file is copied to where I am.
    This should be run from the wet folder.
"""
import time
import os
import platform
import socket
from datetime import date, datetime

ip260 = '67.170.222.39'
# 73.222.30.143
tStartStr = '15-11-21 00:00:00'
tBinSecs = 3600.0
cntBins = 228
cntCols = 12

oneCycleVol = 0.748
oneTickVol = oneCycleVol*0.5     # about 3/8 of a gallon = 3 pints


def makeTime(s):   # seems like this should be in the lib but I can't find it
  try:
    if len(s) < 18:
      t = time.mktime(datetime.strptime( s, '%y-%m-%d %H:%M:%S' ).timetuple())
    else:
      t = time.mktime(datetime.strptime( s, '%y-%m-%d %H:%M:%S.%f' ).timetuple())
  except ValueError:
    print 'makeTime() ValueError'
    t = None
  return t


def binTimes(tms,first,wid,cnt):
  bined = [0]*cnt
  slope = 1.0/wid
  bins = [first+i*wid for i in range(cnt+1) ]
  for t in tms:
    i = int((t-first)*slope)
    if i >= 0 and i<cnt:
      bined[i] = bined[i]+1
  return bined, bins


# returns 1 ip address, not 127.0.0.0 as a list of octet strings. '88' means pi; '192' means 260; '172' means SRS and '10' meas 7C
def getMyIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))  # connecting to a UDP address doesn't send packets
    retS = s.getsockname()[0]
    s.close()
    return retS.split('.')      # e.g. ['172','25','96','168'] at SRS


def showHeader(c,b):
  w = b[1]-b[0]
  if w >= 86400:
    tFmt = '%a'
  elif w >= 3600:
    tFmt = '%H'
  elif w >= 60:
    tFmt = '%M'
  else:
    tFmt = '%S'
  # print time.strftime('%y-%m-%d %H:%M:%S',time.localtime(b[0])), w
  tms = [time.strftime(tFmt,time.localtime(b[i])) for i in range(c)]
  print '%-16s'%('gallons')+'%5s'*c%tuple(tms),


def showBined(d,c,m):
  i = 0
  for j, x in enumerate(d):
    if i == 0:
      print '\n%5.1f%11s'% (oneTickVol*sum(d[j:j+c]),time.strftime('%a %H:%M',time.localtime(m[j]))),
    if x>0:
        print '%4.0f'%(x*oneTickVol),
    else:
        print '%4s'%(''),
    i += 1
    if i >= c:
      i = 0
  print''


def getStampList(lines):    # convert timestamp text lines to a list of numbers ready for binning
    stamps = []
    tmin = makeTime('15-09-01 12:00:00')
    for i, ln in enumerate(lines):
        t = makeTime(ln)
        if t is None or t < tmin:
            print 'Bad input at line %6d: %s' %(i,ln)
        else:
            # stamps += [time.mktime(datetime.strptime( ln, '%y-%m-%d %H:%M:%S' ).timetuple())]
            stamps += [t]
    return stamps


def getWaterLines(bUseExisting):    # get a list filled with all the timestamp text lines
    # I could do this with platform.system() which returns 'Linux', 'Darwin', or 'Windows'
    if not bUseExisting:
        # determine where we are so we can get the waterlog.txt file here: 260, SRS, 7C, or on the pi
        """
        myip = getMyIp()    # returns 1 ip address, not 127.0.0.0 as a list of octet strings. '88' means pi; '192' means 260; '172' means SRS and '10' meas 7C
        if '192' in myip[0] and '88' in myip[3]:  # I'm on the pi the file is already here
            pass
        elif '172' in myip[0]:                    # I'm at the SRS ip
            os.system('pscp -i "C:\BobMenu\Good Stuff\ssh-rsa-pi.ppk" -P 801 pi@73.222.30.143:/home/pi/wet/waterlog.txt .' )  # from SRS
        elif '192' in myip[0]:                    # I'm on the 260 mac
            os.system('scp pi@192.168.2.88:/home/pi/wet/waterlog.txt .' ) # from 260
        elif '10' in myip[0]:                     # I'm at 7C
            os.system('scp -P 801 pi@73.222.30.143:/home/pi/wet/waterlog.txt .' )       # from 7C
        else:   # I don't know where I am
            print 'where am I?','.'.join(myip)
            return []
        """
        myos = platform.system()    # returns 'Linux', 'Darwin', or 'Windows'
        if 'Linux' in myos:  # I'm on the pi the file is already here
            pass
        elif 'Windows' in myos:                    # I'm at the SRS ip
            os.system('pscp -i "C:\BobMenu\Good Stuff\ssh-rsa-pi.ppk" -P 801 pi@%s:/home/pi/wet/waterlog.txt .'%ip260 )  # from SRS
        elif 'Darwin' in myos:                     # I'm at 7C
            os.system('scp -P 801 pi@%s:/home/pi/wet/waterlog.txt .'%ip260 )       # from 7C
        else:   # I don't know where I am
            print 'where am I?',myos
            return []

    with open('waterlog.txt','r') as fin:
        flines = fin.readlines()
    lines = [ln.strip() for ln in flines]
    return lines

def footer(stamps):
    print "Saw %d lines" %(len(stamps))
    print 'last 4 intervals at %.3f gpm'%(oneTickVol*240.0/(stamps[-1]-stamps[-5]))
    print '   last interval at %.3f gpm'%(oneTickVol*60.0/(stamps[-1]-stamps[-2]))

if __name__ == '__main__':
    print 'wetbin.py stand alone'
    lines = getWaterLines(False)
    stamps = getStampList(lines)
    b, m = binTimes(stamps,makeTime(tStartStr),tBinSecs,cntBins)
    showBined(b,cntCols,m)
    footer(stamps)

