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
	def update(self):
		update()

def main():
	global a, indicator
	a = nfc(NfcApplet()).adapters[0]
	indicator = appindicator.Indicator.new(NFCINDICATOR_ID, os.path.abspath('icon.png'), appindicator.IndicatorCategory.SYSTEM_SERVICES)
	indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
	indicator.set_menu(build_menu())
	notify.init(NFCINDICATOR_ID)
	gtk.main()

def update():
	icon_update()

def quit(_):
	print 'EXIT'
	notify.uninit()
	gtk.main_quit()

def icon_update():
	if a.is_polling():
		indicator.set_icon (os.path.abspath('icon-polling.png'))
	else:
		indicator.set_icon (os.path.abspath('icon.png'))
		
def build_menu():
    menu = gtk.Menu()

    enable = gtk.CheckMenuItem('Polling')
    enable.set_active(True)
    enable.connect("activate", enable_cb)
    menu.append(enable)
    
    item_settings = gtk.MenuItem('NFC Settings')
    item_settings.connect('activate', settings)
    menu.append(item_settings)

    item_quit = gtk.MenuItem('Quit')
    item_quit.connect('activate', quit)
    menu.append(item_quit)

    menu.show_all()

    return menu

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
