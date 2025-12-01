# ./subito/cmds.py
#
# SUBito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Commands
# Functions available via CLI, handled by Click framework.
#

import click
from . import validation
from . import calc


@click.command()
@click.argument(
    "config_string",
    help=f"Basic configuration string group format is 'h:r' or 'h:r(n)', "
         f"where 'h'=host count, 'r'=reserve in %, 'n'=duplicate group n times. "
         f"You can combine multiple elements.",
    type=click.STRING,
    nargs=-1
)
def create_netplan():

    pass


@click.command()
def convert():
    pass


@click.command()
def validate():
    pass