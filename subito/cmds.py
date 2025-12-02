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
import calc
import output as out


@click.command(
    help=f"IP_ADDRESS must be an IPv4 network address given in common decimal octet format. "
         f"Examples: '192.168.23.0', '181.210.8.16', etc. "
         f"Please note that for network addresses, the last octet MUST always be an even number! "
         f"[CONFIG_STRING] must consist of has the basic form '<h>:<r>', "
         f"which stands for a single subnet, which should be capable of a certain count "
         f"of hosts (digit <h> before colon, where h >= 2) and should offer a reserve "
         f"in percent for future expansion, which may be zero if no reserve "
         f"is desired (digit <r> after colon, where r >= 0). "
         f"This expression can be extended by an optional multiplier <n> preceded by lower char 'x', "
         f"which is to be appended to the basic form, resulting in '<h>:<r>x<n>', if a subnet "
         f"of this type should be implemented for <n> times. "
         f"The config string must contain at least either two basic strings ('<h>:<r> <h>:<r>') "
         f"or a single extended string along with a multiplier ('<h>:<r>x<n>', where n >= 2). "
         f"Examples: '300:20 1500:0' aims to create two subnets, one consisting of 300 initial hosts, "
         f"offering a reserve of 30% of the host count, one consisting of 1500 hosts "
         f"offering no reserve at all; "
         f"'200:150x4 2:0x10 4000:10' aims to create 15 subnets, one consisting of 4000 hosts "
         f"offering 10% reserve, four consisting of 200 hosts offering 150% reserve, "
         f"ten peer-to-peer networks (two hosts) offering no reserve."
)
@click.argument(
    "ip-address",
    type=click.STRING,
    nargs=1
)
@click.argument(
    "config_string",
    type=click.STRING,
    nargs=-1
)
@click.option(
    "-s", "--save-spreadsheet",
    help=f"Save netplan in a spreadsheet file with custom name for TEXT.",
    type=click.STRING
)
def create_netplan(config_string, ip_address, save_spreadsheet):
    # Caution: 'config_string' itself is a tuple, due to 'nargs=-1'!
    config_str = ", ".join(config_string)
    try:
        demanded_host_blocks = calc.get_host_blocks(config_str)
        subnets = calc.create_subnets(ip_address, demanded_host_blocks)
        out.echo_netplan(subnets)
        if save_spreadsheet:
            out.save_subnetting_to_spreadsheet(save_spreadsheet, subnets)

    except ValueError as e:
        click.echo(f"{e}\nPlease consult '--help' option to show usage.\n")
        raise SystemExit(2)

    except UserWarning as e:
        click.echo(f"\n⚠️ {e}\n")
        raise SystemExit(1)

    except Exception as e:
        click.echo(f"\n💥 Sorry, undefined problem: {e}\n")
        raise SystemExit(3)


@click.command()
def convert():
    pass


@click.command()
def validate():
    pass