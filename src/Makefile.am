SUBDIRS = gnomenfc

bin_SCRIPTS = gnome-nfc
CLEANFILES = $(bin_SCRIPTS)
EXTRA_DIST = gnome-nfc.in

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' 

gnome-nfc: gnome-nfc.in Makefile
	$(do_substitution) < $(srcdir)/gnome-nfc.in > gnome-nfc
	chmod +x gnome-nfc
