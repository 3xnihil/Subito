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
import validation
from math import ceil


def get_host_blocks(user_config_str: str, is_binary_block_len: bool=True) -> list[int]:
    """
    From a given user config string, get a list of host blocks
    telling how many hosts every demanded subnet should be capable of.
    If block-length flag becomes unset, the function will return the required absolute host block
    amounts for each subnet.
    :param user_config_str: User configuration string. It has the basic form "<h>:<r>",
        which stands for a single subnet, which should be capable of a certain count
        of hosts (digit 'h' before colon, where 'h' >= 2) and should offer a reserve
        in percent for future expansion, which may be zero if no reserve
        is desired (digit 'r' after colon, where 'r' >= 0).
        This expression can be extended by an optional multiplier 'n' preceded by lower char "x",
        which is to be appended to the basic form, resulting in "<h>:<r>x<n>", if a subnet
        of this type should be implemented for 'n' times.
        The config string must contain at least either two basic strings ("<h>:<r> <h>:<r>")
        or a single extended string along with a multiplier ("<h>:<r>x<n>", where 'n' >= 2).
        Examples: "300:20 1500:0" --> Two subnets, one consisting of 300 initial hosts,
            offering a reserve of 30% of the host count, one consisting of 1500 hosts
            offering no reserve at all;
            "200:150x4 2:0x10 4000:10" --> 15 subnets, one consisting of 4000 hosts
            offering 10% reserve, four consisting of 200 hosts offering 150% reserve,
            ten peer-to-peer networks (two hosts) offering no reserve.
    :param is_binary_block_len: Defaults to True. If set to False, the function will return the host
        counts rather than block sizes in bits each subnet would require.
    :except ValueError: If host count not 'h' >= 2 or multiplier not 'n' >= 1.
    :return: List, containing either demanded host block sizes in bits or the demanded host count
        for each subnet, ordered from the largest down to the smallest.
    """
    config_regex = r"(\d+):(\d+)(?:x(\d+))?"
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
    prefix = 0
    if not validation.is_ipaddr_well_formed(ip): raise ValueError("Invalid IP address!")
    ip_filter = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
    first_octet_bin_str = bin(int(ip_filter.findall(ip)[0][0]))[2:].rjust(8, '0')
    first_nibble_bin_str = first_octet_bin_str[:4]
    if first_nibble_bin_str[0] == '0': addr_class = "A"; prefix = 8
    elif first_nibble_bin_str[:2] == '10': addr_class = "B"; prefix = 16
    elif first_nibble_bin_str[:3] == '110': addr_class = "C"; prefix = 24
    elif first_nibble_bin_str == '1110': addr_class = "D"
    else: addr_class = "E"
    return addr_class, prefix


def convert_ip_addr_to_octet_notation_str(ip) -> str:
    """
    Convert an IPv4 address from either binary string or integer format into
    the commonly known and human-readable octet string notation.
    :param ip: IP address, either encoded into an integer or binary string.
    :except TypeError: If ``ip`` is neither an integer nor a string.
    :except ValueError: If ``ip`` does neither resemble a valid IP address
        in integer nor in binary string encoding.
    :return: IP address string in octet notation.
    """
    if not (isinstance(ip, int) or isinstance(ip, str)):
        raise TypeError("Param 'ip' must either be of type 'int' or 'str'!")
    if isinstance(ip, str) and not (len(ip) == 32 and len(set(ip)) == 2 and ('1' and '0' in set(ip))):
        raise ValueError("Param 'ip' is not a valid binary IP string!")
    if isinstance(ip, int) and not (len(bin(ip)[2:].rjust(32, '0')) == 32 and ip >= 0):
        raise ValueError("Param 'ip' is not a valid IP integer!")

    ip_addr_octet_str = ""
    if isinstance(ip, str):
        octets = [str(int(ip[n:n + 8], 2)) for n in range(0, 24 + 1, 8)]
        ip_addr_octet_str = '.'.join(octets)
    if isinstance(ip, int):
        ip_addr_bin_str = bin(ip)[2:].rjust(32, '0')
        octets = [str(int(ip_addr_bin_str[n:n + 8], 2)) for n in range(0, 24 + 1, 8)]
        ip_addr_octet_str = '.'.join(octets)
    return ip_addr_octet_str


def convert_ip_octet_notation_str_to_int(ip: str) -> int:
    """
    Convert an IPv4 octet notation string to its numerical integer representation to calc with.
    :param ip: IP address string in decimal octet notation.
    :except ValueError: If IP address string is malformed.
    :return: Numerical value of this IP address as an integer.
    """
    if not validation.is_ipaddr_well_formed(ip): raise ValueError("Invalid IP address!")
    ip_filter = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
    ip_bin_str = ''.join([bin(int(octet))[2:].rjust(8, '0') for octet in ip_filter.findall(ip)[0]])
    return int(ip_bin_str, 2)


def create_subnets(
        orig_ip: str,
        host_blocks_len: list[int]) -> list[dict]:
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
        to use an address from a space of special use not suitable for subnetting (see RFC 7535,
        https://www.rfc-editor.org/rfc/rfc5735#section-4).
    :except ValueError: If IP address octet string, ``orig_ip``, is invalid or if
        the last octet of ``orig_ip`` is not an even number (ends with zero in binary)
        and therefore is not a valid network address.
    :return: List containing final subnets with their properties stored in dictionaries, using the keys
        "addr", "mask", "prefix", "first_host_addr", "last_host_addr", "broadcast_addr", "succeeding_addr",
        "max_hosts" and "annotation".
    """
    final_subnets = []
    annotation = ""

    # First check: Address suitable for subnetting at all?
    is_special_use_case, is_apt_for_subnetting, description = validation.investigate_special_use(orig_ip)
    if is_special_use_case and not is_apt_for_subnetting:
        raise UserWarning(f"Address reserved for special purpose: {description}")
    elif is_special_use_case and is_apt_for_subnetting:
        annotation = f"Will not be routed: {description}"
    orig_addr_class, orig_prefix = get_addr_class(orig_ip)
    if orig_addr_class not in "ABC":
        raise UserWarning(f"Addresses aside the classes A, B and C shouldn't be used for subnetting!")

    # If suitable, test if all blocks will fit:
    do_all_blocks_fit, faulty_blocks = validation.investigate_network_block_fit(orig_prefix, host_blocks_len)
    if not do_all_blocks_fit:
        faulty_subnets_descriptions = [
            f"{faulty_block[0]}. Subnet: {pow(2, faulty_block[1])-2} hosts max\n"
            f"\thost portion: BS={faulty_block[1]} bits, "
            f"{faulty_block[2]} bits colliding with network portion\n"
            f"\tsubnet portion: BS={faulty_block[3]} bits, "
            f"{faulty_block[4]} bits exploding\n"
            for faulty_block in faulty_blocks
        ]
        err_description = f"Sorry, some of your demanded subnets for network {orig_ip}/{orig_prefix} "\
                          f"(class {orig_addr_class}) won't fit!\nPlease investigate the messages below:\n"\
                          f"\n{'\n'.join(faulty_subnets_descriptions)}\n"\
                          f"(i) For class C networks, you most likely ran out of host block space.\n"\
                          f" A 'subnet portion: BS=0 bits' means that the host block size is too large,\n"\
                          f" preventing the creation of subnets at all.\n"\
                          f" More than zero 'bits exploding' means you ran out of subnetting block space.\n"
        raise UserWarning(err_description)

    # Everything is fine, so let's perform the actual subnetting:
    else:
        # Convert IP string to binary. Only even IP addresses are valid network addresses:
        ip_filter = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        orig_ip_bin_str = ''.join([bin(int(octet))[2:].rjust(8, '0') for octet in ip_filter.findall(orig_ip)[0]])
        if orig_ip_bin_str[-1:] == '1': raise ValueError(
            "The last octet of a valid network address must be an even number (ends with zero in binary)!"
        )
        # Internally, it's best to calculate with actual numeric values of IP addresses
        current_ip_addr_int = int(orig_ip_bin_str, 2)
        host_blocks_len.sort(reverse=True)

        for (n, demanded_host_block_len) in enumerate(host_blocks_len):
            subnet_host_count = pow(2, demanded_host_block_len) - 2
            subnet_addr_int = current_ip_addr_int
            subnet_succeeding_addr_int = subnet_addr_int + pow(2, demanded_host_block_len)
            subnet_prefix = 32 - demanded_host_block_len
            subnet_first_host_addr_int = subnet_addr_int + 1
            subnet_last_host_addr_int = subnet_succeeding_addr_int - 2
            subnet_broadcast_addr_int = subnet_succeeding_addr_int - 1
            current_ip_addr_int += pow(2, demanded_host_block_len)
            # Convert these subnet properties into human-readable octet format:
            subnet_addr_str = convert_ip_addr_to_octet_notation_str(subnet_addr_int)
            subnet_first_host_addr_str = convert_ip_addr_to_octet_notation_str(subnet_first_host_addr_int)
            subnet_last_host_addr_str = convert_ip_addr_to_octet_notation_str(subnet_last_host_addr_int)
            subnet_broadcast_addr_str = convert_ip_addr_to_octet_notation_str(subnet_broadcast_addr_int)
            subnet_succeeding_addr_str = convert_ip_addr_to_octet_notation_str(subnet_succeeding_addr_int)
            subnet_mask_str = convert_prefix_to_mask(subnet_prefix)
            final_subnets.append(
                {
                    "addr": subnet_addr_str, "mask": subnet_mask_str, "prefix": str(subnet_prefix),
                    "first_host_addr": subnet_first_host_addr_str, "last_host_addr": subnet_last_host_addr_str,
                    "broadcast_addr": subnet_broadcast_addr_str, "succeeding_addr": subnet_succeeding_addr_str,
                    "max_hosts": str(subnet_host_count), "annotation": annotation
                }
            )
        return final_subnets