# encoding: utf-8
"""
delta.py

Created by Thomas Mangin on 2009-11-07.
Copyright (c) 2009-2012 Exa Networks. All rights reserved.
"""

from exabgp.bgp.message.update import Update

from exabgp.structure.log import Logger


class Delta (object):
	def __init__ (self,table):
		self.logger = Logger()
		self.table = table
		self.last = 0

	def updates  (self,negociated,grouped):
		self.table.recalculate()
		if grouped:
			return self.group_updates (negociated)
		else:
			return self.simple_updates (negociated)

	def simple_updates (self,negociated):
		# table.changed always returns routes to remove before routes to add
		for action,route in self.table.changed(self.last):
			if action == '':
				self.last = route # when action is '' route is a timestamp
				continue

			if action == '+':
				self.logger.rib('announcing %s' % route)
				for update in Update().new([route]).announce(negociated):
					yield update
			elif action == '*':
				self.logger.rib('updating %s' % route)
				for update in Update().new([route]).announce(negociated):
					yield update
			elif action == '-':
				self.logger.rib('withdrawing %s' % route)
				for update in Update().new([route]).withdraw(negociated):
					yield update

	def group_updates (self,negociated):
		grouped = {
			'+' : {},
			'*' : {},
			'-' : {},
		}

		# table.changed always returns routes to remove before routes to add
		for action,route in self.table.changed(self.last):
			if action == '':
				self.last = route # when action is '' route is a timestamp
				continue
			grouped[action].setdefault(str(route.attributes),[]).append(route)

		group = 0
		for attributes in grouped['+']:
			routes = grouped['+'][attributes]
			for route in routes:
				self.logger.rib('announcing group %d %s' % (group,route))
			group += 1
			for update in Update().new(routes).announce(negociated):
				yield update
		for attributes in grouped['*']:
			routes = grouped['*'][attributes]
			for route in routes:
				self.logger.rib('updating group %d %s' % (group,route))
			group += 1
			for update in Update().new(routes).update(negociated):
				yield update
		for attributes in grouped['*']:
			routes = grouped['*'][attributes]
			for route in routes:
				self.logger.rib('updating group %d %s' % (group,route))
			group += 1
			for update in Update().new(routes).withdraw(negociated):
				yield update

