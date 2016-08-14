#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
from datetime import date, datetime
import signal
import sys


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


# d = date.date.now()
# print d.strftime('%y-%m-%d %H:%M:%S')


GPIO.setmode(GPIO.BOARD)
GPIO.setup(7,GPIO.IN)
print 'Current state is', GPIO.input(7)
GPIO.setwarnings(False)
GPIO.setup(10,GPIO.OUT)
bLed = GPIO.LOW
cntT = 0
cntS = 0
v = GPIO.input(7)
tStart = time.time()
try:
  while True:
    t = GPIO.input(7)
    time.sleep(1)
    GPIO.output(10,bLed)
    if bLed == GPIO.LOW:
        bLed = GPIO.HIGH 
    else:
        bLed = GPIO.LOW
    cntS += 1
    if t != v:
      print t,
      v = t
      cntT += 1
      fout = open('/home/pi/wet/waterlog.txt','a')
      fout.write('%s\n' % datetime.now().strftime('%y-%m-%d %H:%M:%S'))
      fout.close()

except KeyboardInterrupt:
  GPIO.cleanup()
  print '[%s] done'%get_now()


print "Saw %d"%cntT, "in %d:%02d:%02d" %timeSince( tStart)

