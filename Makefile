PREFIX = /usr/local

all:

installdeps:
	apt-get -y update
	apt-get -y install python3-requests python3-bs4 python3-gnupg

installprog:
	install -d $(PREFIX)/lib/flni/modules/
	install -d $(PREFIX)/share/flni/
	install -d $(PREFIX)/share/flni/doc/
	install -m 644 flni_functions.py $(PREFIX)/lib/flni/modules/
	install -m 644 flni_config.py $(PREFIX)/lib/flni/modules/
	install -m 755 update-firmware-nonfree $(PREFIX)/bin/
	install -m 644 readme.md $(PREFIX)/share/flni/doc/
	install -m 644 LICENSE $(PREFIX)/share/flni/doc/
	install -m 644 signing-key.asc $(PREFIX)/share/flni/

install: installdeps installprog
