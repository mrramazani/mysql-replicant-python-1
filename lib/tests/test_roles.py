# Copyright (c) 2010, Mats Kindahl, Charles Bell, and Lars Thalmann
# All rights reserved.
#
# Use of this source code is goverened by a BSD licence that can be
# found in the LICENCE file.

import sys, os.path
here = os.path.dirname(os.path.abspath(__file__))
rootpath = os.path.split(here)[0]
sys.path.append(rootpath) 

import mysql.replicant
import re
import unittest

import tests.utils

class TestRoles(unittest.TestCase):
    """Test case to test role usage."""

    def __init__(self, methodName, options):
        super(TestRoles, self).__init__(methodName)
        my = tests.utils.load_deployment(options['deployment'])
        self.main = my.main
        self.subordinate = my.subordinates[0]
        self.subordinates = my.subordinates

    def setUp(self):
        pass

    def _imbueRole(self, role):
        # We are likely to get an IOError because we cannot write the
        # configuration file, but this is OK.
        try:
            role.imbue(self.main)
        except IOError:
            pass

    def testMainRole(self):
        "Test how the main role works"
        user = mysql.replicant.server.User("repl_user", "xyzzy")
        self._imbueRole(mysql.replicant.roles.Main(user))
        
    def testSubordinateRole(self):
        "Test that the subordinate role works"
        self._imbueRole(mysql.replicant.roles.Final(self.main))

    def testRelayRole(self):
        "Test that the subordinate role works"
        self._imbueRole(mysql.replicant.roles.Relay(self.main))

def suite(options={}):
    if not options['deployment']:
        return None
    suite = unittest.TestSuite()
    for test in unittest.defaultTestLoader.getTestCaseNames(TestRoles):
        suite.addTest(TestRoles(test, options))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
