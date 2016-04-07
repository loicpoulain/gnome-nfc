import os
import signal
import dbus

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from dbus.mainloop.glib import DBusGMainLoop


NFCINDICATOR_ID = 'nfcindicator'

def main():
    global nf
    DBusGMainLoop(set_as_default=True)
    nf = NfcAdapter('/org/neard/nfc0')
    indicator = appindicator.Indicator.new(NFCINDICATOR_ID, os.path.abspath('icon.png'), appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(build_menu())
    notify.init(NFCINDICATOR_ID)
    gtk.main()
    

def build_menu():
    menu = gtk.Menu()

    enable = gtk.CheckMenuItem("Enable NFC")
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

def enable_nfc(_):
	#bus = dbus.SystemBus()
	#proxy = bus.get_object('org.freedesktop.NetworkManager',
	#		       '/org/freedesktop/NetworkManager/Devices/eth0')
	adapter_enable('/org/neard/nfc0')

def adapter_enable(path):
	a = NfcAdapter('/org/neard/nfc0')

	try:
		a.start_polling()
	except Exception, e:
			print(a.path + ': ' + str(e))


	#prop = adapter.GetProperties()[
	#print type(prop)
	#print prop['Polling']
	#print prop['Protocols']

def enable_cb(check):
	if check.get_active() == True:
		print 'enabling'
		try:
			nf.start_polling()
		except Exception, e:
			print str(e)
			check.set_active(False)
	else:
		print 'disabling'
		try:
			nf.stop_polling()
		except Exception, e:
			print str(e)

def test():
	print 'TOTO'
	
class NfcAdapter(object):
	def __init__(self, path):
		self.bus = dbus.SystemBus()
		self.adapter = dbus.Interface(self.bus.get_object('org.neard', path),
					      'org.neard.Adapter')
		self.adapter.connect_to_signal('PropertyChanged', self.signal_prop_changed)
		self.adapter.connect_to_signal('TagFound', self.signal_tag_found)
		self.adapter.connect_to_signal('TagLost', self.signal_tag_lost)
		self.tag = 0
	def start_polling(self):
		self.adapter.StartPollLoop('Initiator')

	def stop_polling(self):
		self.adapter.StopPollLoop()
	
	def signal_prop_changed(self, s, v):
		if s == 'Tags':
			if len(v) == 0:
				return
			self.tag = NfcTag(str(v[0]))
			#self.tag.write_uri('mailto:loic.poulain@gmail.com')

	def signal_tag_found(self, o):
		print 'FOUND'
	
	def signal_tag_lost(self, o):
		print 'LOST'

def print_dict(dict):
	for keys,values in dict.items():
		try:
			print str(keys) + ':' + str(values)
		except Exception, e:
			continue

class NfcTag(object):
	def __init__(self, path):
		self.bus = dbus.SystemBus()
		self.tag = dbus.Interface(self.bus.get_object('org.neard', path),
					  'org.neard.Tag')
		props = self.tag.GetProperties()
		print_dict(props)
		self.protocol = props['Protocol']
		self.readonly = props['ReadOnly']
		records = props['Records']
		if len(records) > 0:
			self.record = NfcRecord(records[0])

	def write(self, string):
		self.tag.Write({'URI': dbus.Variant('loic')})
	
	def write_uri(self, string):
		data = { }
		records = []
		data['Type'] = "URI"
		data['URI'] = string
		self.tag.Write(data)

class NfcRecord(object):
	def __init__(self, path):
		self.bus = dbus.SystemBus()
		self.tag = dbus.Interface(self.bus.get_object('org.neard', path),
					  'org.neard.Record')
		props = self.tag.GetProperties()
		print_dict(props)
		self.rtype = props['Type']
		#self.uri = props['URI']
		#print str(self.uri)
		
		
def adapter_start_polling(adapter):
	if adapter.GetProperties()['Polling'] == True:
		print 'Already Polling'
		return
	adapter.StartPollLoop()

def adapter_stop_polling(adapter):
	if adapter.GetProperties()['Polling'] == False:
		print 'Already Stopped'
		return
	adapter.StopPollLoop()

def adapter_set_power(adapter, enable):
	adapter.SetProperties('Powered', dbus.Boolean(True, 1))

def fetch_joke():
    joke = "TOTO"
    return joke

def settings(_):
    notify.Notification.new("<b>Joke</b>", fetch_joke(), None).show()

def quit(_):
    notify.uninit()
    gtk.main_quit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
