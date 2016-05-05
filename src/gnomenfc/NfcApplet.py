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
		self.notifier = None
		self.menu = None
		self.init()

	def init(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.indicator.set_menu(self.build_menu())
		notify.init(NFCINDICATOR_ID)
		self.update_adapter()

	def build_menu(self):
		self.menu = gtk.Menu()

		self.initiator = gtk.CheckMenuItem('Initiator')
		self.initiator.connect('activate', self.initiator_cb)
		self.initiator.set_draw_as_radio(True)
		self.menu.append(self.initiator)

		item_quit = gtk.MenuItem('Quit')
		item_quit.connect('activate', self.quit)
		self.menu.append(item_quit)

		self.menu.show_all()

		return self.menu

	def initiator_cb(self, check):
		if check.get_active():
			self.adapter.start_poll()
		else:
			self.adapter.stop_poll()

	def update(self, evt, arg):
		if (evt == EVT_CHG_ADAPTER):
			if (self.adapter == arg):
				self.update_adapter()
		if (evt == EVT_ADD_TAG):
			self.notifyEvent('TAG Detected ' + os.path.basename(arg.path))
			self.add_tag(arg)
		if (evt == EVT_DEL_TAG):
			self.notifyEvent('TAG Removed ' + os.path.basename(arg.path))
			self.remove_tag(arg)

	def update_adapter(self):
		if self.adapter.is_polling():
			self.indicator.set_icon(ICON_ACTIVE)
		else:
			self.initiator.set_active(False)
			self.indicator.set_icon(ICON_DISABLED)

	def notifyEvent(self, txt):
		if self.notifier is None:
			self.notifier = notify.Notification.new(txt)
			self.notifier.set_timeout(2000)
		else:
			self.notifier.update(txt)
		self.notifier.show()

	def add_tag(self, tag):
		tag = gtk.MenuItem(os.path.basename(tag.path))
		self.menu.append(tag)
		self.menu.show_all()

	def remove_tag(self, tag):
		for c in self.menu.get_children():
			if c.get_label() in tag.path:
				self.menu.remove(c)

	def quit(self, _):
		self.adapter.stop_poll()
		self.adapter.power_off()
		notify.uninit()
		gtk.main_quit()

