import dbus
import os
from gi.repository import Gtk, Gdk
from pkg_resources import *

SETTINGS_UI = resource_filename(__name__, "settings.ui")

class AdapterPropertiesWindow(object):
	def __init__(self, adapter):
		self.adapter = adapter
		self._window = None
		self._label_proto = None
		self._create_window()
		self._update(None, None)
		self.adapter.register_listener(self._update)

	def _create_window(self):
		self._window = Gtk.Window()
		self._window.set_border_width(10)
		self._window.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
		self._window.set_title(os.path.basename(self.adapter.path))
		self._window.show()

		builder = Gtk.Builder()
		builder.add_from_file(SETTINGS_UI)
		self._label_proto = builder.get_object("label_protocols")
		self._switch_nfc = builder.get_object("switch_nfc")
		self._switch_nfc.connect('notify::active', self._switch_nfc_cb)
		self._spin_polling = builder.get_object("spin_polling")
		self._check_initiator = builder.get_object("check_initiator")
		self._check_initiator.connect('notify::active', self._check_cb)
		self._check_target = builder.get_object("check_target")
		self._check_target.connect('notify::active', self._check_cb)

		treeview_tag = builder.get_object("treeview_tag")
		self._list_tag = Gtk.ListStore(str, str, str, str)
		treeview_tag.set_model(self._list_tag)
		column = Gtk.TreeViewColumn('Tag', Gtk.CellRendererText(), text=0)
		treeview_tag.append_column(column)
		column = Gtk.TreeViewColumn('Protocol', Gtk.CellRendererText(), text=1)
		treeview_tag.append_column(column)
		column = Gtk.TreeViewColumn('Type', Gtk.CellRendererText(), text=2)
		treeview_tag.append_column(column)
		column = Gtk.TreeViewColumn('ReadOnly', Gtk.CellRendererText(), text=3)
		treeview_tag.append_column(column)

		box = builder.get_object("box_properties")
		box.show()
		self._window.add(box)

	def _switch_nfc_cb(self, switch, active):
		if switch.get_active():
			self.adapter.power_on()
		else:
			self.adapter.power_off()

	def _check_cb(self, check, active):
		if self._updating:
			return
		if self._check_initiator.get_active() and self._check_target.get_active():
			self.adapter.start_poll(mode='Both')
		elif self._check_initiator.get_active():
			self.adapter.start_poll(mode='Initiator')
		elif self._check_target.get_active():
			self.adapter.start_poll(mode='Target')
		else:
			self.adapter.stop_poll()

	def _update(self, evt, arg):
		self._updating = True
		str_protos = ''
		for n in self.adapter.get_protos():
			str_protos = str_protos + str(n) + ' '
		self._label_proto.set_text(str_protos)

		if self.adapter.is_powered():
			self._switch_nfc.set_active(True)
			self._check_initiator.set_sensitive(True)
			self._check_target.set_sensitive(True)
		else:
			self._switch_nfc.set_active(False)
			self._check_initiator.set_sensitive(False)
			self._check_target.set_sensitive(False)

		mode = self.adapter.get_polling_mode()
		self._check_initiator.set_active(mode is 'Initiator' or mode is 'Both')
		self._check_target.set_active(mode is 'Target' or mode is 'Both')

		self._spin_polling.set_visible(self.adapter.is_polling())

		self._list_tag.clear()
		for t in self.adapter.tags:
			self._list_tag.append([os.path.basename(t.path),
					       t.get_protocol(),
					       t.get_type(),
					       str(t.is_read_only())
					      ])

		self._updating = False
