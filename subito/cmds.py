# ./subito/cmds.py
#
# Subito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Commands
# Functions available via CLI, handled by Click framework.
#

import click
from . import calc
from . import output as out
from . import validation


@click.command()
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
    """
    Create subnetting for a given address space with optional export to a spreadsheet.

    - IP_ADDRESS must be an IPv4 network address given in common decimal octet format.
    Examples: '192.168.23.0', '181.210.8.16', '10.35.7.128' etc.
    Please note that valid network addresses always end with an even octet number!

    - [CONFIG_STRING] has the basic form '<h>:<r>', which stands for a single subnet,
    intended to be capable of a certain count of <h> hosts (placed before colon, where h >= 2)
    and should offer a reserve <r> in percent for future expansion, which may be zero
    if no reserve is desired (placed after colon, where r >= 0).
    This expression can be extended by an optional multiplier <n> preceded by lower char 'x',
    which is to be appended to the basic form;
    resulting in '<h>:<r>x<n>', if a subnet of this type should be implemented for <n> times.

    - [CONFIG_STRING] must be compiled of at least either two basic strings ('<h>:<r> <h>:<r>')
    or a single extended string along with a multiplier ('<h>:<r>x<n>', where n >= 2).

    - Example 1: '300:20 1500:0' aims to create two subnets, one consisting of 300 initial hosts,
    offering a reserve of 30% of the host count, one consisting of 1500 hosts offering no reserve at all

    - Example 2: '200:150x4 2:0x10 4000:10' aims to create 15 subnets, one consisting of 4000 hosts
    offering 10% reserve, four consisting of 200 hosts offering 150% reserve,
    ten peer-to-peer networks (two hosts) offering no reserve.
    """
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
        click.echo(f"\n💥 Sorry, unexpected problem: {e}\n")
        raise SystemExit(3)


@click.command()
@click.argument(
    "mask_or_prefix",
    type=click.STRING,
    nargs=1
)
def convert(mask_or_prefix):
    """
    Convert network prefixes to subnet masks and vice versa.

    - MASK_OR_PREFIX may contain either a subnet mask
    in decimal octet notation (i.e '255.255.224.0', 255.255.0.0')
    OR a network prefix (i.e. '24', '8', '16') to be converted to the opposite format.
    """
    # Determine what kind of data: Prefix or subnet mask?
    if len(mask_or_prefix) < 3 and mask_or_prefix.isdigit() and int(mask_or_prefix) in range(8, 30+1):
        click.echo(f"As a subnet mask: {calc.convert_prefix_to_mask(int(mask_or_prefix))}")
        raise SystemExit(0)
    elif validation.is_netmask_well_formed(mask_or_prefix):
        click.echo(f"As a prefix: /{calc.convert_mask_to_prefix(mask_or_prefix)}")
        raise SystemExit(0)
    else:
        click.echo(f"⚠️ Conversion not possible: Neither a valid prefix nor subnet mask!")
        raise SystemExit(2)


@click.command()
@click.argument(
    "ip_addr",
    type=click.STRING,
    nargs=1
)
@click.option(
    "-p", "--custom-prefix",
    help=f"Helpful if you want to determine the custom domain network of an IP address.",
    type=click.INT,
    nargs=1
)
def inspect(ip_addr, custom_prefix):
    """
    Get detailed info about arbitrary IPv4 addresses.

    - IP_ADDR may contain any valid IPv4 address to inspect
    """
    try:
        is_special_use, is_apt_for_subnetting, description = validation.investigate_special_use(ip_addr)
        addr_class, default_prefix = calc.get_addr_class(ip_addr)
        click.echo(f"\nInspection results for IP {ip_addr}:\n")
        click.echo(
            f"\tAddress class:  {addr_class}"
        )
        if is_special_use:
            click.echo(f"\tSpecial use case: {description}\n")
        # When a class D or E address is provided, 'get_addr_class()' returns a zero prefix, which would
        # lead to misleading error concerning wrong prefix. To prevent that, 'default_prefix' is also checked:
        if default_prefix:
            click.echo(
                f"\tDefault prefix: /{default_prefix}\n"
                f"\tDefault mask:   {calc.convert_prefix_to_mask(default_prefix)}\n"
            )
        if is_apt_for_subnetting and addr_class in "ABC" and custom_prefix and custom_prefix in range(8, 30+1):
            if custom_prefix >= default_prefix:
                ip_addr_int = calc.convert_ip_octet_notation_str_to_int(ip_addr)
                ip_net_addr_int = ip_addr_int & (int('1' * custom_prefix, 2) << 32 - custom_prefix)
                ip_net_addr_str = calc.convert_ip_addr_to_octet_notation_str(ip_net_addr_int)
                click.echo(f"\tNetwork addr: {ip_net_addr_str}/{custom_prefix}\n")
            else:
                click.echo(
                    f"\t⚠️ Cannot determine network address:\n"
                    f"\t Custom prefix must not be smaller than default!\n"
                )
        elif is_apt_for_subnetting and addr_class in "ABC" and custom_prefix and custom_prefix not in range(8, 30+1):
            click.echo(
                f"\t⚠️ Cannot determine network address:\n"
                f"\t Custom prefix is invalid!\n"
            )
        if addr_class not in "ABC":
            click.echo(
                f"\t⚠️ Please note: Address spaces below the classes\n"
                f"\t A, B and C shouldn't be used for subnetting!\n"
            )

    except ValueError as e:
        click.echo(f"⚠️ {e}")
        raise SystemExit(2)

    except Exception as e:
        click.echo(f"💥 Sorry, unexpected problem: {e}")
        raise SystemExit(3)
