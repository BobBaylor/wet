#! /usr/bin/env python

""" wetbin.py water log timestamp binning functions
    This can be run from any of my 4 locations and it will make sure the waterlog.txt file is copied to where I am.
    This should be run from the wet folder.

"""
import time
import os
import platform
import socket
from datetime import date, datetime
try:
    from wetip import ip260
except ImportError:
    ip260 = '127.0.0.0'
# ip260 = '73.222.30.143'

tStartStr = '15-11-21 00:00:00'
tBinSecs = 3600.0
cntBins = 228
cntCols = 12

oneCycleVol = 0.748
oneTickVol = oneCycleVol*0.5     # about 3/8 of a gallon = 3 pints


def makeTime(s):   # seems like this should be in the lib but I can't find it
  try:
    if len(s) < 18:
        t = time.mktime(datetime.strptime( s, '%y-%m-%d %H:%M:%S' ).timetuple())   # old style up to 2016-06-13
    else:
        v = datetime.strptime( s, '%y-%m-%d %H:%M:%S.%f' )                         # new style with microseconds
        t = time.mktime(v.timetuple())+(v.microsecond*1e-6)
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
def getMyIp():              # not used
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
  print '%-17s'%('gallons')+'%5s'*c%tuple(tms),


def showBined(d,c,m):
  i = 0
  for j, x in enumerate(d):
    if i == 0:
      print '\n%6.1f%11s'% (oneTickVol*sum(d[j:j+c]),time.strftime('%a %H:%M',time.localtime(m[j]))),
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


def sliceWaterLines(lines,first,last):
    bInRange = False
    print 'slicing',first,'to',last
    x = []
    for l in lines:
        if bInRange:
            x += [l]
            if last in l:
                bInRange = False
        else:
            if first in l:
                bInRange = True
                x += [l]
    return x

def bringFile(bUseExisting):
    if bUseExisting:
        print 'Using existing waterlog.txt'
        return
    # determine the OS so we can use the proper cmd to get the waterlog.txt file here
    myos = platform.system()    # returns 'Linux', 'Darwin', or 'Windows'
    if 'Linux' in myos:         # I'm on the pi: the file is already here
        pass                    # todo: differentiate between the wet host and another Linux box
    elif 'Windows' in myos:                    # I'm on my Win box
        eRet = os.system('pscp -i "C:\BobMenu\Good Stuff\ssh-rsa-pi.ppk" -P 801 pi@%s:/home/pi/wet/waterlog.txt .'%ip260 )
        if eRet:
            raise OSError(eRet,'Windows failed to scp the file with code %d'%eRet)
    elif 'Darwin' in myos:                     # I'm at 7C
        eRet = os.system('scp -P 801 pi@%s:/home/pi/wet/waterlog.txt .'%ip260 )       # I'm on one of my macs
        if eRet:
            raise (eRet,'OSX failed to scp the file with code %d'%eRet)
    else:   # I don't know where I am
        print 'where am I?',myos


class iterStamps:
    def __init__(self, opts):
        self.opts = opts
        self.lNo = 0         # line number counter to help with bad input
        self.len = 0         # stamp counter. Only counts the stamps within the requested date range
        self.tmin = makeTime('15-09-01 12:00:00')
        self.bInRange = False
        self.fin = open('waterlog.txt','r')

    def __iter__(self):
        return self

    def __len__(self):
        return self.len

    def next(self):
        while True:
            l, self.lNo = self.fin.readline(), self.lNo+1
            if not l:
                self.fin.close()
                raise StopIteration          # readline() returns zero len string on EOF: we're done
            l = l.strip()
            if self.bInRange:
                if self.opts['--last'] in l:
                    self.bInRange = False
            else:
                if self.opts['--first'] in l:
                    self.bInRange = True
            if self.bInRange:
                t = makeTime(l)
                if t is None or t < self.tmin:
                    print 'Bad input at line %6d: %s' %(self.len,l)
                else:
                    self.len = self.len+1
                    return t


def getWaterLines():    # get a list filled with all the timestamp text lines
    # I could do this with platform.system() which returns 'Linux', 'Darwin', or 'Windows'
    with open('waterlog.txt','r') as fin:
        flines = fin.readlines()
    lines = [ln.strip() for ln in flines]
    return lines


def genStamps(opts):
    tmin = makeTime('15-09-01 12:00:00')
    bInRange = False
    with open('waterlog.txt','r') as fin:
        for i, l in enumerate(fin.readlines()):
            l = l.strip()
            if bInRange:
                if opts['--last'] in l:
                    bInRange = False
            else:
                if opts['--first'] in l:
                    bInRange = True
            if bInRange:
                t = makeTime(l)
                if t is None or t < tmin:
                    print 'Bad input at line %6d: %s' %(i,ln)
                else:
                    yield t


def footer(stamps):
    try:
        print "Saw %d lines" %(len(stamps))
        print 'last 4 intervals at %.3f gpm'%(oneTickVol*240.0/(stamps[-1]-stamps[-5]))
        print '   last interval at %.3f gpm'%(oneTickVol*60.0/(stamps[-1]-stamps[-2]))
    except (AttributeError, TypeError):
        print 'stamps missing  __len__ or __getitem__'


if __name__ == '__main__':
    print 'Running wetbin.py stand alone. Try wetui.py for more features.'
    lines = getWaterLines()
    stamps = getStampList(lines)
    b, m = binTimes(stamps,makeTime(tStartStr),tBinSecs,cntBins)
    showBined(b,cntCols,m)
    footer(stamps)

