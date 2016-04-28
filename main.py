import os
import signal
import dbus

from neardutils import *

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from dbus.mainloop.glib import DBusGMainLoop

NFCINDICATOR_ID = 'nfcindicator'


class NfcApplet(object):
	def __init__(self, adapter):
		self.adapter = adapter
		self.indicator = appindicator.Indicator.new(NFCINDICATOR_ID,
													os.path.abspath('icon.png'),
													appindicator.IndicatorCategory.SYSTEM_SERVICES)
		self.init()

	def init(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.indicator.set_menu(self.build_menu())
		notify.init(NFCINDICATOR_ID)
		self.update_adapter()

	def build_menu(self):
		menu = gtk.Menu()

		self.enable = gtk.CheckMenuItem('Polling')
		self.enable.connect("activate", self.cb_poll)
		menu.append(self.enable)
		
		item_settings = gtk.MenuItem('NFC Settings')
		item_settings.connect('activate', settings)
		menu.append(item_settings)

		item_quit = gtk.MenuItem('Quit')
		item_quit.connect('activate', quit)
		menu.append(item_quit)

		menu.show_all()

		return menu

	def cb_poll(self, check):
		if check.get_active():
			self.adapter.start_poll()
		else:
			self.adapter.stop_poll()

	def update(self, evt, arg):
		if (evt == EVT_CHG_ADAPTER):
			if (self.adapter == arg):
				self.update_adapter()
		if (evt == EVT_ADD_TAG):
			print 'NEW TAG'
		if (evt == EVT_DEL_TAG):
			print 'DEL TAG'

	def update_adapter(self):
		if self.adapter.get_mode() == 'Initiator':
			self.indicator.set_icon (os.path.abspath('icon-presence.png'))
			self.enable.set_active(False)
		elif self.adapter.is_polling():
			self.enable.set_active(True)
			self.indicator.set_icon (os.path.abspath('icon-active.png'))
		else:
			self.enable.set_active(False)
			self.indicator.set_icon (os.path.abspath('icon-nonactive.png'))

class NfcManager(object):
	def __init__(self):
		self.applet = None
		self.applet = NfcApplet(nfc(self.update).adapters[0])

	def update(self, evt, arg):
		if self.applet is not None:
			self.applet.update(evt, arg)

def main():
	mgmr = NfcManager()
	gtk.main()

def quit(_):
	print 'EXIT'
	notify.uninit()
	gtk.main_quit()

def icon_update():
	if a.is_polling():
		indicator.set_icon (os.path.abspath('icon-polling.png'))
	else:
		indicator.set_icon (os.path.abspath('icon.png'))
		


def settings(button):
	a.tags[0].write_email('loic.poulain@intel.com')

def enable_cb(check):
	if check.get_active() == True:
		a.start_poll()
	else:
		a.stop_poll()
	
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
