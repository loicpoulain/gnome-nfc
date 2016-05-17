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
		self.path = '/org/neard'
		self.adapters = []
		self._debug = debug
		self._listeners = []
		self._init(listener)

	def _init(self, listener=None):
		if listener is not None:
			self._listeners.append(listener)
		self._populate_adapters()
		bus.add_signal_receiver(self._dbus_intf_added,
					bus_name=NEARD_BUS,
					dbus_interface=OBJMANAGER_INTERFACE,
					signal_name="InterfacesAdded")
		bus.add_signal_receiver(self._dbus_intf_removed,
					bus_name=NEARD_BUS,
					dbus_interface=OBJMANAGER_INTERFACE,
					signal_name="InterfacesRemoved")

	def _add_adapter(self, path):
		self._print_dbg('Adding Adapter ' + path)
		a = Adapter(path, self._notify, self._debug)
		self.adapters.append(a)
		self._notify(EVT_ADD_ADAPTER, a)

	def _remove_adapter(self, path):
		for a in self.adapters:
			if a.path == path:
				self._print_dbg('Removing Adapter ' + path)
				self.adapters.remove(a)
				self._notify(EVT_DEL_ADAPTER, a)

	def _populate_adapters(self):
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if ADAPTER_INTERFACE not in interfaces:
				continue
			self._add_adapter(path)

	def _dbus_intf_added(self, path, interfaces):
		for iface, props in interfaces.iteritems():
			if iface == ADAPTER_INTERFACE:
				self._add_adapter(path)
				continue
			for a in self.adapters:
				if a.path in path:
					a.dbus_intf_added(path, iface)
					continue

	def _dbus_intf_removed(self, path, interfaces):
		for iface in interfaces:
			if iface == ADAPTER_INTERFACE:
				self._remove_adapter(path)
				continue
			for a in self.adapters:
				if a.path in path:
					a.dbus_intf_removed(path, iface)
					continue

	def _print_dbg(self, msg):
		if self._debug:
			print '[N]' + self.path + ': ' + msg

	def _notify(self, evt, arg):
		for l in self._listeners:
			l(evt, arg)

	def register_change_listener(self, cb):
		self._listeners.append(cb)

class Adapter(object):
	def __init__(self, path, notifier=None, debug=False):
		self.path = path
		self.tags = []
		self._adapter = dbus.Interface(bus.get_object(NEARD_BUS, path),
					       ADAPTER_INTERFACE)
		self._props = dbus.Interface(bus.get_object(NEARD_BUS, path),
					     PROP_INTERFACE)
		self._listeners = []
		self._listeners.append(notifier)
		self._debug = debug
		self._init()

	def _init(self):
		self._props.connect_to_signal("PropertiesChanged",
					      self._dbus_props_changed)
		self._dbus_props_changed(ADAPTER_INTERFACE,
					 self._props.GetAll(ADAPTER_INTERFACE),
					 self._props.GetAll(ADAPTER_INTERFACE),
					 True)
		self._populate_tags()

	def _add_tag(self, path):
		self._print_dbg('Adding Tag ' + path)
		tag = Tag(path, self._notify, self._debug)
		self.tags.append(tag)
		self._notify(EVT_ADD_TAG, tag)

	def _remove_tag(self, path):
		for t in self.tags:
			if t.path == path:
				self._print_dbg('Removing Tag ' + path)
				self.tags.remove(t)
				self._notify(EVT_DEL_TAG, t)

	def _populate_tags(self):
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if TAG_INTERFACE not in interfaces:
				continue
			self._add_tag(path)

	def _print_dbg(self, msg):
		if self._debug:
			print '[A]' + self.path + ': ' + msg

	def _notify(self, evt, arg):
		for l in self._listeners:
			l(evt, arg)

	def _dbus_props_changed(self, iface, changed, invalided, silent=False):
		for name, val in changed.iteritems():
			self._print_dbg(name + ' = ' + str(val))
		if not silent:
			self._notify(EVT_CHG_ADAPTER, self)

	def dbus_intf_added(self, path, iface):
		if iface == TAG_INTERFACE:
			self._add_tag(path)
			return True
		for t in self.tags:
			if t.path in path:
				return t.dbus_intf_added(path, iface)
		return False
		
	def dbus_intf_removed(self, path, iface):
		if iface == TAG_INTERFACE:
			self._remove_tag(path)
			return True
		for t in self.tags:
			if t.path in path:
				return t.dbus_intf_removed(path, iface)
		return False

	def register_listener(self, notifier):
		self._listeners.append(notifier)

	def unregister_listener(self, notifier):
		self._listeners.remove(notifier)

	def is_polling(self):
		if self._props.Get(ADAPTER_INTERFACE, 'Polling') == dbus.Boolean(1):
			return True
		return False

	def is_powered(self):
		if self._props.Get(ADAPTER_INTERFACE, 'Powered') == dbus.Boolean(1):
			return True
		return False

	def get_protos(self):
		return self._props.Get(ADAPTER_INTERFACE, 'Protocols')

	def start_poll(self):
		if not self.is_powered():
			self.power_on()
		if self.is_polling():
			self.stop_poll()
		self._print_dbg('Starting poll')
		self._adapter.StartPollLoop('Initiator')

	def stop_poll(self):
		if not self.is_polling():
			return
		self._print_dbg('Stopping poll')
		self._adapter.StopPollLoop()

	def power_on(self):
		if self.is_powered():
			return;
		self._props.Set(ADAPTER_INTERFACE, 'Powered', dbus.Boolean(1))
	
	def power_off(self):
		if not self.is_powered():
			return;
		self._props.Set(ADAPTER_INTERFACE, 'Powered', dbus.Boolean(0))

	def get_mode(self):
		return self._props.Get(ADAPTER_INTERFACE, 'Mode')

	def get_properties(self):
		return self._props.GetAll(ADAPTER_INTERFACE)
		
class Tag(object):
	def __init__(self, path, notifier=None, debug=False):
		self.path = path
		self._debug = debug
		self.records = []
		self._tag = dbus.Interface(bus.get_object(NEARD_BUS, path),
					   TAG_INTERFACE)
		self._props = dbus.Interface(bus.get_object(NEARD_BUS, path),
					     PROP_INTERFACE)
		self._notifier = notifier
		self._init()

	def _init(self):
		self._props.connect_to_signal("PropertiesChanged",
					      self._dbus_props_changed)
		self._dbus_props_changed(TAG_INTERFACE,
					 self._props.GetAll(TAG_INTERFACE),
					 self._props.GetAll(TAG_INTERFACE), True)
		self._populate_records()

	def _add_record(self, path):
		self._print_dbg('Adding Record ' + path)
		record = Record(path, self._notifier, self._debug)
		self.records.append(record)
		if self._notifier is not None:
			self._notifier(EVT_ADD_RECORD, record)

	def _remove_record(self, path):
		for r in self.records:
			if r.path == path:
				self._print_dbg('Removing Record ' + path)
				self.records.remove(r)
				if self._notifier is not None:
					self._notifier(EVT_DEL_RECORD, r)

	def _dbus_props_changed(self, iface, changed, invalided, silent=False):
		for name, val in changed.iteritems():
			self._print_dbg(name + ' = ' + str(val))
		if self._notifier is not None and not silent:
			self._notifier(EVT_CHG_TAG, self)

	def _print_dbg(self, msg):
		if self._debug:
			print '[T]' + self.path + ': ' + msg

	def _populate_records(self):
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if RECORD_INTERFACE not in interfaces:
				continue
			self._add_record(path)

	def dbus_intf_added(self, path, iface):
		if iface == RECORD_INTERFACE:
			self._add_record(path)
			return True
		return False
		
	def dbus_intf_removed(self, path, iface):
		if iface == RECORD_INTERFACE:
			self._remove_record(path)
			return True
		return False

	def get_properties(self):
		return self._props.GetAll(TAG_INTERFACE)

	def write_uri(self, URI, prefix=None):
		if prefix is not None:
			URI = prefix + ':' + URI
		self.tag.Write(({'Type' : 'URI', 'URI' : URI}))

	def write_email(self, email):
		self.write_uri(email, 'mailto')

class Record(object):
	def __init__(self, path, notifier=None, debug=False):
		self.path = path
		self._debug = debug
		self._record = dbus.Interface(bus.get_object(NEARD_BUS, path),
					      RECORD_INTERFACE)
		self._props = dbus.Interface(bus.get_object(NEARD_BUS, path),
					     PROP_INTERFACE)
		self._notifier = notifier
		self._init()
	
	def _init(self):
		self._props.connect_to_signal("PropertiesChanged",
					      self._dbus_props_changed)
		self._dbus_props_changed(RECORD_INTERFACE,
					 self._props.GetAll(RECORD_INTERFACE),
					 self._props.GetAll(RECORD_INTERFACE),
					 True)

	def _dbus_props_changed(self, iface, changed, invalided, silent=False):
		for name, val in changed.iteritems():
			try:
				self._print_dbg(name + ' = ' + str(val))
			except UnicodeEncodeError, e:
				self._print_dbg(name + ' NOT ASCII')
		if self._notifier is not None and not silent:
			self._notifier(EVT_CHG_RECORD, self)

	def _print_dbg(self, msg):
		if self._debug:
			print '[R]' + self.path + ': ' + msg

	def get_properties(self):
		return self._props.GetAll(RECORD_INTERFACE)
	
