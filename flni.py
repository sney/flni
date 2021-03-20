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

    soup = bs4.BeautifulSoup(tags, "html.parser")

    firmware_dates = soup.find_all(string=re.compile("^[0-9]{8}$"))
    firmware_dates.sort()  # The latest will probably always be the top entry, but it costs nothing to make sure
    firmware_latest = firmware_dates[-1]
    print("Latest firmware is " + firmware_latest)
    return firmware_latest


def download(tgz, tb, sg):
    # Download gzipped tarball and signature.

    print(
        "Downloading latest firmware archive from git.kernel.org. This file may be >200MB, please be patient."
    )  # TODO: Progress bar? Spinner?

    tarball_url = config.snapshoturl + tgz

    r = requests.get(tarball_url, stream=True)

    with open(tgz, "wb") as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

    print("Decompressing firmware archive.")

    with gzip.open(tgz, "rb") as f_in:
        with open(tb, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    print("Downloading latest firmware signature from git.kernel.org.")

    signature_url = config.snapshoturl + sg

    r = requests.get(signature_url, stream=True)

    with open(sg, "wb") as fd:
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

    try:
        gpg.verify_file(archive_sig, tb)
    except:
        cleanup(tf)
        exit("BAD signature, exiting.")
    else:
        print("Good signature, continuing")


def check_installed(fl, tf):

    if os.path.exists(config.fpi_log):
        fpi_content = open(config.fpi_log, "r")
        firmware_installed = fpi_content.read()
        if firmware_installed.rstrip() == fl:
            cleanup(tf)
            exit(
                "Latest firmware already on this system. If this is in error, remove "
                + config.fpi_log
                + " and retry."
            )
        else:
            print(
                "Previous firmware on this system: "
                + firmware_installed
                + "\n Upgrading to "
                + fl
            )
    else:
        print(
            "Previous installation not found. Proceeding with install. WARNING: Manually installed firmware blobs may be overwritten."
        )


def install(tb, fl, tf):
    # Use our temp directory from setup() to unpack tarball
    temp_extract = os.path.join(tf, "extract")

    if not os.path.exists(temp_extract):
        os.makedirs(temp_extract)

    tar = tarfile.open(tb, "r")
    pre = os.path.commonprefix(tar.getnames())
    wdir = os.path.join(temp_extract, pre)

    print("Unpacking " + pre)
    tar.extractall(path=temp_extract)

    os.chdir(wdir)

    try:
        subprocess.run(
            ["./copy-firmware.sh", "-v", config.firmwaredir]
        )  # Roll that beautiful scrolling output footage
    except:
        cleanup(tf)
        print(
            "Something went wrong. Please ensure that we are running as root and that "
            + config.firmwaredir
            + " is writable."
        )
    else:
        print(
            "Successfully installed "
            + pre
            + " to "
            + config.firmwaredir
            + ". You may want to update your initramfs."
        )

    # Log installed files
    filelist = []

    with open("WHENCE", "r") as f:
        for strings in f:
            if (
                strings.startswith("File:")
            ):
                f1 = strings.replace("File:", "")
                f2 = f1.replace('"', '')
                f3 = f2.lstrip()
                filelist.append(f3)

    with open(config.files_log, "w") as g:
        for names in filelist:
            if os.path.exists(os.path.join(config.firmwaredir, names.strip())):
                g.write(names)



    # Install licenses
    if not os.path.exists(config.licensedir):
        os.makedirs(config.licensedir)

    print(
        "Installing firmware licenses to "
        + config.licensedir
        + "."
    )

    for files in os.listdir(wdir):
        if (
            files.startswith("LICENCE")
            or files.startswith("LICENCE")
            or files == "WHENCE"
        ):  # You'd think they could agree on 1 spelling for this
            shutil.copy(files, config.licensedir)

    # Log installed version
    with open(config.fpi_log, "w") as f:
        f.write(fl)


def uninstall():
    filelist = []
    fpi_content = open(config.fpi_log, "r")
    fpi_ver = fpi_content.read()

    print(
        "Beginning uninstall of linux-firmware-"
        + fpi_ver
        + "."
    )


    print(
        "Generating list of files to remove."
    )

    with open(config.files_log, "r") as f:
        for files in f.readlines():
            if os.path.exists(os.path.join(config.firmwaredir, files.strip())):
                print("Found "
                    + files
                )
                print("Removing "
                    + files
                )
                os.remove(os.path.join(config.firmwaredir, files.strip()))
    print(
        "Removing dead symlinks."
    )
    subprocess.run(["find", config.firmwaredir, "-xtype", "l", "-delete"])

    print(
        "Removing empty directories."
    )
    subprocess.run(["find", config.firmwaredir, "-type", "d", "-empty", "-delete"])

    print(
        "Removing installer logs."
    )
    os.remove(config.fpi_log)
    os.remove(config.files_log)


def setup():
    temp_flni = tempfile.mkdtemp()
    os.chdir(temp_flni)
    return temp_flni


def cleanup(tf):
    print("Cleaning up temporary files.")
    if os.path.exists(tf):
        shutil.rmtree(tf)
