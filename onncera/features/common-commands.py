
""" COMMENTARY
- THIS FILE CONTAINS ALL COMMON EMACS KEYBINDS THAT DO NOT REQUIRE CONVOLUTED AMOUNTS OF CODE TO IMPLEMENT
"""

import sublime
import sublime_plugin

class SebQuitCommand(sublime_plugin.TextCommand):

	""" emacs c-g
	- A QUIT COMMAND THAT COLLASPE SELECTION(S) TO THE CURSOR AND DEACTIVATE THE MARK
	"""

	def run(self, edit):
		sel = self.view.sel()

		# KEEP ONLY THE LAST CURSOR (WHERE POINT VISUALLY IS) AND CLEAR ITS SELECTION
		point = sel[-1].b
		sel.clear()
		sel.add(sublime.Region(point))

		# mark integration: deactivate the mark if one is active
		if  self.view.settings().get("onncera_mark_active", False):
			self.view.settings().set("onncera_mark_active", False)
			self.view.erase_regions("onncera_mark")
