# ./subito/__main__.py
#
# SUBito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Main
# CLI entry point and main program structure.
#

import click
from . import cmds

@click.group()
def cli():
    pass

# TODO: Add all functions from module 'cmds' and add them to cli group!