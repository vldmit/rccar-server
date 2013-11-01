import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.internet import threads

import pygame
import pygame.joystick
import pygame.event

class Joystick(object):
    axis = [ 0, 0, 0, 0 ]
    button = [ False, ] * 16
    button_toggle = [ False, ] * 16

    def __init__(self):
        log.msg("Initializing pygame...")
        pygame.init()
        if pygame.joystick.get_count() < 1:
            log.err("No joysticks were found, exiting")
            sys.exit(100)

        self.joy = pygame.joystick.Joystick(0)
        self.joy.init()
        log.msg(u"Using joystick %s" % self.joy.get_name())
        reactor.callLater(0, self._loop)

    def _loop(self):
        def cb(event):
            if event.type == pygame.JOYBUTTONDOWN and event.button == 8:
                reactor.stop()
            if event.type == pygame.JOYAXISMOTION:
                self.axis[event.axis] = event.value
            if event.type == pygame.JOYBUTTONDOWN:
                self.button[event.button] = True
            if event.type == pygame.JOYBUTTONUP:
                self.button[event.button] = False
                self.button_toggle[event.button] = not self.button_toggle[event.button]
            reactor.callLater(0, self._loop)
        def eb(err):
            log.err(err)
        d = threads.deferToThread(pygame.event.wait)
        d.addCallbacks(cb, eb)

    def get_throttle(self):
        if abs(self.axis[1]) < 0.1:
            mode = "RELEASE"
        elif self.axis[1] < 0:
            mode = "FORWARD"
        else:
            mode = "BACKWARD"
        return (int(abs(self.axis[1]*255)), mode)

    def get_turn(self):
        if abs(self.axis[0]) < 0.5:
            mode = "RELEASE"
        elif self.axis[0] < 0:
            mode = "LEFT"
        else:
            mode = "RIGHT"
        return mode
    
    def get_camerapan(self):
        return (int((1 + self.axis[2]) * 127), self.button[5])

    def get_camera(self):
        return self.button_toggle[0]
    