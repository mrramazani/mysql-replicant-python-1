# Copyright (c) 2010, Mats Kindahl, Charles Bell, and Lars Thalmann
# All rights reserved.
#
# Use of this source code is goverened by a BSD licence that can be
# found in the LICENCE file.

import sys
import os.path
here = os.path.dirname(os.path.abspath(__file__))
rootpath = os.path.split(here)[0]
sys.path.append(rootpath) 

import re
import unittest

from mysql.replicant.roles import (
    Final,
    Main,
    )

from mysql.replicant.server import (
    User,
    )

from mysql.replicant.commands import (
    change_main,
    fetch_main_position,
    fetch_subordinate_position,
    subordinate_wait_and_stop,
    subordinate_wait_for_pos,
    )

from tests.utils import load_deployment

class TestCommands(unittest.TestCase):
    """Test case to test various commands"""

    def __init__(self, methodNames, options={}):
        super(TestCommands, self).__init__(methodNames)
        my = load_deployment(options['deployment'])
        self.main = my.main
        self.mains = my.servers[0:1]
        self.subordinates = my.servers[2:3]

    def setUp(self):

        main_role = Main(User("repl_user", "xyzzy"))
        for main in self.mains:
            main_role.imbue(main)

        final_role = Final(self.mains[0])
        for subordinate in self.subordinates:
            try:
                final_role.imbue(subordinate)
            except IOError:
                pass

    def testChangeMain(self):
        "Test the change_main function"
        for subordinate in self.subordinates:
            change_main(subordinate, self.main)

        self.main.sql("DROP TABLE IF EXISTS t1", db="test")
        self.main.sql("CREATE TABLE t1 (a INT)", db="test")
        self.main.disconnect()

        for subordinate in self.subordinates:
            result = subordinate.sql("SHOW TABLES", db="test")

    def testSubordinateWaitForPos(self):
        "Test the subordinate_wait_for_pos function"

        subordinate = self.subordinates[0]
        main = self.main

        subordinate.sql("STOP SLAVE")
        pos1 = fetch_main_position(main)
        change_main(subordinate, main, pos1)
        subordinate.sql("START SLAVE")

        main.sql("DROP TABLE IF EXISTS t1", db="test")
        main.sql("CREATE TABLE t1 (a INT)", db="test")
        main.sql("INSERT INTO t1 VALUES (1),(2)", db="test")
        pos2 = fetch_main_position(main)
        subordinate_wait_for_pos(subordinate, pos2)
        pos3 = fetch_subordinate_position(subordinate)
        self.assert_(pos3 >= pos2)

    def testSubordinateWaitAndStop(self):
        "Test the subordinate_wait_and_stop function"

        subordinate = self.subordinates[0]
        main = self.main

        subordinate.sql("STOP SLAVE")
        pos1 = fetch_main_position(main)
        change_main(subordinate, main, pos1)
        subordinate.sql("START SLAVE")

        main.sql("DROP TABLE IF EXISTS t1", db="test")
        main.sql("CREATE TABLE t1 (a INT)", db="test")
        main.sql("INSERT INTO t1 VALUES (1),(2)", db="test")
        pos2 = fetch_main_position(main)
        main.sql("INSERT INTO t1 VALUES (3),(4)", db="test")
        pos3 = fetch_main_position(main)
        subordinate_wait_and_stop(subordinate, pos2)
        pos4 = fetch_subordinate_position(subordinate)
        self.assertEqual(pos2, pos4)
        row = subordinate.sql("SELECT COUNT(*) AS count FROM t1", db="test")
        self.assertEqual(row['count'], 2)
        subordinate.sql("START SLAVE")
        subordinate_wait_and_stop(subordinate, pos3)
        row = subordinate.sql("SELECT COUNT(*) AS count FROM t1", db="test")
        self.assertEqual(row['count'], 4)

    def testSubordinateStatusWaitUntil(self):
        "Test subordinate_status_wait_until"
        subordinate = self.subordinates[0]
        main = self.main

        subordinate.sql("STOP SLAVE")
        pos1 = fetch_main_position(main)
        change_main(subordinate, main, pos1)
        subordinate.sql("START SLAVE")
        

def suite(options={}):
    if not options['deployment']:
        return None
    suite = unittest.TestSuite()
    for test in unittest.defaultTestLoader.getTestCaseNames(TestCommands):
        suite.addTest(TestCommands(test, options))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')


