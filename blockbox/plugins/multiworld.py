#	iCraft is Copyright 2010 both
#
#	The Archives team:
#				   <Adam Guy> adam@adam-guy.com AKA "Adam01"
#				   <Andrew Godwin> andrew@aeracode.org AKA "Aera"
#				   <Dylan Lukes> lukes.dylan@gmail.com AKA "revenant"
#				   <Gareth Coles> colesgareth2@hotmail.com AKA "gdude2002"
#
#	And,
#
#	The iCraft team:
#				   <Andrew Dolgov> fox@bah.org.ru AKA "gothfox"
#				   <Andrew Horn> Andrew@GJOCommunity.com AKA "AndrewPH"
#				   <Brad Reardon> brad@bradness.co.cc AKA "PixelEater"
#				   <Clay Sweetser> CDBKJmom@aol.com AKA "Varriount"
#				   <James Kirslis> james@helplarge.com AKA "iKJames"
#				   <Jason Sayre> admin@erronjason.com AKA "erronjason"
#				   <Joseph Connor> destroyerx100@gmail.com AKA "destroyerx1"
#				   <Nick Tolrud> ntolrud@yahoo.com AKA "ntfwc"
#				   <Noel Benzinger> ronnygmod@gmail.com AKA "Dwarfy"
#				   <Randy Lyne> qcksilverdragon@gmail.com AKA "goober"
#				   <Willem van der Ploeg> willempieeploeg@live.nl AKA "willempiee"
#
#	iCraft is licensed under the Creative Commons
#	Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
#	To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#	Or, send a letter to Creative Commons, 171 2nd Street,
#	Suite 300, San Francisco, California, 94105, USA.

import random
import os
import shutil
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
from blockbox.world import World

class MultiWorldPlugin(ProtocolPlugin):
	
	commands = {
		"new": "commandNew",
		"mapadd": "commandNew",
		"rename": "commandRename",
		"maprename": "commandRename",
		"shutdown": "commandShutdown",
		"l": "commandLoad",
		"j": "commandLoad",
		"load": "commandLoad",
		"join": "commandLoad",
		"map": "commandLoad",
		"boot": "commandBoot",
		"worlds": "commandWorlds",
		"maps": "commandWorlds",
		"templates": "commandTemplates",
		"reboot": "commandReboot",
		"home": "commandHome",
		"create": "commandCreate",
		"delete": "commandDelete",
		"mapdelete": "commandDelete",
		"undelete": "commandUnDelete",
		"deleted": "commandDeleted",
	}
	
	@world_list
	@admin_only
	def commandNew(self, parts, byuser, overriderank):
		"/new worldname [templatename] - Admin\nAliases: mapadd\nMakes a new world, and boots it."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a new worldname.")
		elif self.client.factory.world_exists(parts[1]):
			self.client.sendServerMessage("Worldname in use")
		else:
			if len(parts) == 2:
				template = "default"
			elif len(parts) == 3 or len(parts) == 4:
				template = parts[2]
			world_id = parts[1].lower()
			self.client.factory.newWorld(world_id, template)
			self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
			self.client.factory.worlds[world_id].all_write = False
			if len(parts) < 4:
				self.client.sendServerMessage("World '%s' made and booted." % world_id)

	@world_list
	@mod_only
	def commandRename(self, parts, byuser, overriderank):
		"/rename worldname newworldname - Mod\nAliases: maprename\nRenames a SHUT DOWN world."
		if len(parts) < 3:
			self.client.sendServerMessage("Please specify two worldnames.")
		else:
			old_worldid = parts[1]
			new_worldid = parts[2]
			if old_worldid in self.client.factory.worlds:
				self.client.sendServerMessage("World '%s' is booted, please shut it down!" % old_worldid)
			elif not self.client.factory.world_exists(old_worldid):
				self.client.sendServerMessage("There is no world '%s'." % old_worldid)
			elif self.client.factory.world_exists(new_worldid):
				self.client.sendServerMessage("There is already a world called '%s'." % new_worldid)
			else:
				self.client.factory.renameWorld(old_worldid, new_worldid)
				self.client.sendServerMessage("World '%s' renamed to '%s'." % (old_worldid, new_worldid))
	
	@world_list
	@mod_only
	def commandShutdown(self, parts, byuser, overriderank):
		"/shutdown worldname - Mod\nTurns off the named world."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
		else:
			if parts[1] in self.client.factory.worlds:
				self.client.factory.unloadWorld(parts[1])
				self.client.sendServerMessage("World '%s' unloaded." % parts[1])
			else:
				self.client.sendServerMessage("World '%s' doesn't exist." % parts[1])

	@world_list
	@mod_only
	def commandReboot(self, parts, byuser, overriderank):
		"/reboot worldname - Mod\nReboots a map"
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
		else:
			if parts[1] in self.client.factory.worlds:
				self.client.factory.rebootworld(parts[1])
				self.client.sendServerMessage("World %s rebooted" % parts[1])
			else:
				self.client.sendServerMessage("World '%s' isnt booted." % parts[1])

	@world_list
	@mod_only
	def commandBoot(self, parts, byuser, overriderank):
		"/boot worldname - Mod\nStarts up a new world."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
		else:
			if parts[1] in self.client.factory.worlds:
				self.client.sendServerMessage("World '%s' already exists!" % parts[1])
			else:
				try:
					self.client.factory.loadWorld("mapdata/worlds/%s" % parts[1], parts[1])
					self.client.sendServerMessage("World '%s' booted." % parts[1])
				except AssertionError:
					self.client.sendServerMessage("There is no world by that name.")
	
	@world_list
	@only_string_command("world name")
	def commandLoad(self, world_id, byuser, overriderank, params=None):
		"/l worldname - Guest\nAliases: j, join, load, map\nMoves you into world 'worldname'"
		if world_id not in self.client.factory.worlds:
			self.client.sendServerMessage("Attempting to boot and join '%s'" % world_id)
			try:
				self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
			except AssertionError:
				self.client.sendServerMessage("There is no world by that name.")
				return
		world = self.client.factory.worlds[world_id]
		if not self.client.canEnter(world):
			if world.private:
				self.client.sendServerMessage("'%s' is private; you're not allowed in." % world_id)
				return
			#elif self.username.lower() in world.worldbans:
			else:
				self.client.sendServerMessage("You're WorldBanned from '%s'; so you're not allowed in." % world_id)
				return
		self.client.changeToWorld(world_id)
	
	@world_list
	def commandWorlds(self, parts, byuser, overriderank):
		"/worlds [letter|all] - Guest\nAliases: maps\nLists available worlds - by letter, online, or all."
		if len(parts) != 2 and len(parts) != 3:
			self.client.sendServerMessage("Do /worlds all for all worlds or choose a letter.")
			self.client.sendServerList(["Online:"] + [id for id, world in self.client.factory.worlds.items() if self.client.canEnter(world)])
			return
		else:
			if parts[1] == 'all':
				self.client.sendServerList(["Worlds:"] + os.listdir("worlds/"))
				return
			if len(parts[1]) != 1:
				self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
				return
			if len(parts)==3:
				if len(parts[2]) != 1:
					self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
					return
			letter1 = ord(parts[1].lower())
			if len(parts)==3:
				letter2 = ord(parts[2].lower())
			else:
				letter2 = letter1
			if letter1>letter2:
				a = letter1
				letter1 = letter2
				letter2 = a
			worldlist = os.listdir("mapdata/worlds/")
			newlist = []
			for world in worldlist:
				if letter1 <= ord(world[0]) <= letter2 and not world.startswith("."):
					newlist.append(world)
			self.client.sendServerList(["Worlds:"] + newlist)

	def commandTemplates(self, parts, byuser, overriderank):
		"/templates - Guest\nLists available templates"
		self.client.sendServerList(["Templates:"] + os.listdir("mapdata/templates/"))

	def commandHome(self, parts, byuser, overriderank):
		"/home [worldname] - Guest\nGoes to and/or changes your home world."
		if not len(parts) > 1:
			self.client.changeToWorld(self.client.homeworld)
		else:
			self.client.homeworld = parts[1]
			self.client.persist.set("misc", "homeworld", parts[1])
			self.client.sendServerMessage("Your home world is now %s!" % parts[1])

	@world_list
	@admin_only
	def commandCreate(self, parts, byuser, overriderank):
		"/create worldname width height length - Admin\nCreates a new world with specified dimensions."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a world name.")
		elif self.client.factory.world_exists(parts[1]):
			self.client.sendServerMessage("Worldname in use")
		elif len(parts) < 5:
			self.client.sendServerMessage("Please specify dimensions. (width, length, height)")
		elif int(parts[2]) < 16 or int(parts[3]) < 16 or int(parts[4]) < 16:
			self.client.sendServerMessage("No dimension may be smaller than 16.")
		elif int(parts[2]) > 1024 or int(parts[3]) > 1024 or int(parts[4]) > 1024:
			self.client.sendServerMessage("No dimension may be greater than 1024.")
		elif (int(parts[2]) % 16) > 0 or (int(parts[3]) % 16) > 0 or (int(parts[4]) % 16) > 0:
			self.client.sendServerMessage("All dimensions must be divisible by 16.")
		else:
			world_id = parts[1].lower()
			sx, sy, sz = int(parts[2]), int(parts[3]), int(parts[4])
			grass_to = (sy // 2)
			world = World.create(
				"mapdata/worlds/%s" % world_id,
				sx, sy, sz, # Size
				sx//2,grass_to+2, sz//2, 0, # Spawn
				([BLOCK_DIRT]*(grass_to-1) + [BLOCK_GRASS] + [BLOCK_AIR]*(sy-grass_to)) # Levels
			)
			self.client.factory.loadWorld("mapdata/worlds/%s" % world_id, world_id)
			self.client.factory.worlds[world_id].all_write = False
			self.client.sendServerMessage("World '%s' made and booted." % world_id)
	
	@world_list
	@admin_only
	def commandDelete(self, parts, byuser, overriderank):
		"/delete worldname - Admin\nAliases: mapdelete\nSets the specified world to 'ignored'."
		if len(parts) == 1:
			self.client.sendServerMessage("Please specify a worldname.")
		else:
			if not os.path.exists("mapdata/worlds/%s" % parts[1]):
				self.client.sendServerMessage("World %s doesnt exist." %(parts[1]))
				return
			if parts[1] in self.client.factory.worlds:
				self.client.factory.unloadWorld(parts[1])
			name = parts[1]
			extra="_0"
			if os.path.exists("mapdata/worlds/.trash/%s" %(name)):
				while True:
					if os.path.exists("mapdata/worlds/.trash/%s" %(name+extra)):
						extra = "_" + str(int(extra[1:])+1)
					else:
						name = name+extra
						break
			shutil.copytree("mapdata/worlds/%s" %parts[1], "mapdata/worlds/.trash/%s" %parts[1])
			shutil.rmtree("mapdata/mworlds/%s" % parts[1])
			self.client.sendServerMessage("World deleted.")
	
	@world_list
	@admin_only
	def commandUnDelete(self, parts, byuser, overriderank):
		"/undelete worldname - Admin\nRestores a deleted map."
		if len(parts) < 2:
			self.client.sendServerMessage("Please specify a worldname.")
			return
		name = parts[1]
		world_dir = ("mapdata/worlds/.trash/%s/" % name)
		if not os.path.exists(world_dir):
		   self.client.sendServerMessage("World %s is not in the world trash bin." % name)
		   return
		extra="_0"
		if os.path.exists("mapdata/worlds/%s/" %(name)):
			while True:
				if os.path.exists("mapdata/worlds/%s/" %(name+extra)):
					extra = "_" + str(int(extra[1:])+1)
				else:
					name = name+extra
					break
		path = ("mapdata/worlds/%s/" % name)
		shutil.move(world_dir, path)
		self.client.sendServerMessage("World restored as %s." % name)

	@world_list
	@admin_only
	def commandDeleted(self, parts, byuser, overriderank):
		"/deleted [letter] - Admin\nLists deleted worlds - by letter or all."
		if len(parts) != 2 and len(parts) != 3:
			self.client.sendServerMessage("Do '/deleted letter' for all starting with a letter.")
			self.client.sendServerList(["Deleted:"] + os.listdir("mapdata/worlds/.trash/"))
			return
		else:
			if len(parts[1]) != 1:
				self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
				return
			if len(parts)==3:
				if len(parts[2]) != 1:
					self.client.sendServerMessage("Only specify one starting letter per entry, not multiple")
					return
			letter1 = ord(parts[1].lower())
			if len(parts)==3:
				letter2 = ord(parts[2].lower())
			else:
				letter2 = letter1
			if letter1>letter2:
				a = letter1
				letter1 = letter2
				letter2 = a
			worldlist = os.listdir("mapdata/worlds/.trash/")
			newlist = []
			for world in worldlist:
				if letter1 <= ord(world[0]) <= letter2 and not world.startswith("."):
					newlist.append(world)
			self.client.sendServerList(["Deleted:"] + newlist)