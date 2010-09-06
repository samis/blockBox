# -*- test-case-name: lib.twisted.test.test_app -*-
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


"""Backwards compatability, and utility functions.

In general, this module should not be used, other than by reactor authors
who need to use the 'installReactor' method.

Maintainer: Itamar Shtull-Trauring
"""

import error

CONNECTION_DONE = error.ConnectionDone('Connection done')
CONNECTION_LOST = error.ConnectionLost('Connection lost')

def installReactor(reactor):
    # this stuff should be common to all reactors.
    import lib.twisted.internet
    import sys
    assert not sys.modules.has_key('lib.twisted.internet.reactor'), \
           "reactor already installed"
    lib.twisted.internet.reactor = reactor
    sys.modules['lib.twisted.internet.reactor'] = reactor

__all__ = ["CONNECTION_LOST", "CONNECTION_DONE", "installReactor"]