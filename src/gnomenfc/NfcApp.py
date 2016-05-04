import os
import signal

from neardutils import *
from NfcApplet import *

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from dbus.mainloop.glib import DBusGMainLoop

class NfcApp(object):
	def __init__(self, *args, **kwargs):
		self.applet = None

	def update(self, evt, arg):
		if self.applet is not None:
			self.applet.update(evt, arg)

	def run(self):
		self.applet = NfcApplet(Nfc(self.update).adapters[0])
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		gtk.main()
