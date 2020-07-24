# Copyright (c) 2010, Mats Kindahl, Charles Bell, and Lars Thalmann
# All rights reserved.
#
# Use of this source code is goverened by a BSD licence that can be
# found in the LICENCE file.

import mysql.replicant.errors as _errors

import subprocess

def lock_database(server):
    """Flush all tables and lock the database"""
    server.sql("FLUSH TABLES WITH READ LOCK")

def unlock_database(server):
    "Unlock database"
    server.sql("UNLOCK TABLES")

_CHANGE_MASTER_TO = """CHANGE MASTER TO
   MASTER_HOST=%s, MASTER_PORT=%s,
   MASTER_USER=%s, MASTER_PASSWORD=%s,
   MASTER_LOG_FILE=%s, MASTER_LOG_POS=%s"""

_CHANGE_MASTER_TO_NO_POS = """CHANGE MASTER TO
   MASTER_HOST=%s, MASTER_PORT=%s,
   MASTER_USER=%s, MASTER_PASSWORD=%s"""

def change_main(subordinate, main, position=None):
    """Configure replication to read from a main and position."""
    try:
        user = main.repl_user
    except AttributeError:
        raise _errors.NotMainError

    subordinate.sql("STOP SLAVE")
    if position:
        subordinate.sql(_CHANGE_MASTER_TO,
                  (main.host, main.port, user.name, user.passwd,
                   position.file, position.pos))
    else:
        subordinate.sql(_CHANGE_MASTER_TO_NO_POS,
                  (main.host, main.port, user.name, user.passwd))
    subordinate.sql("START SLAVE")
    subordinate.disconnect()

def fetch_main_position(server):
    """Get the position of the next event that will be written to
    the binary log"""

    from mysql.replicant.server import Position
    try:
        result = server.sql("SHOW MASTER STATUS")
        return Position(result["File"], result["Position"])
    except _errors.EmptyRowError:
        raise _errors.NotMainError

def fetch_subordinate_position(server):
    """Get the position of the next event to be read from the main.

    """

    from mysql.replicant.server import Position

    try:
        result = server.sql("SHOW SLAVE STATUS")
        return Position(result["Relay_Main_Log_File"],
                        result["Exec_Main_Log_Pos"])
    except _errors.EmptyRowError:
        raise _errors.NotSubordinateError

_START_SLAVE_UNTIL = """START SLAVE UNTIL
    MASTER_LOG_FILE=%s, MASTER_LOG_POS=%s"""

_MASTER_POS_WAIT = "SELECT MASTER_POS_WAIT(%s, %s)"

def subordinate_wait_for_pos(subordinate, position):
    subordinate.sql(_MASTER_POS_WAIT, (position.file, position.pos))

def subordinate_status_wait_until(server, field, pred):
    while True:
        row = server.sql("SHOW SLAVE STATUS")
        value = row[field]
        if pred(value):
            return value

def subordinate_wait_and_stop(subordinate, position):
    """Set up replication so that it will wait for the position to be
    reached and then stop replication exactly at that binlog
    position."""
    subordinate.sql("STOP SLAVE")
    subordinate.sql(_START_SLAVE_UNTIL, (position.file, position.pos))
    subordinate.sql(_MASTER_POS_WAIT, (position.file, position.pos))
    
def subordinate_wait_for_empty_relay_log(server):
    "Wait until the relay log is empty and return."
    result = server.sql("SHOW SLAVE STATUS")
    fname = result["Main_Log_File"]
    pos = result["Read_Main_Log_Pos"]
    if server.sql(_MASTER_POS_WAIT, (fname, pos)) is None:
        raise _errors.SubordinateNotRunningError

def fetch_binlog(server, binlog_files=None,
                 start_datetime=None, stop_datetime=None):
    """Fetch the lines of a binary log remotely using the
    ``mysqlbinlog`` program.

    If no binlog file names are given, a connection to the server is
    made and a ``SHOW BINARY LOGS`` is executed to get a full list of
    the binary logs, which is then used.
    """
    from subprocess import Popen, PIPE
    if not binlog_files:
        binlog_files = [
            row["Log_name"] for row in server.sql("SHOW BINARY LOGS")]
    
    command = ["mysqlbinlog",
               "--read-from-remote-server",
               "--force",
               "--host=%s" % (server.host),
               "--user=%s" % (server.sql_user.name)]
    if server.sql_user.passwd:
        command.append("--password=%s" % (server.sql_user.passwd))
    if start_datetime:
        command.append("--start-datetime=%s" % (start_datetime))
    if stop_datetime:
        command.append("--stop-datetime=%s" % (stop_datetime))
    return iter(Popen(command + binlog_files, stdout=PIPE).stdout)

def clone(subordinate, source, main = None):
    """Function to create a new subordinate by cloning either a main or a
    subordinate."""

    backup_name = source.host + ".tar.gz"
    if main is not None:
        source.sql("STOP SLAVE")
    lock_database(source)
    if main is None:
        position = fetch_main_position(source)
    else:
        position = fetch_subordinate_position(source)
    source.ssh("tar Pzcf " + backup_name + " /usr/var/mysql")
    if main is not None:
        source.sql("START SLAVE")
    subprocess.call(["scp", source.host + ":" + backup_name, subordinate.host + ":."])
    subordinate.ssh("tar Pzxf " + backup_name + " /usr/var/mysql")
    if main is None:
        change_main(subordinate, source, position)
    else:
        change_main(subordinate, main, position)
    subordinate.sql("START SLAVE")

_START_SLAVE_UNTIL = "START SLAVE UNTIL MASTER_LOG_FILE=%s, MASTER_LOG_POS=%s"
_MASTER_POS_WAIT = "SELECT MASTER_POS_WAIT(%s,%s)"

def replicate_to_position(server, pos):
    """Run replication until it reaches 'pos'.

    The function will block until the subordinate have reached the position."""
    server.sql(_START_SLAVE_UNTIL, (pos.file, pos.pos))
    server.sql(_MASTER_POS_WAIT, (pos.file, pos.pos))
