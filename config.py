#######################################################################
# This file is part of flni.
#
# Copyright (C) 2021 by Jesse Rhodes.
#
# flni is distributed under the MIT license.  See the file
# LICENSE for distribution details.
#######################################################################


# Global configuration variables
import os

baseurl = "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/"
snapshoturl = baseurl + "snapshot/"
tagurl = baseurl + "refs/tags"

install_prefix = "/usr/local"
firmwaredir = "/lib/firmware"
package_prefix = "share/flni"

signing_key = os.path.join(install_prefix,  package_prefix,  "signing-key.asc")
fpi_log = os.path.join(install_prefix, package_prefix, "firmware_installed") # firmware previously installed
licensedir = os.path.join(install_prefix, package_prefix, "firmware_licenses")

