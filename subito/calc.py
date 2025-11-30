# ./subito/calc.py
#
# SUBito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Calculations
# Contains functions for network calculations.
#

import re
from . import validation
from math import ceil


def get_host_blocks(user_config_str: str, is_binary_block_len: bool=False) -> list[int]:
    """
    From a given user config string, get a list of host counts
    telling how many hosts every demanded subnet should be capable of.
    If an additional flag is set, the function will return the required host block
    size for each subnet.
    :param user_config_str: User configuration string. It has the basic form "h:r",
        which stands for a single subnet, which should be capable of a certain count
        of hosts (digit 'h' before colon, where 'h' >= 2) and should offer a reserve
        in percent for future expansion, which may be zero if no reserve
        is desired (digit 'r' after colon, where 'r' >= 0).
        This expression can be extended by an optional multiplier 'n' put in brackets,
        which is to be appended to the basic form, resulting in "h:r(n)", if a subnet
        of this type should be implemented for 'n' times.
        The config string must contain at least either two basic strings ("h:r h:r")
        or a single extended string along with a multiplier ("h:r(n)", where 'n' >= 1).
        Examples: "300:20 1500:0" --> Two subnets, one consisting of 300 initial hosts,
            offering a reserve of 30% of the host count, one consisting of 1500 hosts
            offering no reserve at all;
            "200:150(4) 2:0(10) 4000:10" --> 15 subnets, one consisting of 4000 hosts
            offering 10% reserve, four consisting of 200 hosts offering 150% reserve,
            ten peer-to-peer networks (two hosts) offering no reserve.
    :param is_binary_block_len: If set to True, the function will return the host
        block sizes in bits each subnet would require.
    :except ValueError: If host count not 'h' >= 2 or multiplier not 'n' >= 1.
    :return: List, containing either final host counts or the required host block sizes
        in bits for each demanded subnet, ordered from the largest down to the smallest.
    """
    config_regex = r"(\d+):(\d+)(?:\((\d+)\))?"
    config_filter = re.compile(config_regex)
    configs_found = config_filter.findall(user_config_str)

    # If there are any matches, continue. Otherwise, return an empty tuple:
    if len(configs_found):
        final_host_blocks = []
        host_configs = [host_config for host_config in configs_found]
        for host_config in host_configs:
            block_multiplier = 1
            initial_host_count = int(host_config[0])
            reserve_percent = int(host_config[1])

            if initial_host_count < 2: raise ValueError("Host count must be at least 2!")
            if host_config[2].isdigit(): block_multiplier = int(host_config[2])
            if block_multiplier < 1: raise ValueError("Block multipliers must be greater than zero!")

            final_host_block = initial_host_count + ceil(initial_host_count * (reserve_percent/100))
            if is_binary_block_len: final_host_block = len(bin(final_host_block)[2:])

            for _ in range(block_multiplier):
                final_host_blocks.append(final_host_block)

        if len(final_host_blocks) < 2: raise ValueError("Provide at least 2 host blocks!")

        # Order final block sizes from largest to smallest:
        final_host_blocks.sort(reverse=True)
        return final_host_blocks

    else:
        raise ValueError("Insufficient configuration string!")


def convert_prefix_to_mask(prefix: int) -> str:
    """
    Convert a prefix to a subnet mask string.
    :param prefix: Network prefix between 8 and 30.
    :except ValueError: If ``prefix`` is not in the valid range.
    :return: Subnet mask string in human-readable octet notation.
    """
    if prefix not in range(8, 31): raise ValueError("Invalid prefix!")
    mask_bin_str = str('1' * prefix).ljust(32, '0')
    octets = [str(int(mask_bin_str[n:n+8], 2)) for n in range(0, 25, 8)]
    return ".".join(octets)


def convert_mask_to_prefix(mask: str) -> int:
    """
    Convert a subnet mask string to a prefix.
    :param mask: Subnet mask string, in human-readable octet notation.
        Examples: "255.192.0.0"; "255.255.255.0"
    :except ValueError: If ``mask`` is not valid.
    :return: Network prefix.
        Examples: 10; 24
    """
    if not validation.is_netmask_well_formed(mask): raise ValueError("Invalid subnet mask!")
    mask_filter = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
    mask_bin_str = ''.join([bin(int(octet))[2:] for octet in mask_filter.findall(mask)[0]])
    return mask_bin_str.count('1')


def get_addr_class(ip: str) -> tuple[str, int]:
    """
    Get the address class of an IP address, according to the first bits
    of the first address octet:

        - A: Bit 1, ``0``
        - B: Bits 1-2, ``10``
        - C: Bits 1-3, ``110``
        - D (Multicast): Bits 1-4, ``1110``
        - E (Scientific): Bits 1-4, ``1111``

    :param ip: IP address string, human-readable octet format.
    :except ValueError: If the IP address is not valid.
    :return: Tuple, containing the class letter ("A"; "B"; ...; "E")
        and the default prefix of this address class.
        -- Please note: As classes D and E don't have commonly associated
        prefixes and should only be used if one knows what s:he is doing,
        the function will return a prefix of zero in this case!
    """
    if not validation.is_ipaddr_well_formed(ip): raise ValueError("Invalid IP address!")
    ip_filter = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
    ip_bin_str = ''.join([bin(int(octet))[2:] for octet in ip_filter.findall(ip)[0]])
    prefix = 0
    first_nibble_bin_str = ip_bin_str[:4]
    if first_nibble_bin_str[0] == '0': addr_class = "A"; prefix = 8
    elif first_nibble_bin_str[:2] == '10': addr_class = "B"; prefix = 16
    elif first_nibble_bin_str[:3] == '110': addr_class = "C"; prefix = 24
    elif first_nibble_bin_str == '1110': addr_class = "D"
    else: addr_class = "E"
    return addr_class, prefix


def create_subnets(
        orig_ip: str,
        host_blocks_len: list[int]) -> list[tuple[str, str, str, str, str, str, str, str]]:
    """
    Perform actual subnetting on a given network and create a list of final subnets
    if the demanded host blocks all fit into.
    :param orig_ip: Original networks IP address string.
        Example: "142.212.80.8"
    :param host_blocks_len: List of host blocks demanded. Its length determines how
        many subnets are required.
    :except ValueError: Insufficient host block list. Less than 2 entries
        in ``host_blocks_len``.
    :except UserWarning: Subnetting could not be achieved because host block list
        leads to block collisions. ``host_blocks_len`` contains too many
        and / or too large blocks such that network and host blocks don't fit all in,
        or the original network defined by ``orig_ip`` cannot provide enough space (it depends on
        how a user weighs the aspects at all). Will also be raised if user tries
        to use an address from a reserved space (see RFC7535).
    :return: List containing final subnets with their properties stored inside a tuple
        of the form ("<subnet IP addr>", "<subnet mask>", "<prefix>",
        "<first host IP addr>", "<last host IP addr>",
        "<broadcast IP addr>", "<succeeding subnet IP addr>").
    """

