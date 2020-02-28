#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" gen_sitemap.py
    Generates a sitemap.xml for cjwelborn.github.io.
    -Christopher Welborn 02-27-2020
"""

import os
import sys
from datetime import datetime

from colr import (
    Colr as C,
    auto_disable as colr_auto_disable,
    docopt,
)
from printdebug import DebugColrPrinter

debugprinter = DebugColrPrinter()
debugprinter.enable(('-D' in sys.argv) or ('--debug' in sys.argv))
debug = debugprinter.debug
debug_err = debugprinter.debug_err

colr_auto_disable()

NAME = 'Static Site Map Generator'
VERSION = '0.0.1'
VERSIONSTR = f'{NAME} v. {VERSION}'
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = f"""{VERSIONSTR}
    Usage:
        {SCRIPT} [-h | -v]
        {SCRIPT} [-D] [INPUT_DIR] [-o file]

    Options:
        INPUT_DIR           : Directory to find html files.
        -o file,--out file  : File for sitemap output.
                              Default: <stdout>
        -D,--debug          : Show more info while running.
        -h,--help           : Show this help message.
        -v,--version        : Show version.
"""

sitemap_template = """<?xml version="1.0" encoding="UTF-8"?>
<urlset
      xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
{urls}
</urlset>
"""

url_template = """<url>
  <loc>{location}</loc>
  <lastmod>{lastmod}</lastmod>
  <priority>{priority}</priority>
</url>
"""


def main(argd):
    """ Main entry point, expects docopt arg dict as argd. """
    return write_sitemap(
        argd['INPUT_DIR'],
        filepath=argd['--out'],
        exclude=('config', '.template')
    )


def get_mod_time(filepath):
    """ Return a file-modification string such as: 2020-02-27T02:23:22+00:00
    """
    if filepath:
        try:
            st = os.stat(filepath)
        except EnvironmentError as ex:
            print_err(f'Failed to get modification time for: {filepath}\n{ex}')
            dt = datetime.today()
        else:
            dt = datetime.fromtimestamp(st.st_mtime)
    else:
        dt = datetime.today()
    return dt.strftime('%Y-%m-%d')


def get_sitemap(rootdir, domain=None, include='.html', exclude=None):
    urls = []
    rootdirlen = len(rootdir)
    domain = domain or 'https://welbornprod.com'
    if '://' not in domain:
        domain = f'https://{domain}'
    # Include the domain itself in urls.
    urls.append(get_url_info(None, url=domain, priority='1.0'))
    for root, dirs, files in os.walk(rootdir):
        urlroot = root[rootdirlen:]
        if exclude and urlroot.endswith(exclude):
            debug(f'Excluding directory: {urlroot}')
            continue
        for filename in files:
            if include and (not filename.endswith(include)):
                continue
            if exclude and filename.endswith(exclude):
                continue
            filepath = os.path.join(root, filename)
            fileurl = '/'.join((urlroot, filename))
            urls.append(get_url_info(
                filepath,
                url=''.join((domain, fileurl)),
                priority=get_url_priority(filepath)
            ))
    return sitemap_template.format(urls='\n'.join(urls))


def get_url_info(filepath, url=None, priority='0.81'):
    """ Get info for the url_template about a file, and return the resulting
        string.
    """
    return url_template.format(
        location=url or filepath,
        lastmod=get_mod_time(filepath),
        priority=priority or '0.81',
    )


def get_url_priority(filepath, default='0.81'):
    pri_map = {
        'development.html': '0.9',
        'downloads.html': '0.9',
        'index.html': '1.0',
        'source.html': '0.5',
        'example.html': '0.5',
        'annotated.html': '0.5',
    }
    pri_map.update({f'_{i}.html': '0.4' for i in range(1, 10)})
    pri_map.update({f'_{s}.html': '0.4' for s in 'abcdefghijklmnopqrstuvwxyz'})

    for ending, pri in pri_map.items():
        if filepath.endswith(ending):
            return pri
    return default


def print_err(*args, **kwargs):
    """ A wrapper for print() that uses stderr by default.
        Colorizes messages, unless a Colr itself is passed in.
    """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr

    # Use color if the file is a tty.
    if kwargs['file'].isatty():
        # Keep any Colr args passed, convert strs into Colrs.
        msg = kwargs.get('sep', ' ').join(
            str(a) if isinstance(a, C) else str(C(a, 'red'))
            for a in args
        )
    else:
        # The file is not a tty anyway, no escape codes.
        msg = kwargs.get('sep', ' ').join(
            str(a.stripped() if isinstance(a, C) else a)
            for a in args
        )

    print(msg, **kwargs)


def write_sitemap(
        rootdir, filepath='sitemap.xml',
        domain=None, include='.html', exclude=None):
    if not rootdir:
        rootdir = os.getcwd()
    mapstr = get_sitemap(
        rootdir,
        domain=domain,
        include=include,
        exclude=exclude,
    )
    if not mapstr:
        print_err('\nNo site map to write!')
        return 1
    if not filepath:
        print(mapstr)
        return 0

    try:
        with open(filepath, 'w') as f:
            f.write(mapstr)
    except EnvironmentError as ex:
        print_err(f'Unable to write sitemap: {ex.filename}\n{ex}')
        return 1
    print(C(': ').join('Wrote sitemap', C(filepath, 'blue')))
    return 0


class InvalidArg(ValueError):
    """ Raised when the user has used an invalid argument. """
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return f'Invalid argument, {self.msg}'
        return 'Invalid argument!'


if __name__ == '__main__':
    try:
        mainret = main(docopt(USAGESTR, version=VERSIONSTR, script=SCRIPT))
    except InvalidArg as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\nUser cancelled.\n')
        mainret = 2
    except BrokenPipeError:
        print_err('\nBroken pipe, input/output was interrupted.\n')
        mainret = 3
    sys.exit(mainret)
