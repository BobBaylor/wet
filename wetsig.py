#! /usr/bin/env python

useStr = """
 --Display appliance usage signature found in waterlog.txt--
 Usage:
  wetsig  [--first=<F>] [--last=<L>] [--minimum=<M>] [--times <B,E>] [--offline]
  wetsig -h | --help
  wetsig -v | --version

 Options:
  -h --help               Show this screen.
  -f --first <F>          first day of range [default: 15-11-07].
  -l --last <L>           last day of range [default: now].
  -m --minimum <M>        smallest volume (gallons) to show [default: 2].
  -t --times <B,E>        select time of day range  [default: 0:0:0,23:59:59].
  -o --offline            don't retrieve waterlog.txt
  -v --version            show the version
    """

import docopt
from wetbin import *

def isEdge(a,b,c):
  rChg = a+c-2*b  # (c-b)-(b-a) = c-2b --a = c+a-2b
  if -3.5 < rChg < 3.5:
    return False,rChg
  return True,rChg


"""
    Water usage by appliance assumed to have a rectangular rate shape: 0..rrr..0  where r is the flow rate (with some noise).
    Noise due to time stamp Quantization of 1 second r = K/d  where d is +/- 1 so r is between K/(d+1) and K/(d-1).
    Algorithm: walk the timestamps either in a flow or on an edge:
        edge is a rate outside of the Quant range for the previous rate.
        flow is between edges
        list start and end edge times, time diff, flow rate between edges, total ticks

    Reminders:
        datetime.strptime( s, '%y-%m-%d %H:%M:%S' )             parse a time string into a  datetime object
        datetime.timetuple()                                    convert datetime object to a 9-tuple
        time.mktime(x)                                          convert 9-tuple to a time float (secs since epoch 1970-01-01)
        time.localtime(x)                                       convert time.time_struct to a 9-tuple
        time.strftime('%y-%m-%d %H:%M:%S',x)                    format a 9-tuple
"""


if __name__ == '__main__':
    opts = docopt.docopt(useStr,version='0.0.2')
    # print opts

    lines = getWaterLines(opts['--offline'])     # get a list of the raw file lines
    stamps = getStampList(lines)                # make a list of time floats
    print 'len',len(stamps)

    # do complete rows that include the start and stop bins
    tStart = opts['--times'].split(',')[0]
    dtFirst = time.mktime(datetime.strptime( opts['--first']+' '+tStart, '%y-%m-%d %H:%M:%S' ).timetuple())
    if 'now' in opts['--last']:  # default --last means show usage
        dtLast2 = time.mktime(time.localtime(time.time()))
    else:
        dtLast2 = time.mktime(datetime.strptime( opts['--last']+' 23:59:59', '%y-%m-%d %H:%M:%S' ).timetuple())
    print 'From',time.strftime('%y-%m-%d %H:%M:%S',time.localtime(dtFirst)),
    print 'to',time.strftime('%y-%m-%d %H:%M:%S',time.localtime(dtLast2)), 'inclusive'

    selStamps = []
    for x in stamps:
        # print dtFirst, x, dtLast2
        if dtFirst < x < dtLast2:
            selStamps += [x]
    print 'len',len(selStamps)
    # print dtLast2
    #  walk through selStamps looking for the signature of an appliance
    diffStamps = [[selStamps[0],0,(False,0)],[selStamps[1],0,(False,0)]]
    for x in selStamps[2:]:
        diffStamps += [[x,oneTickVol*120.0/(x-diffStamps[-2][0]),isEdge(diffStamps[-2][0],diffStamps[-1][0],x)]]

    evts = []

    blkFirst = diffStamps[0]
    stampLast = diffStamps[0]
    volCnt = 0
    for x in diffStamps[1:]:
      # print x, stampLast
      if stampLast[2][0] and not x[2][0]:  # starting a new block
        volCnt, blkFirst = 1, x
      elif not stampLast[2][0] and x[2][0]: # ending a block
        evts += [[blkFirst,x,volCnt]]
      volCnt = volCnt+1
      stampLast = x

    for x in evts[2:]:
      if oneTickVol*x[2] > float(opts['--minimum']):
        print time.strftime('%a %y-%m-%d %H:%M',time.localtime(x[0][0])),
        print 'for',time.strftime('%M',time.gmtime(x[1][0]-x[0][0])),
        print 'at %6.2f gpm'%(oneTickVol*60.0*x[2]/(x[1][0]-x[0][0])),
        print '= %6.1f'%(oneTickVol*x[2])
        # print '%7.3f'%oneTickVol*60.0/(x[1][0]-x[0][0])

