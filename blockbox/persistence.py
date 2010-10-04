# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from ConfigParser import RawConfigParser as ConfigParser
from lib.twisted.internet import reactor

class PersistenceEngine(object):
	def __init__(self, username):
		self.username = username
		if self.factory.info_store == "flatfile":
			self.ini = ConfigParser()
		else:
			raise StoringMethodNotSupported
		reactor.callLater(.1, self.reload, username)
	
	def __str__(self):
		return self.username
	
	def __enter__(self):
		return self
	
	def __exit__(self, type, value, traceback):
		self.username = None
		self.ini = None
	
	def reload(self, username):
		try:
			self.ini.read("persist/%s.ini" % username.lower())
		except:
			pass
		else:
			reactor.callLater(10, self.reload, username)
			
	def string(self, section, name, default=None):
		try:
			ret = self.ini.get(section, name)
		except:
			if default is not None:
				self.set(section, name, default)
				ret = default
			else:
				ret = ""
		return ret
	
	def int(self, section, name, default=None):
		try:
			ret = self.ini.getint(section, name)
		except:
			if default is not None:
				self.set(section, name, default)
				ret = default
			else:
				ret = 0
		return ret
		
	def bool(self, section, name, default=None):
		try:
			ret = self.ini.getboolean(section, name)
		except:
			if default is not None:
				self.set(section, name, default)
				ret = default
			else:
				ret = False
		return ret
	
	def set(self, section, name, value):
		self.ini.read("persist/%s.ini" % self.username.lower())
		if not self.ini.has_section(section):
			self.ini.add_section(section)
		self.ini.set(section, name, str(value))
		with open("persist/%s.ini" % self.username.lower(), "w") as fp:
			self.ini.write(fp)
