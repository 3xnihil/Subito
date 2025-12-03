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
import xlsxwriter


def echo_netplan(final_subnets: list[dict]) -> None:
    """
    Display the resulting netplan on terminal's stdout.

    - CAUTION: This function does not verify the validity of its parameters!
    It's meant to process and display already approved contents only!
    :param final_subnets: List containing final subnets with their properties stored in dictionaries, using the keys
        "addr", "mask", "prefix", "first_host_addr", "last_host_addr", "broadcast_addr", "succeeding_addr",
        "max_hosts" and "annotation".
    :return: Nothing.
    """
    click.echo(f"\nSubnetting table for network {final_subnets[0]['addr']}/{final_subnets[0]['prefix']}\n")
    for (n, subnet_config) in enumerate(final_subnets):
        if subnet_config['annotation'] != "":
            annotation_str = f"\n\t(i) {subnet_config['annotation']}\n"
        else:
            annotation_str = f"\n"
        click.echo(
            f"{n+1}. Subnet {subnet_config['addr']}/{subnet_config['prefix']}\n"
            f"\tCapable of {subnet_config['max_hosts']} hosts at max\n"
            f"\tSubnet mask:     {subnet_config['mask']}\n"
            f"\tFirst host addr: {subnet_config['first_host_addr']}\n"
            f"\tLast host addr:  {subnet_config['last_host_addr']}\n"
            f"\tBroadcast addr:  {subnet_config['broadcast_addr']}"
            f"{annotation_str}"
        )
        
        
def save_subnetting_to_spreadsheet(
        filename: str,
        final_subnets: list[dict]) -> None:
    """
    Save a subnetting table stored inside a list of the given structure to a spreadsheet file,
    suitable for further adjustments, annotations and distribution. Resulting file's format is MS Excel,
    which can be opened and edited by basically any spreadsheet application of your choice.
    :param filename: Name given to the spreadsheet file.
    :param final_subnets: List containing final subnets with their properties stored in dictionaries, using the keys
        "addr", "mask", "prefix", "first_host_addr", "last_host_addr", "broadcast_addr", "succeeding_addr",
        "max_hosts" and "annotation".
    :return: Nothing.
    """
    workbook = xlsxwriter.Workbook(f"{filename}.xlsx")
    worksheet = workbook.add_worksheet(name="SUBito netplan")

    col_titles = (
        "Subnet no.", "Network addr.",
        "Max. hosts", "Subnet mask",
        "Prefix", "Hostname",
        "Interface", "IP addr."
    )

    row_titles = (
        "First host", "Last host", "Broadcast"
    )

    # Fill in the titles of the columns, first
    for (col, title) in enumerate(col_titles):
        worksheet.write(0, col, title)

    # We can write down all the networks' data.
    # The dedicated iteration counter vars are really
    # not that elegant, but this may be fixed in future
    # and serves its purpose for now ^^
    k = 0
    for (i, subnet) in enumerate(final_subnets):
        further_addresses = (
            subnet['first_host_addr'],
            subnet['last_host_addr'],
            subnet['broadcast_addr']
        )

        # The subnet's number
        worksheet.write(k + 1, 0, i + 1)

        # The subnet's own address
        worksheet.write(k + 1, 1, subnet['addr'])

        # Maximum host amount for this subnet
        worksheet.write(k + 1, 2, subnet['max_hosts'])

        # Subnet mask
        worksheet.write(k + 1, 3, subnet['mask'])

        # Prefix
        worksheet.write(k + 1, 4, subnet['prefix'])

        # Write the already known "host names"
        for (row, entry) in enumerate(row_titles):
            worksheet.write(k + row + 1, 5, entry)

        # Finally, put in first host, last host and broadcast addresses
        j = 0
        for row in range(k + 1, k + 4):
            worksheet.write(row, 7, further_addresses[j])
            j += 1

        # We have to step over at least three lines in next iteration.
        # Otherwise, two lines of the previous subnet config would
        # become overwritten
        k += 4

    # Important: Finally close the file!
    workbook.close()
    click.echo(f" ✅ Stored your spreadsheet at \"./{filename}.xlsx\"\n")
