
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

	carets = [sel.b for sel in selection]

	if  carets:
		selection.clear()
		for caret in carets:
			selection.add(caret)


class SebKillLineCommand(sublime_plugin.TextCommand):

	""" emacs c-k
	"""

	def run(self, edit):
		view = self.view

		regions = []
		for selection in view.sel():
			point = selection.b
			line  = view.line(point)

			if   point < line.end():
				 regions.append(
				 	sublime.Region(point, line.end())
				 )
			elif point < view.size():
				 regions.append(
				 	sublime.Region(point, point + 1)
				 )

		if not regions:
			return

		sublime.set_clipboard("\n".join(view.substr(r) for r in regions))
		for region in reversed(regions):
			view.erase(edit, region)


class SebMoveTextCommand(sublime_plugin.TextCommand):

	""" emacs move-text (m-up / m-down)
	- support reindents
	"""

	def run(self, edit, up=True):
		view = self.view
		view.run_command("swap_line_up" if up else "swap_line_down")
		view.run_command("reindent", {"single_line": True})


class SebMarkTracker(sublime_plugin.ViewEventListener):

	"""
	- any command other than seb_set_mark breaks the "pressed twice in a row" chain
	- any edit to the buffer deactivates the mark (copy does not edit the buffer but emacs deactivates the mark for it too)
	TODO > how do we extend for future commands besides copy?
	"""

	KEEP_MARK_COMMANDS, EXTEND_COMMANDS = ("seb_move_text",), ("move", "move_to")

	def on_text_command(self, command_name, args):
		settings = self.view.settings()
		if  command_name in self.KEEP_MARK_COMMANDS:
			settings.set("onncera_keep_marked", True)

		if  command_name in self.EXTEND_COMMANDS and settings.get("onncera_mark_active", False):
			args = dict(args or {})
			if  not args.get("extend", False):
				args["extend"] = True
				return (command_name, args)

	def on_post_text_command(self, command_name, args):
		if  command_name != "seb_set_mark":
			self.view.settings().set("onncera_mark_recent", False)
		if  command_name in self.KEEP_MARK_COMMANDS:
			self.view.settings().set("onncera_keep_marked", False)
		if  command_name == "copy" and self.view.settings().get("onncera_mark_active", False):
			seb_deactivate_mark(self.view)

	def on_modified(self):
		if  self.view.settings().get("onncera_keep_marked", False):
			return
		if  self.view.settings().get("onncera_mark_active", False):
			seb_deactivate_mark(self.view)


class SebQuitCommand(sublime_plugin.TextCommand):

	""" emacs c-g
	"""

	def run(self, edit):
		view      = self.view
		selection = view.sel()

		seb_deactivate_mark(view)

		if  len(selection) > 1:
			carets  = list(selection)
			visible = view.visible_region()
			keep    = next((r for r in reversed(carets) if visible.contains(r.b)), carets[-1])

			selection.clear()
			selection.add(keep)
			view.show(keep)


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

		# single tap: collapse every selection to its own cursor and (re)set the marks there
		carets = [sel.b for sel in selection]

		selection.clear()
		for caret in carets:
			selection.add(caret)

		settings.set("onncera_mark_active", True)
		settings.set("onncera_mark_recent", True)
		sublime.status_message("Mark set")


class SebMoveWordCommand(sublime_plugin.TextCommand):

	""" emacs alt-f & alt-b - AKA M-f & M-b
	"""

	def run(self, edit, forward=True):
		view       = self.view
		selection  = view.sel()
		extend     = view.settings().get("onncera_mark_active", False)
		separators = view.settings().get("word_separators", "")

		regions = []
		for sel in selection:
			point = sel.b

			if  forward:
				point = view.find_by_class(point, True,  sublime.CLASS_WORD_END,   separators)
			else:
				point = view.find_by_class(point, False, sublime.CLASS_WORD_START, separators)

			if  extend:
				regions.append(sublime.Region(sel.a, point))
			else:
				regions.append(sublime.Region(point, point))

		selection.clear()
		for region in regions:
			selection.add(region)

		view.show(selection[-1].b)


class SebMoveParagraphCommand(sublime_plugin.TextCommand):

	""" emacs m-} / m-{ (forward-paragraph / backward-paragraph)
	"""

	def run(self, edit, forward=True):
		view      = self.view
		selection = view.sel()
		extend    = view.settings().get("onncera_mark_active", False)
		last_row  = view.rowcol(view.size())[0]

		def is_blank(row):
			return view.substr(view.line(view.text_point(row, 0))).strip() == ""

		regions = []
		for sel in selection:
			row = view.rowcol(sel.b)[0]

			if  forward:
				while row <= last_row and is_blank(row):
					row += 1
				while row <= last_row and not is_blank(row):
					row += 1
				point = view.size() if row > last_row else view.text_point(row, 0)
			else:
				while row >= 0 and is_blank(row):
					row -= 1
				while row >= 0 and not is_blank(row):
					row -= 1
				point = 0 if row < 0 else view.text_point(row, 0)

			if  extend:
				regions.append(sublime.Region(sel.a, point))
			else:
				regions.append(sublime.Region(point, point))

		selection.clear()
		for region in regions:
			selection.add(region)

		view.show(selection[-1].b)


class SebKillWordCommand(sublime_plugin.TextCommand):

	""" emacs alt-d
	"""

	def run(self, edit):
		view = self.view
		separators = view.settings().get("word_separators", "")

		regions = []
		for selection in view.sel():
			point = selection.b
			end   = view.find_by_class(point, True, sublime.CLASS_WORD_END, separators)

			if  end > point:
				regions.append(sublime.Region(point, end))

		if not regions:
			return

		sublime.set_clipboard("\n".join(view.substr(r) for r in regions))

		for region in reversed(regions):
			view.erase(edit, region)
