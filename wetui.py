#! /usr/bin/env python

useStr = """
 -- Display table of water usage found in waterlog.txt --
 Usage:
  wetui  [--bins=<B>] [--columns=<C>] [--first=<F>] [--last=<L>] [--times <B,E>] [--width=<W>] [--offline] [--generator] [--iterator]
  wetui -h | --help
  wetui -v | --version

 Options:
  -h --help               Show this screen.
  -b --bins <B>           set bin count [default: 84].
  -c --columns <C>        column count in display [default: 12].
  -f --first <F>          first day of range [default: 15-11-21].
  -g --generator          use python generator instead of list
  -i --iterator           use python iterator instead of list
  -l --last <L>           last day of range [default: today].
  -t --times <B,E>        select time of day range  [default: 0:0:0,23:59:59].
  -w --width <W>          bin width in seconds [default: 3600].
  -o --offline            don't retrieve waterlog.txt
  -v --version            show the version
    """

"""
Todo:
  -d --days <S>           select days where 0 is Monday [default: 0123456].
  -x --xaxis <X>          use date or time a x axis [default: date]

"""
import docopt
from wetbin import *

# @profile
def main(opts):
    cntCols = int(opts['--columns'])
    tBinSecs = float(opts['--width'])
    cntBins = int(opts['--bins'])

    # do complete rows that include the start and stop bins
    if 'today' in opts['--last']:  # default --last means show cntBins back from now
      dtl = list(time.localtime(time.time()-tBinSecs*cntBins))
      if tBinSecs >= 86400:
        dtl[3], dtl[4], dtl[5] = 0,0,0
        dtInc = 86400.0*(7+dtl[6])
      if tBinSecs >= 3600:
        dtInc = 3600*24.0
        dtl[3], dtl[4], dtl[5] = 0,0,0
      elif tBinSecs >= 60:
        dtInc = 60*60.0
        dtl[4], dtl[5] = 0,0
      else:
        dtInc = 60.0
        dtl[5] = 0

      dtFirst = dtInc+time.mktime(time.struct_time(tuple(dtl)))
      opts['--first'] = time.strftime('%y-%m-%d',time.localtime(dtFirst))
    else:   # todo: this hasn't been tested like the above code -------
      tStart = opts['--times'].split(',')[0]
      dtFirst = makeTime(opts['--first']+' '+tStart)

    print 'start at',time.strftime('%y-%m-%d',time.localtime(dtFirst))
    cntBins = int(1.999+cntBins/cntCols)*cntCols  # round bins up to complete rows

    bringFile(opts['--offline'])
    if opts['--generator']:             # preferred
        stamps = genStamps(opts)
    elif opts['--iterator']:
        stamps = iterStamps(opts)
    else:
        lines = getWaterLines()
        lines = sliceWaterLines(lines,opts['--first'],opts['--last'])
        stamps = getStampList(lines)

    b, m = binTimes(stamps,dtFirst,tBinSecs,cntBins)
    showHeader(cntCols,m)
    showBined(b,cntCols,m)
    footer(stamps)


if __name__ == '__main__':
    opts = docopt.docopt(useStr,version='0.0.2')
                        # profiling 98k lines before sliceWaterLines to take it down to 553  : 4.31 S
                        #                      using sliceWaterLines                    553  : 0.11 S
                        #                      using generator                                 0.12
                        #                      using iterator                                  0.225

                        #  profiling on 98k stamps into 340 bins of 1 day each, w/o file transfer
                        #             simple       generator        iterator
    # print opts        #  Seconds     3.817         3.933            4.192
    main(opts)          #  mem MB     32.1          22.8             22.2


