#! /usr/bin/env python

useStr = """
 --Display water usage graph from data found in waterlog.txt--
 Usage:
  wetgraph  [--first=<F>] [--last=<L>] [--minimum=<M>] [--blockfile <B>] [--times <B,E>] [--ratefile <R>] [--savefile <S>] [--offline] [--double]
  wetgraph -h | --help
  wetgraph -v | --version

 Options:
  -h --help               Show this screen.
  -b --blockfile <B>      Name for output block file [default: ]
  -f --first <F>          first day of range [default: 18-02-26].
  -l --last <L>           last day of range [default: now].
  -m --minimum <M>        smallest volume (gallons) to show [default: 2].
  -r --ratefile <R>       Name for output rate file [default: ]
  -s --savefile <S>       Name for output image file [default: ]
  -t --times <B,E>        select time of day range  [default: 0:0:0,23:59:59].
  -o --offline            don't retrieve waterlog.txt
  -d --double             don't skip every other meter tick
  -v --version            show the version
    """

import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pylab as plt
import matplotlib.dates as pdate
import docopt
from wetbin import *


"""

    Reminders:
        datetime.strptime( s, '%y-%m-%d %H:%M:%S' )             parse a time string into a  datetime object
        datetime.timetuple()                                    convert datetime object to a 9-tuple
        time.mktime(x)                                          convert 9-tuple to a time float (secs since epoch 1970-01-01)
        time.localtime(x)                                       convert time.time_struct to a 9-tuple
        time.strftime('%y-%m-%d %H:%M:%S',x)                    format a 9-tuple
"""



def makeGraph(opts):
    global oneTickVol

    # do complete rows that include the start and stop bins
    tStart = opts['--times'].split(',')[0]
    dtFirst = time.mktime(datetime.strptime( opts['--first']+' '+tStart, '%y-%m-%d %H:%M:%S' ).timetuple())
    if 'now' in opts['--last']:  # default --last means show usage
        dtLast2 = time.mktime(time.localtime(time.time()))
    else:
        dtLast2 = time.mktime(datetime.strptime( opts['--last']+' 23:59:59', '%y-%m-%d %H:%M:%S' ).timetuple())
    print 'From',time.strftime('%y-%m-%d %H:%M:%S',time.localtime(dtFirst)),
    print 'to',time.strftime('%y-%m-%d %H:%M:%S',time.localtime(dtLast2)), 'inclusive'

    bringFile(opts['--offline'])
    lines = getWaterLines()                     # get a list of the raw file lines
    stamps = genStamps(opts)
    lines = sliceWaterLines(lines,opts['--first'],opts['--last'])
    stamps = getStampList(lines)                # make a list of time floats

    if not opts['--double']:
        stamps = stamps[::2]
        oneTickVol = oneTickVol*2.0

    selStamps = [x for x in stamps if dtFirst < x < dtLast2]
    print '%d ticks = %.0f gal or %.1f ccf'%(len(selStamps),len(selStamps)*oneTickVol,len(selStamps)*oneTickVol/748.02)
    diffStamps = [selStamps[i+1]-selStamps[i] for i in range(len(selStamps)-1)]

    rates = [oneTickVol*60.0/(x+0.01) for x in diffStamps]
    if len(opts['--ratefile']):
        with open(opts['--ratefile'],'w') as fb:
            for i in range(len(rates[:-1])):
                fs = '%f'%(selStamps[i]%1)
                fb.write('%s%s,%7.2f\n'%(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(selStamps[i])),fs[1:],rates[i]))

    """ blocks = []
        for i, r in enumerate(rates[:-1]):    # blocks: make steps between rate periods
            blocks += [(selStamps[i],r)]
            blocks += [(selStamps[i+1],r)]
    """
    blocks = [f(i,r) for i, r in enumerate(rates[:-1])    # nested list comprehension version
                        for f in (lambda i,r:(selStamps[i],r), lambda i,r:(selStamps[i+1],r))]

    if len(opts['--blockfile']):
        with open(opts['--blockfile'],'w') as fb:
            for t in blocks:
                fs = '%f'%(t[0]%1)
                fb.write('%s%s,%7.2f\n'%(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t[0])),fs[1:],t[1]))
    xcoords, ycoords = zip(*blocks)
    xcoords = [datetime.fromtimestamp(x) for x in xcoords]
    xcoords = pdate.date2num(xcoords)
    fig, ax = plt.subplots()
    ax.plot_date(xcoords, ycoords,'k-', lw=2)
    # ax.set_yscale('log')
    ax.grid(True)
    fig.autofmt_xdate()
    if opts['--savefile']:
        fig.savefig(opts['--savefile'], bbox_inches='tight')
    else:
        plt.show()


if __name__ == '__main__':
    opts = docopt.docopt(useStr,version='0.0.2')
    # print opts
    makeGraph(opts)


