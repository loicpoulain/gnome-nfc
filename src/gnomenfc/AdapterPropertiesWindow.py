import dbus
from gi.repository import Gtk, Gdk

class AdapterPropertiesWindow(object):
	def __init__(self, adapter):
		self.adapter = adapter
		self.window = Gtk.Window()
		self.window.show()
		self.update()

	def update(self):
		self.window.set_title(self.adapter.path)

# TODO: FIX this ugly code
		props = self.adapter.get_properties()
		table = Gtk.Table(rows=10, columns=10, homogeneous=False)
		i = 0
		for name, val in props.iteritems():
			if type(val) == dbus.Array:
				valstr = ''
				for n in val:
					valstr = valstr + str(n) + ', '
				text_val = Gtk.Label(str(valstr))
			else:
				text_val = Gtk.Label(str(val))
			text_val.show()

			text_name = Gtk.Label(str(name) + ': ')
			text_name.show()

			table.attach(text_name, 0, 1, i, i + 1)
			table.attach(text_val, 1, 2, i, i + 1)
			i = i + 1
		table.show()
		self.window.add(table)


		
		

