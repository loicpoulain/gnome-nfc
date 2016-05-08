icons = nfc-active.png \
	nfc-disabled.png \
	nfc-detect.png

EXTRA_DIST = $(icons)

install-data-local:
	mkdir -p $(pythondir)/gnomenfc/icons; \
	for i in $(icons); do \
		$(INSTALL_DATA) $(srcdir)/$$i $(pythondir)/gnomenfc/icons/; \
	done

