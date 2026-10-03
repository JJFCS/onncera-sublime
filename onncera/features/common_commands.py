
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
		regions = list(self.view.sel())

		# IF THERE IS EXACTLY ONE SELECTION , COLLAPSE IT TO THE ACTIVE/CURSOR END
		if len(regions) == 1 and not regions[0].empty():
			position = regions[0].b
			self.view.sel().clear()
			self.view.sel().add(sublime.Region(position))
			return
