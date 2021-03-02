# FLNI

This is the firmware-linux-nonfree installer. It scrapes [kernel.org's linux-firmware repository](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git) for the newest tag, 
downloads and verifies the linked archive, then uses the included script to install the firmware files.

Binary firmware is a pain, but a necessary evil for driver support for linux on most modern hardware, particularly commonplace amd64 desktops and laptops.

To install: download flni-main.zip from the Code button above, unpack, and run `make install`

To use: run `update-firmware-nonfree`

Developed for, and tested on, Debian 10 (buster); will probably work unmodified on any debian derivative.

Coming soon: command line switches! better documentation! big-screen license warnings! surround sound! Ok, maybe not the last one. 
