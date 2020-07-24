# Copyright (c) 2010, Mats Kindahl, Charles Bell, and Lars Thalmann
# All rights reserved.
#
# Use of this source code is goverened by a BSD licence that can be
# found in the LICENCE file.

"""Module holding all the exceptions of the Replicant package.

"""

class Error(Exception):
    """Base class for all exceptions in this package
    """
    pass

class EmptyRowError(Error):
    """Class to handle attempts to fetch a key from an empty row.
    """
    pass

class NoOptionError(Error):
    "Exception raised when ConfigManager does not find the option"
    pass

class SubordinateNotRunningError(Error):
    "Exception raised when subordinate is not running but were expected to run"
    pass

class NotMainError(Error):
    """Exception raised when the server is not a main and the
    operation is illegal."""
    pass

class NotSubordinateError(Error):
    """Exception raised when the server is not a subordinate and the
    operation is illegal."""
    pass

class QueryStatusVariableError(Error):
    """Exception raised when a bad number for a non-existing status
    variable is seen in a query event.
    """
    pass

class BinlogMagicError(Error):
    """Exception raised when the binary log magic number is not
    correct. This usally indicates that it's not a binary log file,
    but it could also mean that the file is corrupt.
    """
    pass

class UnrecognizedSchemeError(Error):
    """Exception raised when a URL is used with an unrecognized scheme.
    """
    pass

class BadStatusVariableError(Error):
    """Exception raised when requesting a non-existant status
    variable.
    """
    pass

class BadMagicError(Error):
    """Exception raised when the magic for a binary log is incorrect.
    """
    pass
