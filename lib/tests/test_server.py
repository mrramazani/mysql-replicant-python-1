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

from mysql.replicant.errors import (
    NotMainError,
    NotSubordinateError,
    )

from mysql.replicant.commands import (
    change_main,
    fetch_main_position,
    fetch_subordinate_position,
    lock_database,
    unlock_database,
    )

import tests.utils

_POS_CRE = re.compile(r"Position\(('\w+-bin.\d+', \d+)?\)")

class TestServerBasics(unittest.TestCase):
    """Test case to test server basics. It relies on an existing MySQL
    server."""

    def __init__(self, methodName, options):
        super(TestServerBasics, self).__init__(methodName)
        my = tests.utils.load_deployment(options['deployment'])
        self.main = my.main
        self.subordinate = my.subordinates[0]
        self.subordinates = my.subordinates

    def setUp(self):
        pass

    def testConfig(self):
        "Get some configuration information from the server"
        self.assertEqual(self.main.host, "localhost")
        self.assertEqual(self.main.port, 3307)
        self.assertEqual(self.main.socket, '/var/run/mysqld/mysqld1.sock')

    def testFetchReplace(self):
        "Fetching a configuration file, adding some options, and replacing it"
        config = self.main.fetch_config(os.path.join(here, 'test.cnf'))
        self.assertEqual(config.get('user'), 'mysql')
        self.assertEqual(config.get('log-bin'), '/var/log/mysql/main-bin')
        self.assertEqual(config.get('subordinate-skip-start'), None)
        config.set('no-value')
        self.assertEqual(config.get('no-value'), None)
        config.set('with-int-value', 4711)
        self.assertEqual(config.get('with-int-value'), '4711')
        config.set('with-string-value', 'Careful with that axe, Eugene!')
        self.assertEqual(config.get('with-string-value'),
                         'Careful with that axe, Eugene!')
        self.main.replace_config(config, os.path.join(here, 'test-new.cnf'))
        lines1 = file(os.path.join(here, 'test.cnf')).readlines()
        lines2 = file(os.path.join(here, 'test-new.cnf')).readlines()
        lines1 += ["\n", "no-value\n", "with-int-value = 4711\n",
                   "with-string-value = Careful with that axe, Eugene!\n"]
        lines1.sort()
        lines2.sort()
        self.assertEqual(lines1, lines2)
        os.remove(os.path.join(here, 'test-new.cnf'))

        
    def testSsh(self):
        "Testing ssh() call"
        self.assertEqual(''.join(self.main.ssh(["echo", "-n", "Hello"])),
                         "Hello")
 
    def testSql(self):
        "Testing (read-only) SQL execution"
        result = self.main.sql("select 'Hello' as val")['val']
        self.assertEqual(result, "Hello")

    def testLockUnlock(self):
        "Test that the lock and unlock functions can be called"
        lock_database(self.main)
        unlock_database(self.main)

    def testGetMainPosition(self):
        "Fetching main position from the main and checking format"
        try:
            position = fetch_main_position(self.main)
            self.assertTrue(position is None or _POS_CRE.match(str(position)),
                            "Position '%s' is not correct" % (str(position)))
        except NotMainError:
            self.fail(
                "Unable to test fetch_main_position since"
                " main is not configured as a main"
                )

    def testGetSubordinatePosition(self):
        "Fetching subordinate positions from the subordinates and checking format"
        for subordinate in self.subordinates:
            try:
                position = fetch_subordinate_position(subordinate)
                self.assertTrue(_POS_CRE.match(str(position)),
                                "Incorrect position '%s'" % (str(position)))
            except NotSubordinateError:
                pass

def suite(options={}):
    if not options['deployment']:
        return None
    suite = unittest.TestSuite()
    for test in unittest.defaultTestLoader.getTestCaseNames(TestServerBasics):
        suite.addTest(TestServerBasics(test, options))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

