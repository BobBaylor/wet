#!/usr/bin/env python


import time
from datetime import date, datetime, timedelta
import signal
import sys
fOutName = '/home/pi/wet/waterlog.txt'
tLedDuration = 0.5
VERBOSE_METER = 1
VERBOSE_LED   = 2
bfVerbose = 2

try:
    import RPi.GPIO as GPIO
except ImportError:
    fOutName = '.\stub.txt'
    bfVerbose = VERBOSE_LED
    class gpio:                 # -------  test class to stub out the GPIO not available on a non-pi host ----------
        def __init__(self):
            print '** No RPi.GPIO found. Creating test stub, instead. **'
            self.BOARD = None
            self.IN = None
            self.OUT = None
            self.LOW = 0
            self.HIGH = 1
            self.state = False

        def setmode(self,x):
            pass

        def setup(self,x,y):
            pass

        def setwarnings(self,x):
            pass

        def cleanup(self):
            pass

        def output(self,x,y):
            if bfVerbose & VERBOSE_LED:
                s = 'ON ' if y else 'OFF'
                print s, datetime.now()
            pass

        def input(self,x):
            self.state = not self.state
            return 1 if self.state else 0

    GPIO = gpio()        # -----------  instantiate the test class -------------------------------


def get_now():
    "get the current date and time as a string"
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def sigterm_handler(_signo, _stack_frame):
    "When sysvinit sends the TERM signal, cleanup before exiting."
    print '[%s] received signal %r, exiting...'%(get_now(),_signo)
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)


def timeSince( timeStart ):
    s = int(time.time() - timeStart)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return h, m, s


def timeDiff(prev,nxt):
    return (time.mktime(nxt.timetuple())+nxt.microsecond*1e-6)-(time.mktime(prev.timetuple())+prev.microsecond*1e-6)


GPIO.setmode(GPIO.BOARD)
GPIO.setup(7,GPIO.IN)
print 'Current state is', GPIO.input(7)
GPIO.setwarnings(False)
GPIO.setup(10,GPIO.OUT)
bLed = GPIO.LOW
cntT = 0
v = GPIO.input(7)
tStart = time.time()
tLed = datetime.now()
try:
  while True:
    t = GPIO.input(7)   # capture the water meter state and a timestamp
    tstamp = datetime.now()

    if timeDiff(tLed,tstamp) > tLedDuration:        # flash the LED on a 1 Hz schedule
        tLed = tLed + timedelta(microseconds = tLedDuration*1e6)
        GPIO.output(10,bLed)
        if bLed == GPIO.LOW:
            bLed = GPIO.HIGH
        else:
            bLed = GPIO.LOW

    if t != v:          # did the water meter state change?
      if bfVerbose & VERBOSE_METER:
        print t,
      v = t
      cntT += 1
      fout = open(fOutName,'a')
      fout.write('%s\n' % tstamp.strftime('%y-%m-%d %H:%M:%S.%f'))
      fout.close()
      time.sleep(0.09)   # add some debounce time

    time.sleep(0.01)

except KeyboardInterrupt:
  GPIO.cleanup()
  print '[%s] done'%get_now()


print "Saw %d"%cntT, "in %d:%02d:%02d" %timeSince( tStart)

