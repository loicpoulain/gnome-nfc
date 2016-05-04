import os
import signal
import dbus

from neardutils import *
from pkg_resources import *

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify

NFCINDICATOR_ID = 'nfcindicator'

ICON_DISABLED = resource_filename(__name__, "icons/nfc-disabled.png")
ICON_ACTIVE = resource_filename(__name__, "icons/nfc-active.png")
ICON_DETECT = resource_filename(__name__, "icons/nfc-detect.png")

class NfcApplet(object):
	def __init__(self, adapter):
		self.adapter = adapter
		self.indicator = appindicator.Indicator.new(NFCINDICATOR_ID,
							    ICON_DISABLED,
							    appindicator.IndicatorCategory.SYSTEM_SERVICES)
		self.init()

	def init(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.indicator.set_menu(self.build_menu())
		notify.init(NFCINDICATOR_ID)
		self.update_adapter()

	def build_menu(self):
		menu = gtk.Menu()

		self.initiator = gtk.CheckMenuItem('Initiator')
		self.initiator.connect('activate', self.initiator_cb)
		self.initiator.set_draw_as_radio(True)
		menu.append(self.initiator)

		item_quit = gtk.MenuItem('Quit')
		item_quit.connect('activate', self.quit)
		menu.append(item_quit)

		menu.show_all()

		return menu

	def initiator_cb(self, check):
		if check.get_active():
			self.adapter.start_poll()
		else:
			self.adapter.stop_poll()

	def update(self, evt, arg):
		if (evt == EVT_CHG_ADAPTER):
			if (self.adapter == arg):
				self.update_adapter()

	def update_adapter(self):
		if self.adapter.is_polling():
			self.indicator.set_icon(ICON_ACTIVE)
		else:
			self.initiator.set_active(False)
			self.indicator.set_icon(ICON_DISABLED)

	def quit(self, _):
		self.adapter.tags[0].write_email('loic.poulain@gmail.com')
		notify.uninit()
		gtk.main_quit()

