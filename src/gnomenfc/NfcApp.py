import os
import signal

from neardutils import *
from NfcApplet import *

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from dbus.mainloop.glib import DBusGMainLoop

DEFAULT_ADAPTER = 'nfc0'

class NfcApp(object):
	def __init__(self, *args, **kwargs):
		self.applet = None

	def update(self, evt, arg):
		if evt == EVT_ADD_ADAPTER:
			if DEFAULT_ADAPTER in arg.path:
				self.applet = NfcApplet(arg)
		if evt == EVT_DEL_ADAPTER:
			if a.adapter == arg:
				print 'removing'
		if self.applet is not None:
			self.applet.update(evt, arg)

	def run(self):
		nfc = Nfc(self.update, debug=True)
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		gtk.main()
