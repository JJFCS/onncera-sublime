
""" COMMENTARY
- THIS FILE CONTAINS ALL COMMON EMACS KEYBINDS THAT DO NOT REQUIRE CONVOLUTED AMOUNTS OF CODE TO IMPLEMENT
"""

import sublime
import sublime_plugin

def seb_deactivate_mark(view):

	""" deactivate the mark and collaspe each selection to its caret (point)
	- this feature is used tandem with c-g and region commands
	"""

	settings  = view.settings()
	selection = view.sel()

	settings.set("onncera_mark_active", False)
	settings.set("onncera_mark_recent", False)
	view.erase_regions("onncera_mark")

	carets = []
	for sel in selection:
		point = sel.b
		if  sel.b > sel.a:
			point = point - 1
		carets.append(point)

	if  carets:
		selection.clear()
		for caret in carets:
			selection.add(caret)


class SebMarkTracker(sublime_plugin.ViewEventListener):

	"""
	- any command other than seb_set_mark breaks the "pressed twice in a row" chain
	- any edit to the buffer deactivates the mark (copy does not edit the buffer but emacs deactivates the mark for it too)
	TODO > how do we extend for future commands besides copy?
	"""

	def on_post_text_command(self, command_name, args):
		if  command_name != "seb_set_mark":
			self.view.settings().set("onncera_mark_recent", False)
		if  command_name == "copy" and self.view.settings().get("onncera_mark_active", False):
			seb_deactivate_mark(self.view)

	def on_modified(self):
		if  self.view.settings().get("onncera_mark_active", False):
			seb_deactivate_mark(self.view)


class SebQuitCommand(sublime_plugin.TextCommand):

	""" emacs c-g
	- A QUIT COMMAND THAT COLLASPE SELECTION(S) TO THE CURSOR AND DEACTIVATE THE MARK
	"""

	def run(self, edit):
		seb_deactivate_mark(self.view)


class SebOpenLineCommand(sublime_plugin.TextCommand):

	""" emacs c-o
	- INSERT A NEWLINE AT THE CURSOR AND LEAVE THE CURSOR WHERE IT WAS , WITHOUT AUTO INDENT
	"""

	def run(self, edit):
		view = self.view
		selection = view.sel()
		points = sorted(r.begin() for r in selection)

		inserts = []
		for point in points:
			line   = view.line(point); text = view.substr(line)
			indent = text[:len(text) - len(text.lstrip(" \t"))]

			column = point - line.begin()
			prefix = indent[:column] if column < len(indent) else indent
			inserts.append("\n" + prefix)

		selection.clear()

		for point, s in zip(reversed(points), reversed(inserts)):
			view.insert(edit, point, s)

		offset = 0
		for point, s in zip(points, inserts):
			selection.add(point + offset)
			offset += len(s)


class SebSetMarkCommand(sublime_plugin.TextCommand):

	""" emacs c-space
	- on first press we set the mark and activate it and movement keys will select
	- on press again we drop the current selection but the mark stays active at the new cursor position
	- on press twice in a row we deactivate the mark and drop the selection
	"""

	def run(self, edit):
		view = self.view
		selection = view.sel()
		settings  = view.settings()

		if  len(selection) == 0:
			return

		# double tap: the previous command was also seb_set_mark
		if  settings.get("onncera_mark_active", False) and settings.get("onncera_mark_recent", False):
			settings.set("onncera_mark_active", False)
			settings.set("onncera_mark_recent", False)
			view.erase_regions("onncera_mark")
			sublime.status_message("Mark deactivated")
			return

		# single tap: collapse the selection to the cursor and (re)set the mark there
		point = selection[-1].b
		selection.clear()
		selection.add(point)

		settings.set("onncera_mark_active", True)
		settings.set("onncera_mark_recent", True)
		sublime.status_message("Mark set")
