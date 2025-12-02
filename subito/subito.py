# ./subito/subito.py
#
# SUBito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Main
# CLI entry point and main program structure.
#

import click
import cmds

@click.group(
    help=f"Bare-metal subnetting and network engineering utility."
)
def cli():
    pass

cli.add_command(cmds.create_netplan)
cli.add_command(cmds.convert)
cli.add_command(cmds.inspect)

# TODO: Remove this entry point before starting the build!
if __name__ == '__main__':
    cli()