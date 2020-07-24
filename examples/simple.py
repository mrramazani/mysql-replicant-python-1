# Copyright (c) 2010, Mats Kindahl, Charles Bell, and Lars Thalmann
# All rights reserved.
#
# Use of this source code is goverened by a BSD licence that can be
# found in the LICENCE file.

import sys, os.path
rootpath = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
sys.path.append(rootpath) 

import my_deployment
from mysql.replicant.server import (
    User,
    )
from mysql.replicant.roles import (
    Main,
    Final,
    )
from mysql.replicant.commands import (
    change_main,
    )

main_role = Main(User("repl_user", "xyzzy"))
final_role = Final(my_deployment.main)

try:
    main_role.imbue(my_deployment.main)
except IOError, e:
    print "Cannot imbue main with Main role:", e

for subordinate in my_deployment.subordinates:
    try:
        final_role.imbue(subordinate)
    except IOError, e:
        print "Cannot imbue subordinate with Final role:", e
