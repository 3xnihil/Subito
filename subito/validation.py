# ./subito/validation.py
#
# Subito subnetting tool
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


def investigate_network_block_fit(
        orig_prefix: int,
        required_host_blocks_len: list[int]) -> tuple[bool, list[tuple[int, int, int, int, int]]]:
    """
    Investigate whether a given prefix for arbitrary networks is suitable to provide enough space
    for both given host block lengths in bits and the count of required subnets.
    :param orig_prefix: Prefix of the network, which address space is to be compartmentalized.
    :param required_host_blocks_len: List of host block lengths in bits to be tested whether
        they fit into the subnet portion in question.
        The required amount of host blocks which are to be tested to fit into the same subnet portion in question
        equals the amount of host blocks with the same length inside the list ``required_host_blocks_len``.
    :return: Tuple with test result. If all blocks fit, its first element is True and second element
        is an empty list. If at least a single block collision occurs, its first element is False
        and the second will be a list containing the affected subnets, referenced by a tuple
        consisting of: (1) the subnet sequence number, (2) its host block length, (3) the size of block overlap
        when host block length is exceeded (collision), (4) its subnetting block length and
        (5) the size of block overlap when the count of demanded subnets exceeds the subnetting
        block space available (explosion).
        Examples: Investigation successful: [True, []]
                  Investigation unsuccessful: [False, [(3, 8, 1, 1, 0), (4, 8, 1, 1, 0)]]
                  --> Subnets with sequence numbers 3 and 4 would have issues.
                  Regarding net 3 and 4, host block size is 8 bits, host block collides with
                  network block (overlap of 1 bit), subnetting block size is 1 bit, not exploding
                  because there is no overlap with host block (overlap of 0 bits).
    :except ValueError: If the ``prefix`` is invalid (not between 8 and 30),
        ``required_host_blocks_len`` contains less than 2 entries
        or at least a single host block length is shorter than 2.
    """
    if not orig_prefix in range(8, 31): raise ValueError("Invalid prefix, must keep between 8 and 30!")
    if len(required_host_blocks_len) < 2: raise ValueError("Host block list must provide at least 2 entries!")
    if [block_len < 2 for block_len in required_host_blocks_len].count(True):
        raise ValueError("Every host block length provided inside the list must be at least 2 bits!")

    # First, sort all host blocks from the largest down to the smallest:
    required_host_blocks_len.sort(reverse=True)
    shortest_host_block_len = required_host_blocks_len[-1:][0]
    has_investigation_been_successful = True
    faulty_host_blocks = []

    for (n, required_host_block_len) in enumerate(required_host_blocks_len):
        required_subnets_of_this_type = required_host_blocks_len.count(required_host_block_len)
        required_prefix = 32 - required_host_block_len

        # Network counting starts from zero, so subtract one from required net count to reflect this in bit length!
        required_subnetting_block_len = len(bin(required_subnets_of_this_type - 1)[2:])

        # Available subnetting portion. Network counting starts from zero as well:
        if required_prefix <= orig_prefix:
            available_subnets_of_this_type = 0
            available_subnetting_block_len = 0
        else:
            available_subnets_of_this_type = pow(2, required_prefix - orig_prefix)
            available_subnetting_block_len = len(bin(available_subnets_of_this_type - 1)[2:])

        # Does the required host block fit?
        # ==> If this does not work out, it will affect the first and largest block(s) only:
        if required_prefix < orig_prefix:
            has_investigation_been_successful = False
            host_block_overlap = orig_prefix - required_prefix
            faulty_host_blocks.append(
                (n+1, required_host_block_len, host_block_overlap, available_subnetting_block_len, 0)
            )

        # If host block fits, test if subnet block size is sufficient for the host block count demanded:
        else:
            # As long as fewer subnets are demanded than would be available, it's no problem adding further blocks.
            # If their number equals or even exceeds the space granted by the subnetting block, the journey stops here:
            if ((required_subnets_of_this_type >= available_subnets_of_this_type
                    and required_host_block_len > shortest_host_block_len)
                or (required_subnets_of_this_type > available_subnets_of_this_type
                    and required_host_block_len == shortest_host_block_len)):
                has_investigation_been_successful = False
                subnetting_block_overlap = required_subnetting_block_len - available_subnetting_block_len
                faulty_host_blocks.append(
                    (n+1, required_host_block_len, 0, available_subnetting_block_len, subnetting_block_overlap)
                )

    return has_investigation_been_successful, faulty_host_blocks


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
        If no special use case is found, first bool is False, second is True and the description
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
    return False, True, ""
