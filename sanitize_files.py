#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2014-2016 Martin Tournoij <martin@arp242.net>
# See below for full copyright
#
# http://code.arp242.net/sanitize_files
#

from __future__ import print_function
import argparse
import fnmatch
import os
import sys

_verbose = False


def verbose(msg):
    if _verbose:
        print(msg)


def is_binary(data):
    return data.find(b'\000') >= 0


# TODO: we probably also want to process ignore files, like in:
# https://github.com/ggreer/the_silver_searcher/blob/master/src/ignore.c
def should_always_ignore(path):
    keep = [
        # VCS systems
        '/.git', '/.hg', '/.svn', '/CVS',

        # These files have significant whitespace/tabs, and cannot be edited
        # safely
        # TODO: there are probably more of these files..
        'Makefile', 'BSDmakefile', 'GNUmakefile', 'Gemfile.lock'
    ]

    for k in keep:
        if k in path:
            return True
    return False


def run(files, indent_type='tabs', indent_width=4, max_newlines=2):
    if indent_type == 'tabs':
        indent_find = b' ' * indent_width
        indent_replace = b'\t'
    else:
        indent_find = b'\t'
        indent_replace = b' ' * indent_width

    for f in files:
        try:
            size = os.stat(f).st_size
        # Unresolvable symlink, just ignore those
        except FileNotFoundError as exc:
            verbose('%s is unresolvable, skipping (%s)' % (f, exc))
            continue

        if size == 0:
            continue
        if size > 1024 ** 2:
            verbose("Skipping `%s' because it's over 1MiB" % f)
            continue

        try:
            original = open(f, 'rb').read()
        except (OSError, PermissionError) as exc:
            print("Error: Unable to read `%s': %s" % (f, exc))
            continue

        if is_binary(original):
            verbose("Skipping `%s' because it looks binary" % f)
            continue

        new = original.split(b'\n')

        was_dos = False
        fixed_indent = False
        lines_trimmed = 0
        newlines_trimmed = 0
        consec_lines = 0
        for i, line in enumerate(new):
            # Fix \r\n
            if line[-1:] == b'\r':
                was_dos = True
                line = line[:-1]

            # Trim whitespace
            l = len(line)
            line = line.rstrip()
            if len(line) != l:
                lines_trimmed += 1

            # Fix indentation
            repl_count = 0
            while line.startswith(indent_find):
                fixed_indent = True
                repl_count += 1
                line = line.replace(indent_find, b'', 1)

            if repl_count > 0:
                line = indent_replace * repl_count + line

            # Trim newlines
            if line == b'':
                consec_lines += 1
            else:
                consec_lines = 0

            if consec_lines > max_newlines:
                new[i] = None
                newlines_trimmed += 1
            else:
                new[i] = line

        new = list(filter(lambda x: x is not None, new))
        if was_dos:
            verbose('Fixed \\r\\n line endings')
        if fixed_indent:
            verbose('Fixed indentation')
        if lines_trimmed > 0:
            verbose('Trimmed trailing whitespace of %s lines' % lines_trimmed)
        if newlines_trimmed > 0:
            verbose('Removed %s newlines' % newlines_trimmed)
        if new[-1:] != [b'']:
            verbose('Adding newline at end of file')
            new += [b'']

        new = b'\n'.join(new)
        if new != original:
            verbose('Writing %s' % f)
            try:
                open(f, 'wb').write(new)
            except:
                print("Error: Unable to write to `%s': %s" % (f, sys.exc_info()[1]))


def do_add_file(path):
    if should_always_ignore(path):
        verbose('Ignoring %s' % path)
        return False

    for exclude in excludes:
        if fnmatch.fnmatch(path, exclude):
            verbose('Excluding %s' % path)
            return False

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-V', '--verbose', action='store_true',
                        help='enable verbose messages')
    parser.add_argument('-i', '--indent-type', default='tabs',
                        help='indentation type; tabs (default) or spaces')
    parser.add_argument('-w', '--indent-width', type=int, default=4,
                        help='indentation width; defaults to 4')
    parser.add_argument('-m', '--max-newlines', type=int, default=2,
                        help='maximum consecutive newlines; defaults to 2')
    parser.add_argument('-e', '--exclude', nargs='*',
                        help='paths to exclude; simple glob pattern')
    parser.add_argument('paths', nargs='+',
                        help='directories to (recursively) scan for files')
    args = vars(parser.parse_args())

    paths = args['paths']
    del args['paths']

    excludes = args['exclude'] or []
    del args['exclude']

    _verbose = args['verbose']
    del args['verbose']

    if args['indent_type'].lower().startswith('tab'):
        args['indent_type'] = 'tabs'
    elif args['indent_type'].lower().startswith('space'):
        args['indent_type'] = 'space'
    else:
        print("Unknown option `%s' for indent type; valid options are: `tabs' or `spaces'" % args['indent_type'])
        sys.exit(1)

    allfiles = []
    for path in paths:
        if os.path.isfile(path):
            if do_add_file(path):
                allfiles.append(path)
        else:
            for root, dirs, files in os.walk(path):
                for f in files:
                    p = '%s/%s' % (root, f)
                    if do_add_file(p.replace(path, '', 1)):
                        allfiles.append(p)

    run(allfiles, **args)


# The MIT License (MIT)
#
# Copyright © 2014-2016 Martin Tournoij
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and noninfringement. In no event shall the
# authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising
# from, out of or in connection with the software or the use or other dealings
# in the software.
