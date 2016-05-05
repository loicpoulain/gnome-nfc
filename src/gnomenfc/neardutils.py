import dbus

from dbus.mainloop.glib import DBusGMainLoop

NEARD_BUS = "org.neard"
ADAPTER_INTERFACE = NEARD_BUS + ".Adapter"
DEVICE_INTERFACE = NEARD_BUS + ".Device"
TAG_INTERFACE = NEARD_BUS + ".Tag"
RECORD_INTERFACE = NEARD_BUS + ".Record"
OBJMANAGER_INTERFACE = "org.freedesktop.DBus.ObjectManager"
PROP_INTERFACE = "org.freedesktop.DBus.Properties"
 
MODE_IDLE =	0
MODE_INITIATOR =	1
MODE_TARGET	=	2
MODE_DUAL =	3
MODE_INVALID =	4

DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
manager = dbus.Interface(bus.get_object(NEARD_BUS, "/"),
			"org.freedesktop.DBus.ObjectManager")

EVT_ADD_ADAPTER	= 0x01
EVT_DEL_ADAPTER	= 0x02
EVT_CHG_ADAPTER = 0x03
EVT_ADD_TAG	= 0x04
EVT_DEL_TAG	= 0x05
EVT_CHG_TAG	= 0x06
EVT_ADD_RECORD	= 0x07
EVT_DEL_RECORD	= 0x08
EVT_CHG_RECORD	= 0x09

class Nfc(object):
	def __init__(self, listener=None, debug=False):
		self.debug = debug
		self.path = '/org/neard'
		self.adapters = []
		self.listeners = []
		self.init(listener)

	def init(self, listener=None):
		if listener is not None:
			self.listeners.append(listener)
		self.populate_adapters()
		bus.add_signal_receiver(self.dbus_intf_added,
					bus_name=NEARD_BUS,
					dbus_interface=OBJMANAGER_INTERFACE,
					signal_name="InterfacesAdded")
		bus.add_signal_receiver(self.dbus_intf_removed,
					bus_name=NEARD_BUS,
					dbus_interface=OBJMANAGER_INTERFACE,
					signal_name="InterfacesRemoved")

	def add_adapter(self, path):
		self.print_dbg('Adding Adapter ' + path)
		a = Adapter(path, self.notify, self.debug)
		self.adapters.append(a)
		self.notify(EVT_ADD_ADAPTER, a)

	def remove_adapter(self, path):
		for a in self.adapters:
			if a.path == path:
				self.print_dbg('Removing Adapter ' + path)
				self.adapters.remove(a)
				self.notify(EVT_DEL_ADAPTER, a)

	def populate_adapters(self):
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if ADAPTER_INTERFACE not in interfaces:
				continue
			self.add_adapter(path)

	def dbus_intf_added(self, path, interfaces):
		for iface, props in interfaces.iteritems():
			if iface == ADAPTER_INTERFACE:
				self.add_adapter(path)
				continue
			for a in self.adapters:
				if a.path in path:
					a.dbus_intf_added(path, iface)
					continue

	def dbus_intf_removed(self, path, interfaces):
		for iface in interfaces:
			if iface == ADAPTER_INTERFACE:
				self.remove_adapter(path)
				continue
			for a in self.adapters:
				if a.path in path:
					a.dbus_intf_removed(path, iface)
					continue

	def register_change_listener(self, cb):
		self.listeners.append(cb)
		
	def print_dbg(self, msg):
		if self.debug:
			print '[N]' + self.path + ': ' + msg

	def notify(self, evt, arg):
		for l in self.listeners:
			l(evt, arg)

class Adapter(object):
	def __init__(self, path, notifier=None, debug=False):
		self.path = path
		self.debug = debug
		self.tags = []
		self.adapter = dbus.Interface(bus.get_object(NEARD_BUS, path),
					      ADAPTER_INTERFACE)
		self.props = dbus.Interface(bus.get_object(NEARD_BUS, path),
					    PROP_INTERFACE)
		self.props.connect_to_signal("PropertiesChanged",
					     self.dbus_props_changed)
		self.notifier = notifier
		self.init()

	def init(self):
		self.dbus_props_changed(ADAPTER_INTERFACE,
					self.props.GetAll(ADAPTER_INTERFACE),
					self.props.GetAll(ADAPTER_INTERFACE),
					True)
		self.populate_tags()

	def add_tag(self, path):
		self.print_dbg('Adding Tag ' + path)
		tag = Tag(path, self.notifier, self.debug)
		self.tags.append(tag)
		if self.notifier is not None:
			self.notifier(EVT_ADD_TAG, tag)

	def remove_tag(self, path):
		for t in self.tags:
			if t.path == path:
				self.print_dbg('Removing Tag ' + path)
				self.tags.remove(t)
				if self.notifier is not None:
					self.notifier(EVT_DEL_TAG, t)

	def populate_tags(self):
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if TAG_INTERFACE not in interfaces:
				continue
			self.add_tag(path)

	def dbus_intf_added(self, path, iface):
		if iface == TAG_INTERFACE:
			self.add_tag(path)
			return True
		for t in self.tags:
			if t.path in path:
				return t.dbus_intf_added(path, iface)
		return False
		
	def dbus_intf_removed(self, path, iface):
		if iface == TAG_INTERFACE:
			self.remove_tag(path)
			return True
		for t in self.tags:
			if t.path in path:
				return t.dbus_intf_removed(path, iface)
		return False

	def dbus_props_changed(self, iface, changed, invalided, silent=False):
		for name, val in changed.iteritems():
			self.print_dbg(name + ' = ' + str(val))
		if self.notifier is not None and not silent:
			self.notifier(EVT_CHG_ADAPTER, self)

	def is_polling(self):
		if self.props.Get(ADAPTER_INTERFACE, 'Polling') == dbus.Boolean(1):
			return True
		return False

	def is_powered(self):
		if self.props.Get(ADAPTER_INTERFACE, 'Powered') == dbus.Boolean(1):
			return True
		return False

	def start_poll(self):
		if not self.is_powered():
			self.power_on()
		if self.is_polling():
			self.stop_poll()
		self.print_dbg('Starting poll')
		self.adapter.StartPollLoop('Initiator')

	def stop_poll(self):
		if not self.is_polling():
			return
		self.print_dbg('Stopping poll')
		self.adapter.StopPollLoop()

	def power_on(self):
		if self.is_powered():
			return;
		self.props.Set(ADAPTER_INTERFACE, 'Powered', dbus.Boolean(1))
	
	def power_off(self):
		if not self.is_powered():
			return;
		self.props.Set(ADAPTER_INTERFACE, 'Powered', dbus.Boolean(0))

	def get_mode(self):
		return self.props.Get(ADAPTER_INTERFACE, 'Mode')

	def print_dbg(self, msg):
		if self.debug:
			print '[A]' + self.path + ': ' + msg
		
class Tag(object):
	def __init__(self, path, notifier=None, debug=False):
		self.path = path
		self.debug = debug
		self.records = []
		self.tag = dbus.Interface(bus.get_object(NEARD_BUS, path),
					 TAG_INTERFACE)
		self.props = dbus.Interface(bus.get_object(NEARD_BUS, path),
					    PROP_INTERFACE)
		self.props.connect_to_signal("PropertiesChanged",
					     self.dbus_props_changed)
		self.notifier = notifier
		self.init()

	def init(self):
		self.dbus_props_changed(TAG_INTERFACE,
					self.props.GetAll(TAG_INTERFACE),
					self.props.GetAll(TAG_INTERFACE), True)
		self.populate_records()

	def add_record(self, path):
		self.print_dbg('Adding Record ' + path)
		record = Record(path, self.notifier, self.debug)
		self.records.append(record)
		if self.notifier is not None:
			self.notifier(EVT_ADD_RECORD, record)

	def remove_record(self, path):
		for r in self.records:
			if r.path == path:
				self.print_dbg('Removing Record ' + path)
				self.records.remove(r)
				if self.notifier is not None:
					self.notifier(EVT_DEL_RECORD, r)
	
	def populate_records(self):
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if RECORD_INTERFACE not in interfaces:
				continue
			self.add_record(path)

	def dbus_intf_added(self, path, iface):
		if iface == RECORD_INTERFACE:
			self.add_record(path)
			return True
		return False
		
	def dbus_intf_removed(self, path, iface):
		if iface == RECORD_INTERFACE:
			self.remove_record(path)
			return True
		return False

	def dbus_props_changed(self, iface, changed, invalided, silent=False):
		for name, val in changed.iteritems():
			self.print_dbg(name + ' = ' + str(val))
		if self.notifier is not None and not silent:
			self.notifier(EVT_CHG_TAG, self)

	def print_dbg(self, msg):
		if self.debug:
			print '[T]' + self.path + ': ' + msg

	def write_uri(self, URI, prefix=None):
		if prefix is not None:
			URI = prefix + ':' + URI
		self.tag.Write(({'Type' : 'URI', 'URI' : URI}))

	def write_email(self, email):
		self.write_uri(email, 'mailto')

class Record(object):
	def __init__(self, path, notifier=None, debug=False):
		self.path = path
		self.debug = debug
		self.record = dbus.Interface(bus.get_object(NEARD_BUS, path),
					     RECORD_INTERFACE)
		self.props = dbus.Interface(bus.get_object(NEARD_BUS, path),
					    PROP_INTERFACE)
		self.props.connect_to_signal("PropertiesChanged",
					     self.dbus_props_changed)
		self.notifier = notifier
		self.init()
	
	def init(self):
		self.dbus_props_changed(RECORD_INTERFACE,
					self.props.GetAll(RECORD_INTERFACE),
					self.props.GetAll(RECORD_INTERFACE),
					True)

	def dbus_props_changed(self, iface, changed, invalided, silent=False):
		for name, val in changed.iteritems():
			self.print_dbg(name + ' = ' + str(val))
		if self.notifier is not None and not silent:
			self.notifier(EVT_CHG_RECORD, self)

	def print_dbg(self, msg):
		if self.debug:
			print '[R]' + self.path + ': ' + msg
	
