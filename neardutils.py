import dbus

from dbus.mainloop.glib import DBusGMainLoop

SERVICE_NAME = "org.neard"
ADAPTER_INTERFACE = SERVICE_NAME + ".Adapter"
DEVICE_INTERFACE = SERVICE_NAME + ".Device"
TAG_INTERFACE = SERVICE_NAME + ".Tag"
RECORD_INTERFACE = SERVICE_NAME + ".Record"

DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

class Adapter(object):
	def __init__(self, path):
		print path
		self.path = path
		self.props = dbus.Interface(bus.get_object(SERVICE_NAME, path),
									"org.freedesktop.DBus.Properties")
		self.props.connect_to_signal("PropertiesChanged",
									 self.properties_changed)
		self.adapter = dbus.Interface(bus.get_object(SERVICE_NAME, path),
									  ADAPTER_INTERFACE)
		self.tag = 0
		self.update_tags()

	def properties_changed(self, interface, prop, prop_inv):
		print prop
		self.update_tags()

	def enabled(self):
		if self.props.Get(ADAPTER_INTERFACE, 'Powered') == dbus.Boolean(1):
			return True
		else:
			return False
	
	def enable(self):
		if self.enabled():
			return;
		self.props.Set(ADAPTER_INTERFACE, 'Powered', dbus.Boolean(1))

	def disable(self):
		if not self.enabled():
			return;
		self.props.Set(ADAPTER_INTERFACE, 'Powered', dbus.Boolean(0))
	
	def polling(self):
		self.enable()
		if self.props.Get(ADAPTER_INTERFACE, 'Polling') == dbus.Boolean(1):
			return True
		else:
			return False

	def start_poll(self):
		if self.polling():
			self.stop_poll()
		self.adapter.StartPollLoop('Initiator')

	def stop_poll(self):
		if not self.polling():
			return
		self.adapter.StopPollLoop()

	def update_tags(self):
		manager = dbus.Interface(bus.get_object(SERVICE_NAME, "/"),
								 "org.freedesktop.DBus.ObjectManager")
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if "org.neard.Tag" not in interfaces:
				continue
			self.tag = Tag(path)

	def __str__(self):
		s = self.path
		for keys,values in self.props.GetAll():
			try:
				s = s + '\n' + str(keys) + ':' + str(values)
			except Exception, e:
				s = s + '\n' + str(keys)
				continue

class Tag(object):
	def __init__(self, path):
		print path
		self.path = path
		self.props = dbus.Interface(bus.get_object(SERVICE_NAME, path),
									"org.freedesktop.DBus.Properties")
		self.props.connect_to_signal("PropertiesChanged",
									 self.properties_changed)
		self.tag = dbus.Interface(bus.get_object(SERVICE_NAME, path),
								  TAG_INTERFACE)
		self.type = self.props.Get(TAG_INTERFACE, 'Type')
		self.read_only = self.props.Get(TAG_INTERFACE, 'ReadOnly')
		self.protocol = self.props.Get(TAG_INTERFACE, 'Protocol')
		self.record = 0
		self.update_records()

	def properties_changed(self, interface, prop, prop_inv):
		self.update_records()

	def update_records(self):
		manager = dbus.Interface(bus.get_object(SERVICE_NAME, "/"),
								 "org.freedesktop.DBus.ObjectManager")
		for path, interfaces in manager.GetManagedObjects().iteritems():
			if self.path not in path:
				continue
			if "org.neard.Record" not in interfaces:
				continue
			self.record = Record(path)

	def __str__(self):
		s = path
		for keys,values in self.properties.items():
			try:
				s = s + '\n' + str(keys) + ':' + str(values)
			except Exception, e:
				s = s + '\n' + str(keys)
				continue
	

class Record(object):
	def __init__(self, path):
		print path
		self.path = path
		self.record = dbus.Interface(bus.get_object(SERVICE_NAME, path),
									 RECORD_INTERFACE)
	
	def update(self):
		self.properties = self.record.getProperties()
	
	def __str__(self):
		s = path
		for keys,values in self.properties.items():
			try:
				s = s + '\n' + str(keys) + ':' + str(values)
			except Exception, e:
				s = s + '\n' + str(keys)
				continue
	
