#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" gen_projects.py
    Generates a projects.html page for cjwelborn.github.io
    -Christopher Welborn 08-11-2019
"""

import json
import os
import sys

from colr import (
    Colr as C,
    Preset as ColrPreset,
    auto_disable as colr_auto_disable,
    docopt,
)

from printdebug import DebugColrPrinter
debugprinter = DebugColrPrinter()
debugprinter.enable(('-D' in sys.argv) or ('--debug' in sys.argv))
debug = debugprinter.debug
debug_err = debugprinter.debug_err

colr_auto_disable()

NAME = 'Project Page Generator'
VERSION = '0.0.1'
VERSIONSTR = f'{NAME} v. {VERSION}'
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

REPO_FILE = os.path.join(SCRIPTDIR, 'repos.json')
PROJ_FILE = os.path.join(SCRIPTDIR, 'projects.json')
PAGE_TMP_FILE = os.path.join(SCRIPTDIR, 'projects_template.html')
PROJ_TMP_FILE = os.path.join(SCRIPTDIR, 'project_template.html')
OUTPUT_FILE = os.path.abspath(os.path.join(SCRIPTDIR, '..', 'projects.html'))

USAGESTR = f"""{VERSIONSTR}
    Usage:
        {SCRIPT} -h | -v
        {SCRIPT} [-D] [-q] [-o file | -s]

    Options:
        -D,--debug             : Print some more info while running.
        -h,--help              : Show this help message.
        -o file,--output file  : Output file to use.
                                 Default: {OUTPUT_FILE}
        -q,--quiet             : No status messages.
        -s,--stdout            : Write to stdout.
        -v,--version           : Show version.
"""

SUCCESS_PROJS = 0

CNum = ColrPreset(fore='blue', style='bright')
CFile = ColrPreset(fore='blue')
CLabel = ColrPreset(fore='cyan')


def main(argd):
    """ Main entry point, expects docopt arg dict as argd. """
    global status
    if argd['--quiet']:
        status = noop
    debugprinter.enable(argd['--debug'])

    if argd['--stdout']:
        print(gen_projects_page())
        return 0

    outfile = argd['--output'] if argd['--output'] else OUTPUT_FILE
    with open(outfile, 'w') as f:
        status(C(': ').join('Writing', CFile(outfile)))
        f.write(gen_projects_page())

    status(C(': ').join('Projects generated', CNum(SUCCESS_PROJS)))
    return 0 if SUCCESS_PROJS else 1


def gen_projects_html():
    global SUCCESS_PROJS
    # Info is sorted by stars, watchers, and forks, but it needs to
    # be reversed to put the "best" one on top.
    for info in gen_projects_info_sorted():
        # Add correct urls for a regular non-api page.
        info['starred_url'] = (
            'https://github.com/{full_name}/stargazers'.format(**info)
        )
        info['forked_url'] = (
            'https://github.com/{full_name}/network/members'.format(**info)
        )
        yield PROJ_TEMPLATE.format(**info)
        SUCCESS_PROJS += 1


def gen_projects_info():
    for name in sorted(PROJS['welbornprod']):
        try:
            repoinfo = get_repo_info(name)
            if repoinfo['private'] or repoinfo['disabled']:
                debug(f'Skipping disabled/private repo: {name}')
                continue
        except ValueError:
            # Expected for 'colrc' right now.
            debug_err(f'Missing repo info for: {name}')
            continue
        yield repoinfo


def gen_projects_info_sorted():
    # So glad this works in python.
    yield from reversed(sorted(
        sorted(
            sorted(
                sorted(gen_projects_info(), key=lambda info: info['name']),
                key=lambda info: info['forks_count'],
            ),
            key=lambda info: info['watchers_count'],
        ),
        key=lambda info: info['stargazers_count'],
    ))


def gen_projects_page():
    return PAGE_TEMPLATE.format(projects='\n'.join(gen_projects_html()))


def get_repo_info(name):
    for repoinfo in REPOS:
        if repoinfo['name'] == name:
            return repoinfo
    raise ValueError(f'Repo name not found: {name}')


def noop(*args, **kwargs):
    return None


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


def status(msg, **kwargs):
    if isinstance(msg, C):
        print(msg, **kwargs)
    else:
        print(CLabel(msg), **kwargs)


def try_file_read(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except EnvironmentError as ex:
        print(f'\nUnable to read file: {filepath}\n{ex}', file=sys.stderr)
        sys.exit(1)


def try_json_load(filepath):
    try:
        return json.loads(try_file_read(filepath))
    except json.JSONDecodeError as ex:
        print(f'\nUnable to decode json: {filepath}\n{ex}', file=sys.stderr)
        sys.exit(1)


class InvalidArg(ValueError):
    """ Raised when the user has used an invalid argument. """
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return f'Invalid argument, {self.msg}'
        return 'Invalid argument!'


REPOS = try_json_load(REPO_FILE)
PROJS = try_json_load(PROJ_FILE)
PAGE_TEMPLATE = try_file_read(PAGE_TMP_FILE)
PROJ_TEMPLATE = try_file_read(PROJ_TMP_FILE)


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
