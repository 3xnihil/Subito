# ./subito/output.py
#
# SUBito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Output
# Display outputs of the tool via Click's echo command.
#

import click


def echo_netplan(final_subnets: list[tuple[str, str, str, str, str, str, str, str, str]], orig_prefix: int) -> None:
    """
    Display the resulting netplan on terminal's stdout.

    - CAUTION: This function does not verify the validity of its parameters!
    It's meant to process and display already approved contents only!
    :param final_subnets: List containing final subnets with their properties
        stored as strings inside a tuple of the form ("<subnet IP addr>", "<subnet mask>", "<prefix>",
        "<first host IP addr>", "<last host IP addr>", "<broadcast IP addr>",
        "<succeeding subnet IP addr>", "<max host count>", "<annotation (if any, otherwise empty string)>").
    :param orig_prefix: Original prefix of the network which has been subnetted.
    :return: Nothing.
    """
    click.echo(f"Subnetting table for network {final_subnets[0][0]}/{orig_prefix}")
    for (n, subnet_config) in enumerate(final_subnets):
        if subnet_config[8] != "":
            annotation_str = f"\n\t(i) {subnet_config[8]}\n"
        else:
            annotation_str = f"\n"
        click.echo(
            f"{n+1}. Subnet {subnet_config[0]}/{subnet_config[2]}\n"
            f"\tCapable of {subnet_config[7]} hosts at max\n"
            f"\tSubnet mask:     {subnet_config[1]}\n"
            f"\tFirst host addr: {subnet_config[3]}\n"
            f"\tLast host addr:  {subnet_config[4]}\n"
            f"\tBroadcast addr:  {subnet_config[5]}"
            f"{annotation_str}"
        )
