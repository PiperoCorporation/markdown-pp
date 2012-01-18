# Copyright (C) 2010 John Reese
# Licensed under the MIT license

import re

from MarkdownPP.Module import Module
from MarkdownPP.Transform import Transform

tocre = re.compile("^!TOC(\s+[1-6])?\s*$")
atxre = re.compile("^(#+)\s*(.+)$")
setextre = re.compile("^(=+|-+)\s*$")

class TableOfContents(Module):
	"""
	Module for auto-generating a table of contents based on the Markdown
	headers in the document.  The table of contents is inserted in the document
	wherever a `!TOC` marker is found at the beginning of a line.
	"""

	def transform(self, data):
		transforms = []

		lowestdepth = 10

		tocfound = False
		toclines = []
		tocdepth = 0
		tocdata = ""

		headers = {}

		# iterate through the document looking for markers and headers
		linenum = 0
		for line in data:

			# !TOC markers
			match = tocre.search(line)
			if match:
				tocfound = True
				depth = match.group(1)
				if depth is not None:
					depth = int(depth)
					tocdepth = max(depth, tocdepth)
				toclines.append(linenum)

			# hash headers
			match = atxre.search(line)
			if match:
				depth = len(match.group(1))
				title = match.group(2).strip()
				headers[linenum] = (depth, title)

				if tocfound:
					lowestdepth = min(depth, lowestdepth)

			# underlined headers
			match = setextre.search(line)
			if match:
				depth = 1 if match.group(1)[0] == "=" else 2
				title = lastline.strip()
				headers[linenum-1] = (depth, title)

				if tocfound:
					lowestdepth = min(depth, lowestdepth)

			lastline = line
			linenum += 1

		# short circuit if no !TOC directive
		if not tocfound:
			return []

		if tocdepth == 0:
			tocdepth = 6

		stack = []
		headernum = 0

		lastdepth = 1
		depthoffset = 1 - lowestdepth

		keys = headers.keys()
		keys.sort()

		# interate through the list of headers, generating the nested table
		# of contents data, and creating the appropriate transforms
		for linenum in keys:
			if linenum < toclines[0]:
				continue

			(depth, title) = headers[linenum]
			depth += depthoffset
			short = re.sub("([\s,-]+)", "", title).lower()

			while depth > lastdepth:
				stack.append(headernum)
				headernum = 0
				lastdepth += 1

			while depth < lastdepth:
				headernum = stack.pop()
				lastdepth -= 1

			headernum += 1

			if depth > tocdepth:
				continue

			if depth == 1:
				section = "%d\\. " % headernum
			else:
				section = ".".join([str(x) for x in stack]) + ".%d\\. " % headernum

			tocdata += "%s [%s](#%s)  \n" % (section, title, short)

			transforms.append(Transform(linenum, "swap", re.sub(title, section + title, data[linenum])))
			transforms.append(Transform(linenum, "prepend", "<a name=\"%s\"></a>\n\n" % short))

		# create transforms for the !TOC markers
		for linenum in toclines:
			transforms.append(Transform(linenum, "swap", tocdata))

		return transforms
