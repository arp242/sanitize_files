#!/usr/bin/env python
# encoding: utf-8

import tempfile, subprocess

from sanitize_files import run

def contents_is(fp, expect, desc, opt={}):
	fp.flush()
	run([fp.name], **opt)
	fp.seek(0)

	content = fp.read()

	try:
		assert content == expect, "%s: %s" % (desc, content)
	except AssertionError as e:
		print('Error: %s' % desc)
		print('  Expected: %s' % repr(expect))
		print('  Actual:   %s' % repr(content))
	else:
		print('Okay: %s' % desc)

with tempfile.NamedTemporaryFile() as fp:
	fp.write(b'Hello\nWorld')
	contents_is(fp, b'Hello\nWorld\n', 'Adds a newline to the end of the file')

with tempfile.NamedTemporaryFile() as fp:
	fp.write(b'Hello\r\nWorld\r\n')
	contents_is(fp, b'Hello\nWorld\n', 'Converts DOS line endings to UNIX line endigs')

with tempfile.NamedTemporaryFile() as fp:
	fp.write(b'\tHello\n\t\tW\to    rld\n')
	contents_is(fp, b'    Hello\n        W\to    rld\n', 'Converts tabs to spaces',
		{'indent_type': 'spaces'})

with tempfile.NamedTemporaryFile() as fp:
	fp.write(b'    Hello\n        W    o\trld\n')
	contents_is(fp, b'\tHello\n\t\tW    o\trld\n', 'Converts spaces to tabs',
		{'indent_type': 'tabs'})

with tempfile.NamedTemporaryFile() as fp:
	fp.write(b'Hello\n\n\n\nWorld\nHello\nWorld\n \n    \n\t\nxxx\n')
	contents_is(fp, b'Hello\n\n\nWorld\nHello\nWorld\n\n\nxxx\n', 'Removes consecutive newlines')

with tempfile.NamedTemporaryFile() as fp:
	fp.write(b'Hello     \nWorld\t\t\n')
	contents_is(fp, b'Hello\nWorld\n', 'Removes trailing whitespace')
