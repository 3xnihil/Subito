# ./subito/__main__.py
#
# Subito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Main
# CLI entry point and command provisioning.
#

import click
from . import cmds

@click.group()
def cli():
    """
    Robust, fast and supportive subnetting and network engineering utility.
    Subito aims to help you in creating well-planned and efficient network environments.
    Core features:

    - create-netplan: Cover basic to advanced subnetting scenarios. Tell Subito which and how
    many hosts per network are desired. It will quickly do the maths and calculate whether
    the demanded configuration is sufficient and provide useful feedback if any problems occur.
    If you like, export and save your subnetting to a spreadsheet file easily
    for further adjustment and distribution.

    - inspect: Get detailed technical information about any IPv4 address in question.
    If you have an arbitrary IP address and prefix, but need to know its domain network,
    just provide the address along with the (custom) prefix to get the answer.

    - convert: Need to know the subnet mask for a less common prefix? Just convert it with Subito.
    Vice versa, you can transform prefixes to subnet masks as well.
    """
    pass

cli.add_command(cmds.create_netplan)
cli.add_command(cmds.convert)
cli.add_command(cmds.inspect)
