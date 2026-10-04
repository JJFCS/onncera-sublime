
""" COMMENTARY
- THIS FILE CONTAINS ALL COMMON EMACS KEYBINDS THAT DO NOT REQUIRE CONVOLUTED AMOUNTS OF CODE TO IMPLEMENT
"""

import sublime
import sublime_plugin

class SebQuitCommand(sublime_plugin.TextCommand):

	""" emacs c-g
	- A QUIT COMMAND THAT COLLASPE SELECTION(S) TO THE CURSOR AND DEACTIVATE THE MARK
	- TODO > implement setting the mark and deactivating it
	"""

	def run(self , edit):
		selection = self.view.sel()

		if len(selection) == 0:
			return

		carets = []
		for sel in selection:
			point = sel.b
			if sel.b > sel.a:
				point = point - 1
			carets.append(point)

		selection.clear()
		for caret in carets:
			selection.add(caret)
