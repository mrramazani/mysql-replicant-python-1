# Copyright (c) 2010, Mats Kindahl, Charles Bell, and Lars Thalmann
# All rights reserved.
#
# Use of this source code is goverened by a BSD licence that can be
# found in the LICENCE file.

import sys
import os.path
rootpath = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
sys.path.append(rootpath)

from mysql.replicant.commands import (
    fetch_main_pos,
    fetch_subordinate_pos,
    )

from mysql.replicant.errors import (
    NotMainError,
    NotSubordinateError,
    )

import my_deployment

print "# Executing 'show databases'"
for db in my_deployment.main.sql("show databases"):
    print db["Database"]

print "# Executing 'ls'"
for line in my_deployment.main.ssh(["ls"]):
    print line

try:
    print "Main position is:", fetch_main_pos(my_deployment.main)
except NotMainError:
    print my_deployment.main.name, "is not configured as a main"

for subordinate in my_deployment.subordinates:
    try:
        print "Subordinate position is:", fetch_subordinate_pos(subordinate)
    except NotSubordinateError:
        print subordinate.name, "not configured as a subordinate"
