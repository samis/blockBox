# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

import sys

from lib.twisted.trial import unittest
from lib.twisted.python.runtime import platform
from lib.twisted.python.util import sibpath
from lib.twisted.internet.utils import getProcessOutputAndValue


skipWindowsNopywin32 = None
if platform.isWindows():
    try:
        import win32process
    except ImportError:
        skipWindowsNopywin32 = ("On windows, spawnProcess is not available "
                                "in the absence of win32process.")

class QtreactorTestCase(unittest.TestCase):
    """
    Tests for L{twisted.internet.qtreactor}.
    """
    def test_importQtreactor(self):
        """
        Attempting to import L{twisted.internet.qtreactor} should raise an
        C{ImportError} indicating that C{qtreactor} is no longer a part of
        Twisted.
        """
        sys.modules["qtreactor"] = None
        from lib.twisted.plugins.twisted_qtstub import errorMessage
        try:
            import lib.twisted.internet.qtreactor
        except ImportError, e:
            self.assertEquals(str(e), errorMessage)
