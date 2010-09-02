# -*- test-case-name: lib.twisted.test.test_plugin -*-
# Copyright (c) 2005 Divmod, Inc.
# Copyright (c) 2007-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Plugin system for Twisted.

@author: Jp Calderone
@author: Glyph Lefkowitz
"""

import os
import sys

from lib.zope.interface import Interface, providedBy

def _determinePickleModule():
    """
    Determine which 'pickle' API module to use.
    """
    try:
        import cPickle
        return cPickle
    except ImportError:
        import pickle
        return pickle

pickle = _determinePickleModule()

from lib.twisted.python.components import getAdapterFactory
from lib.twisted.python.reflect import namedAny
from lib.twisted.python import log
from lib.twisted.python.modules import getModule



class IPlugin(Interface):
    """
    Interface that must be implemented by all plugins.

    Only objects which implement this interface will be considered for return
    by C{getPlugins}.  To be useful, plugins should also implement some other
    application-specific interface.
    """



class CachedPlugin(object):
    def __init__(self, dropin, name, description, provided):
        self.dropin = dropin
        self.name = name
        self.description = description
        self.provided = provided
        self.dropin.plugins.append(self)

    def __repr__(self):
        return '<CachedPlugin %r/%r (provides %r)>' % (
            self.name, self.dropin.moduleName,
            ', '.join([i.__name__ for i in self.provided]))

    def load(self):
        return namedAny(self.dropin.moduleName + '.' + self.name)

    def __conform__(self, interface, registry=None, default=None):
        for providedInterface in self.provided:
            if providedInterface.isOrExtends(interface):
                return self.load()
            if getAdapterFactory(providedInterface, interface, None) is not None:
                return interface(self.load(), default)
        return default

    # backwards compat HOORJ
    getComponent = __conform__



class CachedDropin(object):
    """
    A collection of L{CachedPlugin} instances from a particular module in a
    plugin package.

    @type moduleName: C{str}
    @ivar moduleName: The fully qualified name of the plugin module this
        represents.

    @type description: C{str} or C{NoneType}
    @ivar description: A brief explanation of this collection of plugins
        (probably the plugin module's docstring).

    @type plugins: C{list}
    @ivar plugins: The L{CachedPlugin} instances which were loaded from this
        dropin.
    """
    def __init__(self, moduleName, description):
        self.moduleName = moduleName
        self.description = description
        self.plugins = []



def _generateCacheEntry(provider):
    dropin = CachedDropin(provider.__name__,
                          provider.__doc__)
    for k, v in provider.__dict__.iteritems():
        plugin = IPlugin(v, None)
        if plugin is not None:
            cachedPlugin = CachedPlugin(dropin, k, v.__doc__, list(providedBy(plugin)))
    return dropin

try:
    fromkeys = dict.fromkeys
except AttributeError:
    def fromkeys(keys, value=None):
        d = {}
        for k in keys:
            d[k] = value
        return d

def getCache(module):
    """
    Compute all the possible loadable plugins, while loading as few as
    possible and hitting the filesystem as little as possible.

    @param module: a Python module object.  This represents a package to search
    for plugins.

    @return: a dictionary mapping module names to CachedDropin instances.
    """
    allCachesCombined = {}
    mod = getModule(module.__name__)
    # don't want to walk deep, only immediate children.
    buckets = {}
    # Fill buckets with modules by related entry on the given package's
    # __path__.  There's an abstraction inversion going on here, because this
    # information is already represented internally in lib.twisted.python.modules,
    # but it's simple enough that I'm willing to live with it.  If anyone else
    # wants to fix up this iteration so that it's one path segment at a time,
    # be my guest.  --glyph
    for plugmod in mod.iterModules():
        fpp = plugmod.filePath.parent()
        if fpp not in buckets:
            buckets[fpp] = []
        bucket = buckets[fpp]
        bucket.append(plugmod)
    for pseudoPackagePath, bucket in buckets.iteritems():
        dropinPath = pseudoPackagePath.child('dropin.cache')
        try:
            lastCached = dropinPath.getModificationTime()
            dropinDotCache = pickle.load(dropinPath.open('r'))
        except:
            dropinDotCache = {}
            lastCached = 0

        needsWrite = False
        existingKeys = {}
        for pluginModule in bucket:
            pluginKey = pluginModule.name.split('.')[-1]
            existingKeys[pluginKey] = True
            if ((pluginKey not in dropinDotCache) or
                (pluginModule.filePath.getModificationTime() >= lastCached)):
                needsWrite = True
                try:
                    provider = pluginModule.load()
                except:
                    # dropinDotCache.pop(pluginKey, None)
                    log.err()
                else:
                    entry = _generateCacheEntry(provider)
                    dropinDotCache[pluginKey] = entry
        # Make sure that the cache doesn't contain any stale plugins.
        for pluginKey in dropinDotCache.keys():
            if pluginKey not in existingKeys:
                del dropinDotCache[pluginKey]
                needsWrite = True
        if needsWrite:
            try:
                dropinPath.setContent(pickle.dumps(dropinDotCache))
            except:
                log.err()
        allCachesCombined.update(dropinDotCache)
    return allCachesCombined


def getPlugins(interface, package=None):
    """
    Retrieve all plugins implementing the given interface beneath the given module.

    @param interface: An interface class.  Only plugins which implement this
    interface will be returned.

    @param package: A package beneath which plugins are installed.  For
    most uses, the default value is correct.

    @return: An iterator of plugins.
    """
    if package is None:
        import lib.twisted.plugins as package
    allDropins = getCache(package)
    for dropin in allDropins.itervalues():
        for plugin in dropin.plugins:
            try:
                adapted = interface(plugin, None)
            except:
                log.err()
            else:
                if adapted is not None:
                    yield adapted


# Old, backwards compatible name.  Don't use this.
getPlugIns = getPlugins


def pluginPackagePaths(name):
    """
    Return a list of additional directories which should be searched for
    modules to be included as part of the named plugin package.

    @type name: C{str}
    @param name: The fully-qualified Python name of a plugin package, eg
        C{'lib.twisted.plugins'}.

    @rtype: C{list} of C{str}
    @return: The absolute paths to other directories which may contain plugin
        modules for the named plugin package.
    """
    package = name.split('.')
    # Note that this may include directories which do not exist.  It may be
    # preferable to remove such directories at this point, rather than allow
    # them to be searched later on.
    #
    # Note as well that only '__init__.py' will be considered to make a
    # directory a package (and thus exclude it from this list).  This means
    # that if you create a master plugin package which has some other kind of
    # __init__ (eg, __init__.pyc) it will be incorrectly treated as a
    # supplementary plugin directory.
    return [
        os.path.abspath(os.path.join(x, *package))
        for x
        in sys.path
        if
        not os.path.exists(os.path.join(x, *package + ['__init__.py']))]

__all__ = ['getPlugins', 'pluginPackagePaths']
