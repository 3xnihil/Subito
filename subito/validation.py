# ./subito/validation.py
#
# SUBito subnetting tool
# Author: Johannes Hüffer
# License: GPL-3.0-only
#
# Validation
# Verify input values for plausibility and correct format.
#

import re


def is_ipaddr_well_formed(ipaddr: str) -> bool:
    """
    Check if a given string fulfills
    all criteria to be considered a valid IP address.
    :param ipaddr: IP address, in human-readable octet format.
        Examples: "172.16.10.32"; "210.200.345.116"
    :return: Status whether the string is a valid
        IP address (True) or not (False).
    """
    ipaddr_regex = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    ipaddr_filter = re.compile(ipaddr_regex)
    octets_found = ipaddr_filter.findall(ipaddr)
    if len(octets_found):
        ip_addr_bin_str = ''.join(
            [bin(int(octet))[2:].rjust(8, '0') for octet in octets_found[0]]
        )
        # If any of the octets exceeds its max value of 255, the resulting binary string will
        # simply become longer than 32 bits:
        return len(ip_addr_bin_str) == 32
    # Expression did not even meet basic octet format:
    return False


def is_netmask_well_formed(netmask: str) -> bool:
    """
    Check if a given subnet mask is valid and applicable.
    :param netmask: Subnet mask, in human-readable octet format.
        Examples: "255.255.192.0"; "255.255.255.252"
        Please note: In special cases, prefix /31 resp. mask "255.255.255.253"
            could be used when configuring point-to-point connections.
            This is not covered by this net planning tool, however!
    :return: Status whether the string is a valid subnet mask (True)
        or not (False).
    """
    netmask_regex = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    netmask_filter = re.compile(netmask_regex)
    octets_found = netmask_filter.findall(netmask)
    if len(octets_found):
        netmask_bin_str = ''.join(
            [bin(int(octet))[2:].rjust(8, '0') for octet in octets_found[0]]
        )
        for (n, current_bit) in enumerate(netmask_bin_str):
            if n < (len(netmask_bin_str) - 1):
                next_bit = netmask_bin_str[n+1]
                # In a valid subnet mask, a zero bit is never followed by a one bit again:
                if not int(current_bit) and int(next_bit):
                    return False
        # Valid subnet mask is exactly 32 bit long and has a prefix value 8 <= prefix <= 30:
        return (len(netmask_bin_str) == 32
                and netmask_bin_str.count('1') in range(8, 30+1))
    # Expression did not even meet basic octet format:
    return False


def do_blocks_fit_inside_network(prefix: int, host_blocks_len: list[int]) -> tuple[bool, list[tuple[int, int]]]:
    """
    Investigate whether a given prefix for arbitrary networks is suitable to provide enough space
    for both given host block lengths in bits and the count of required subnets.
    :param prefix: Prefix of the network, which address space is to be compartmentalized.
    :param host_blocks_len: List of hostblock lengths in bits to be tested whether they fit in.
        The list's length implies the count of subnets which would be necessary.
    :return: Tuple with test result. If all blocks fit, its first element is True and second element
        is an empty list. If at least a single block collision occurs, its first element is False
        and the second will be a list containing the affected subnets, referenced by a tuple
        consisting of (1) the subnet's number and (2) its block length.
        Examples: Investigation successful: [True, []]
                  Investigation unsuccessful: [False, [(2, 8), (3, 8)]]; subnet 2 with a host
                  block size of 8 bits and subnet 3 with a host block size of 8 bits are faulty.
    :except ValueError: If there are less than 2 entries inside ``host_blocks_len``
        or the ``prefix`` is invalid (not between 8 and 30).
    """
    if not prefix in range(8, 31): raise ValueError("Invalid prefix, must keep between 8 and 30!")
    if len(host_blocks_len) < 2: raise ValueError("Provide at least 2 host blocks!")

    # First, make sure the blocks are in the right order from largest to smallest:
    host_blocks_len.sort(reverse=True)
    faulty_host_blocks = []

    # Calculate subnetting block size. Important: Subtract one from the host blocks' list's length,
    # because the subnet block starts counting at zero (i.e. two subnets require a single subnetting bit).
    subnet_block_len = len(bin(len(host_blocks_len)-1)[2:])
    network_block_len = prefix + subnet_block_len

    # Now, check each host block against the network block. If both exceed 32 bits address space,
    # subnetting will not work out for this config!
    for (n, host_block_len) in enumerate(host_blocks_len):
        total_block_len = network_block_len + host_block_len
        if total_block_len > 32: faulty_host_blocks.append((n+1, host_block_len))

    do_all_blocks_fit = len(faulty_host_blocks) == 0
    return do_all_blocks_fit, faulty_host_blocks


def investigate_special_use(ip: str) -> tuple[bool, bool, str]:
    """
    Check if a given network address belongs to a special use case
    according to RFC 5735 (see https://www.rfc-editor.org/rfc/rfc5735#section-4).
    :param ip: IP address string, human-readable octet format.
    :except ValueError: If IP address string is malformed.
    :return: Tuple containing the investigation's result of the form
        (<bool is_special_use_net>, <bool is_apt_for_subnetting>, <str special_use_description>).
        First element is True if the IP address in question belongs to a special use case,
        second element is True if the IP address is still suitable for subnetting (RFC1918 only),
        along with third string element describing what kind of use case.
        If no special use case is found, first and second bool will be False and the description
        string remains empty.
    """
    if not is_ipaddr_well_formed(ip): raise ValueError("Invalid IP address!")
    ipaddr_regex = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    ipaddr_filter = re.compile(ipaddr_regex)
    octets = [int(octet) for octet in ipaddr_filter.findall(ip)[0]]
    user_ip_bin_str = ''.join([bin(octet)[2:].rjust(8, '0') for octet in octets])
    user_ip_int = int(user_ip_bin_str, 2)

    # (<octets of special use net>): (<prefix>, <apt for subnetting>, "<description>")
    special_use_networks = {
        (0,0,0,0): (8, False, f"\"This\" Network (RFC 1122, Section 3.2.1.3)"),
        (10,0,0,0): (8, True, f"Private-Use Networks (RFC 1918)"),
        (127,0,0,0): (8, False, f"Loopback (RFC 1122, Section 3.2.1.3)"),
        (169,254,0,0): (16, False, f"Link Local (RFC 3927)"),
        (172,16,0,0): (12, True, f"Private-Use Networks (RFC 1918)"),
        (192,0,0,0): (24, False, f"IETF Protocol Assignments (RFC 5736)"),
        (192,0,2,0): (24, False, f"TEST-NET-1 (RFC 5737)"),
        (192,88,99,0): (24, False, f"6to4 Relay Anycast (RFC 3068)"),
        (192,168,0,0): (16, True, f"Private-Use Networks (RFC 1918)"),
        (198,18,0,0): (15, False, f"Network Interconnect Device Benchmarking Testing (RFC 2544)"),
        (198,51,100,0): (24, False, f"TEST-NET-2 (RFC 5737)"),
        (203,0,113,0): (24, False, f"TEST-NET-3 (RFC 5737)"),
        (224,0,0,0): (4, False, f"Multicast (RFC 3171)"),
        (240,0,0,0): (4, False, f"Reserved for Future Use (RFC 1112, Section 4)"),
        (255,255,255,255): (32, False, f"Limited Broadcast (RFC 919, Section 7; RFC 922, Section 7)")
    }

    # Convert octet tuple to binary. We can then use the prefix of the special-use network
    # to bitwise-And with the binary value of the IP address given by the user to find out
    # if network provided coincides with one of these special-use networks.
    # ==> This is to be done for each special-use network:
    for special_use_octet_tuple in special_use_networks.keys():
        ip_addr_bin_str = ''.join([bin(octet)[2:].rjust(8, '0') for octet in special_use_octet_tuple])
        prefix_bin_str = str('1' * special_use_networks.get(special_use_octet_tuple)[0]).ljust(32, '0')
        special_use_ip_addr_int = int(ip_addr_bin_str, 2)
        special_use_prefix_int = int(prefix_bin_str, 2)
        user_net_ip_addr_int = user_ip_int & special_use_prefix_int
        # IP address given by user matches a special-use network address portion:
        if user_net_ip_addr_int == special_use_ip_addr_int:
            return (
                True,   # Flag: Is special use network
                special_use_networks.get(special_use_octet_tuple)[1],   # Flag: Is apt for subnetting
                special_use_networks.get(special_use_octet_tuple)[2]    # Description: What kind of special-use
            )
    # IP address given by user does not match any special-use network address portion:
    return False, False, ""

