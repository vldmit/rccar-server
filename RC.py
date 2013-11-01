# -*- mode: python -*-
#
# Wireless protocol controller

from twisted.internet import reactor
from twisted.internet import threads
from twisted.internet import defer
from twisted.python import log
from twisted.python.failure import Failure

import serial
from xbee import XBee

import settings

class UnexpectedFrameException(Exception):
    pass

class FrameNoACKException(Exception):
    pass

class AlreadyRequestedException(Exception):
    pass


class RCProtocol(object):
    waiting = False
    request = None
    rssi = 0
    rssi_remote = 0
    
    signal = 0
    _frameid = '\x01'

    cnt_snt = 0
    cnt_rcv = 0

    def __init__(self):
        log.msg("Initializing XBee port...")
        self._ser = serial.Serial(settings.SERIAL_PORT, 
                                  settings.SERIAL_SPEED,
                                  timeout = settings.SERIAL_TIMEOUT)
        self._xbee = XBee(self._ser, api_mode = 2)
        reactor.addSystemEventTrigger('before','shutdown',self._xbee.halt)
        reactor.callLater(0, self._loop)

    def _loop(self):
        def cb(xframe):
            self.cnt_rcv = self.cnt_rcv + 1
            #log.msg(xframe)
            if self.waiting is False:
                log.err(UnexpectedFrameException())
                reactor.callLater(0, self._loop)
                return
            d = self.request
            
            if xframe['id'] == 'tx_status':
                if xframe['status'] == '\x00':
                    pass
                else:
                    failure = Failure(exc_value=FrameNoACKException("Frame was not delivered %s" % xframe['status']))
                    d.errback(failure)
            if xframe['id'] == 'rx':
                self.waiting = False
                self.rssi = ord(xframe['rssi'])
                d.callback(xframe['rf_data'])
            reactor.callLater(0, self._loop)
        def eb(err):
            reactor.callLater(0, self._loop)
        d = threads.deferToThread(self._xbee.wait_read_frame)
        d.addCallbacks(cb, eb)

    def send_frame(self, data):
        if self.waiting is True:
            failure = Failure(exc_value=AlreadyRequestedException("Another request already sent"))
            d = defer.Deferred()
            d.errback( failure )
            return d
            
        fid = self.gen_frameid()
        self.cnt_snt = self.cnt_snt + 1
        #log.msg("Sending frame")
        self._xbee.send('tx', frame_id=fid, 
                        dest_addr = '\x00\x00',
                        data = data)
        self.waiting = True
        d = defer.Deferred()
        d.setTimeout(0.1)
        self.request = d
        return d

    def gen_frameid(self):
        "Sequential generator of frame ids"
        fid = ord(self._frameid) + 1
        if fid > 255:
            fid = 1
        return chr(fid)

