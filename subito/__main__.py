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

cli.add_command(cmds.create_netplan)
cli.add_command(cmds.convert)
cli.add_command(cmds.validate)