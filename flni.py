#######################################################################
# This file is part of flni.
#
# Copyright (C) 2021 by Jesse Rhodes.
#
# flni is distributed under the MIT license.  See the file
# LICENSE for distribution details.
#######################################################################

"""This is the flni functions module.

See readme.md for more information.
"""

__version__ = "0.1"
__author__ = "Jesse Rhodes"
__copyright__ = "Copyright 2021, Jesse Rhodes"
__license__ = "MIT"

import shutil
import os
import re
import gzip
import subprocess

import requests
import tarfile
import tempfile
import bs4
import gnupg

import config

def get_latest_firmware():
	# Scrape webpage for latest tag.
	source = requests.get(config.tagurl)
	tags = source.text
#	tags = open("tags.html", "r")

	soup = bs4.BeautifulSoup(tags, 'html.parser')

	firmware_dates = soup.find_all(string=re.compile("^[0-9]{8}$"))
	firmware_dates.sort() # The latest will probably always be the top entry, but it costs nothing to make sure
	firmware_latest = firmware_dates[-1]
	print("Latest firmware is " + firmware_latest)
	return firmware_latest

def download(tgz, tb, sg):
	# Download gzipped tarball and signature.

	print("Downloading latest firmware archive from git.kernel.org. This file may be >200MB, please be patient.")	# TODO: Progress bar? Spinner?

	tarball_url = config.snapshoturl + tgz

	r = requests.get(tarball_url, stream=True)

	with open(tgz, 'wb') as fd:
		for chunk in r.iter_content(chunk_size=128):
			fd.write(chunk)

	print("Decompressing firmware archive.")

	with gzip.open(tgz, "rb") as f_in:
		with open(tb, "wb") as f_out:
			shutil.copyfileobj(f_in, f_out)

	print("Downloading latest firmware signature from git.kernel.org.")

	signature_url = config.snapshoturl + sg

	r = requests.get(signature_url, stream=True)

	with open(sg, 'wb') as fd:
		for chunk in r.iter_content(chunk_size=128):
			fd.write(chunk)

def verify(tb, sg, tf):
	# Check if a) download was successful and b) signature is verified

	if os.path.exists(tb):
		tb_is_tb = tarfile.is_tarfile(tb)
		print("Valid archive detected, continuing")
	else:
		cleanup(tf)
		exit("Download failed, please try again.")

	if os.path.exists(sg):
		print("Signature file present, continuing")
	else:
		cleanup(tf)
		exit("Download failed, please try again.")

	# Use our temp dir from setup() for a gnupg environment for signature verification
	temp_home = os.path.join(tf, "gpg")

	if not os.path.exists(temp_home):
		os.makedirs(temp_home)

	gpg = gnupg.GPG(gnupghome=temp_home)

	upstream_key = open(config.signing_key, "r")
	import_result = gpg.import_keys(upstream_key.read())
	archive_sig = open(sg, "rb")


	verified = gpg.verify_file(archive_sig, tb)
	if verified:
		print("Good signature, continuing")
	else:
		cleanup(tf)
		exit("BAD signature, exiting.")


def check_installed(fl, tf):

	if os.path.exists(config.fpi_log):
		fpi_content = open(config.fpi_log, "r")
		firmware_installed = fpi_content.read()
		if firmware_installed.rstrip() == fl:
			cleanup(tf)
			exit("Latest firmware already on this system. If this is in error, remove " + config.fpi_log + " and retry.")
		else:
			print("Previous firmware on this system: " + firmware_installed + "Upgrading to " + firmware_latest)
	else:
		print("Previous installation not found. Proceeding with install. WARNING: Manually installed firmware blobs may be overwritten.")


def install(tb, fl, tf):
	# Use our temp directory from setup() to unpack tarball
	temp_extract = os.path.join(tf, "extract")

	if not os.path.exists(temp_extract):
		os.makedirs(temp_extract)

	tar = tarfile.open(tb, "r")
	pre = os.path.commonprefix(tar.getnames())
	wdir = os.path.join(temp_extract,pre)

	print("Unpacking " + pre )
	tar.extractall(path=temp_extract)

	os.chdir(wdir)

	install_files = subprocess.run(["./copy-firmware.sh", "-v", config.firmwaredir]) # Roll that beautiful scrolling output footage

	if install_files.returncode == 0:
		print("Successfully installed " + pre + " to " + config.firmwaredir + ". You may want to update your initramfs.")
	else:
		cleanup(tf)
		exit("Something went wrong. Please ensure that we are running as root and that " + config.install_prefix + config.firmwaredir + " is writable.")

	# Install licenses
	if not os.path.exists(config.licensedir):
		os.makedirs(config.licensedir)

	for files in os.listdir(wdir):
		if files.startswith("LICENCE") or files.startswith("LICENCE") or files == "WHENCE": # You'd think they could agree on 1 spelling for this
			shutil.copy(files,config.licensedir)

	# Log installed version
	f = open(config.fpi_log, "w")
	f.write(fl)
	f.close()


def setup():
	temp_flni = tempfile.mkdtemp()
	os.chdir(temp_flni)
	return temp_flni



def cleanup(tf):
	print("Cleaning up temporary files.")
	if os.path.exists(tf):
		shutil.rmtree(tf)