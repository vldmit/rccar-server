# -*- mode: python -*-
#
# RC Car server code

import sys
from twisted.internet import reactor
from twisted.python import log

from RC import RCProtocol
from control import Joystick

log.startLogging(sys.stdout)

rcp = RCProtocol()
joy = Joystick()

def bin(s):
    return str(s) if s<=1 else bin(s>>1) + str(s&1)

def test():
    def cb(data):
        rcp.rssi_remote = ord(data[0])
        reactor.callLater(0, test)
    def eb(err):
        rcp.waiting = False
        #log.err(err)
        reactor.callLater(0, test)
    bitmask = 0
    if joy.get_throttle()[1] == "FORWARD":
        bitmask += 16
    if joy.get_throttle()[1] == "RELEASE":
        bitmask += 8
    if joy.get_turn() == "RELEASE":
        bitmask += 2
    if joy.get_turn() == "RIGHT":
        bitmask += 1
    if joy.get_camerapan()[1]:
        bitmask += 32
    if joy.get_camera():
        bitmask += 4
    frame = chr(bitmask) + chr(joy.get_throttle()[0]) + chr(joy.get_camerapan()[0])
    req = rcp.send_frame(frame)
    req.addCallbacks(cb, eb)

def statlog():
    log.msg("TX: %06d RX: %06d THROTTLE: %s TURN: %s RSSI: -%d OURRSSI: -%d" % (rcp.cnt_snt, rcp.cnt_rcv, joy.get_throttle()[1], joy.get_turn(), rcp.rssi_remote, rcp.rssi))
    #log.msg("THROTTLE: %4d %s TURN: %s CAMERA: %s %s" % (joy.get_throttle()[0], joy.get_throttle()[1], joy.get_turn(), bin(joy.get_camerapan()[0]), joy.get_camerapan()[1]))
    reactor.callLater(1, statlog)


reactor.callLater(0, test)
reactor.callLater(0, statlog)
reactor.run()
