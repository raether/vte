#!/usr/bin/python

import logging
from kivy.uix.screenmanager import Screen
from kivy.base import stopTouchApp

logger = logging.getLogger('status')

class ShutdownScreen(Screen):
    
    def __init__(self, **kwargs):
        super(ShutdownScreen, self).__init__(**kwargs)

    def doShutdown(self):
        logger.info ("Shutting Down System...")
        stopTouchApp()

    pass
