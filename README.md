# Subito: CLI subnetting utility

 **Fast, robust and supportive subnetting and network engineering utility.
 Subito aims to help you in creating well-planned and efficient IPv4 network environments.**

---

## 🎯 Topics

- [Why Subito?](#why-subito)
- [Get ready](#get-ready)
- [Commands](#-commands)
- [Usage](#usage)
- [Error Handling](#error-handling)
- [Final Thoughts](#final-thoughts)
- [Acknowledgments](#-acknowledgements)

---

## Why Subito?

**Subito** (lat. _"instantly", "sudden"_) aims to be a fast, simple and straightforward subnetting utility.
It comes with these **main benefits**:

* 🐍 **Based on Python** and the awesome **[Click framework](https://click.palletsprojects.com/en/stable/)**
* 🎒 **Small code base**, [thanks](#acknowledgements) to Click!
* ✅ **Fully Open Source** and well documented
* 🌱 **Efficient** Command Line Interface
* ℹ️ **Informative feedback** when things get tricky
* ⚙️ **Takes [IETF RFCs](https://www.ietf.org/process/rfcs/) into account** to grant practicability
* ➡️ **Easily export subnet plans** to a pre-formatted [spreadsheet file](#acknowledgements)

---

## Get ready

### 🛠️ Requirements

- **Recent Python** version (_3.10_+)
- Any **POSIX-compatible** environment (_GNU+Linux, macOS, *BSD, WSL_ etc.)

### 🏗️ Install from Source

🚧 _Currently, this is the only install method available, but a **PyPI package will be released soon!**_

1. **Clone** this repo:
    ```bash
   git clone https://github.com/3xnihil/subito.git
    ```
2. **Change** into the repo's dir:
    ```bash
   cd subito
    ```
3. **Create** a Python virtual environment and use it:
    ```bash
   python -m venv .subito-venv
   source .subito-venv/bin/activate
    ```
4. **Install Subito** inside the virtual environment:
    ```bash
   # Bring pip to the latest version first
   pip install --upgrade pip
   
   # Now install Subito along with its dependencies
   pip install .
   
   # If you want to keep the source files editable
   pip install -e .
    ```

---

## 🌰 Commands

| Command                                                                                | Explanation                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `subito create-netplan <ipv4 network address> <config string> [-s <spreadsheet file>]` | _Subito's_ main feature. If you want to **create subnets inside a given address space**,<br/>**1)** provide the space's `ipv4 network address`,<br/>**2)** a `config string` describing each subnet's demanded host capabilities and<br/>**3)** optionally, whether the final subnetting should be exported to a `spreadsheet file`.<br/>**[A detailed explanation on how to create Config Strings](#create-subnets-using-config-strings)** you will find in the next section. |
| `subito inspect <ipv4 address> [-p <custom prefix>]`                                   | **Gain technical information about any IPv4 address** in question. Especially helpful if you have a host address along with an optional `custom prefix` and like to know what domain network address it belongs to.                                                                                                                                                                                                                                                            |
| `subito convert <subnet mask or prefix>`                                               | **Convert subnet masks to their prefix** and vice versa. Useful in cases when a mask or prefix is less common.                                                                                                                                                                                                                                                                                                                                                                 |

### Create Subnets using Config Strings

In Subito, you will use so-called _Configuration Strings_ (_Config Strings_ for short)
to tell the utility how a given network should be compartmentalised. Let's figure it out with an example:

**Suppose** you have a _local class B network_, `172.16.5.0/16`, for a small startup business, and you need an addressing scheme for these networks,
which should have their own broadcast domains of course, keeping data traffic isolated while enhancing performance:

| Network Name                  | Initial Host Count Required | Reserve in % for Future Expansion |
|-------------------------------|-----------------------------|-----------------------------------|
| **LAN A**, _Office_           | 40                          | 300                               |
| **LAN B**, _Customer Support_ | 10                          | 100                               |
| **LAN C**, _IoT_              | 500                         | 150                               |
| **LAN D**, _VoIP_             | 30                          | 300                               |


#### Compiling a Config String

Instead of doing this manually (what is of course possible, but can be tedious and error-prone for larger networks),
you translate the chart above into a simple _Config String_ which Subito can understand:

`40:300 10:100 500:150 30:300`

As you can see, the correlation is quite simple: A _Config String_ always consists of a list of _Basic Strings_,
like `40:300`. It is telling Subito how a **single subnet block is supposed to be dimensioned**.

| Syntax of a Basic String                                        |
|-----------------------------------------------------------------|
| `<initial host count>:<reserve percent for initial host count>` |

In the given example, this _Basic String_ describes the **host block demanded for LAN A**:
The string's first number, `40`, says **how many initial hosts** the demanded host block should be capable of.

Its second number behind the colon, `300`, says **how much buffer in addresses as a percentage of the initial
host count should be reserved additionally** to grant future expansion of the subnet if the network will grow.

In this case, it would demand a host block size capable of `40 + 40 * (300/100) = 160` hosts in total.

#### Tuning a Config String

In larger networks, it's quite common to have multiple host blocks with identical sizes. It would be
horrible if you had 20 identical network portions and would need to type that in 20 times for a Config String with
the method shown above.

💡 **Don't worry**: Subito allows you to use _Extended Strings_ in such a case, like
`2:0x20 500:10x5`.

With a Config String like this, you would tell Subito demanding 20 subnets containing point-to-point connections
with zero reserve and 5 subnets demanding a block size to be capable of 500 hosts with 5 percent reserve each.

| Syntax of an Extended String                                                       |
|------------------------------------------------------------------------------------|
| `<initial host count>:<reserve percent for initial host count>x<block multiplier>` |

#### Combining Basic and Extended Strings

Of course, you can combine both kinds of strings to a custom Config String.
Hopefully, you are now ready to compile your own Config Strings!

ℹ️ **Please keep in mind** that a _Config String_ must describe **at least two** subnet blocks.
Therefore, a minimum _Config String_ of `42:42 42:42` will be equivalent to `42:42x2`,
such that both examples fulfil this requirement.

---

## Usage

To demonstrate how Subito can be applied, let's refer to the previous startup example,
on the basis of the scheme shown above with the network `172.16.5.0/16`.

### Subnetting

```bash
$ subito create-netplan 172.16.5.0 40:300 10:100 500:150 30:300
```
```
Subnetting table for network 172.16.5.0/21

1. Subnet 172.16.5.0/21
        Capable of 2046 hosts at max
        Subnet mask:     255.255.248.0
        First host addr: 172.16.5.1
        Last host addr:  172.16.12.254
        Broadcast addr:  172.16.12.255
        (i) Will not be routed: Private-Use Networks (RFC 1918)

2. Subnet 172.16.13.0/24
        Capable of 254 hosts at max
        Subnet mask:     255.255.255.0
        First host addr: 172.16.13.1
        Last host addr:  172.16.13.254
        Broadcast addr:  172.16.13.255
        (i) Will not be routed: Private-Use Networks (RFC 1918)

3. Subnet 172.16.14.0/25
        Capable of 126 hosts at max
        Subnet mask:     255.255.255.128
        First host addr: 172.16.14.1
        Last host addr:  172.16.14.126
        Broadcast addr:  172.16.14.127
        (i) Will not be routed: Private-Use Networks (RFC 1918)

4. Subnet 172.16.14.128/27
        Capable of 30 hosts at max
        Subnet mask:     255.255.255.224
        First host addr: 172.16.14.129
        Last host addr:  172.16.14.158
        Broadcast addr:  172.16.14.159
        (i) Will not be routed: Private-Use Networks (RFC 1918)
```
💡 **Maybe you noticed** that the subnet capabilities seem to exceed the demanded host count by far in some cases.
This is perfectly fine. Subito operates on **binary level** internally and calculates the required block
length in bits of a certain count.

ℹ️ **Reason:**
The _Basic String_, `500:150`, results in `500 + 500 * 150% = 1250` hosts the demanded host block should
be capable of. In binary notation, `1250 = 0b10011100010`, resulting in a block size `BS = 11` bits.
Now, the host formula for the max host count is `(2 ^ BS) - 2`, giving us `(2 ^ 11) - 2 = 2046` hosts this
block is capable to contain. The `- 2` takes care of the fact that two addresses, both the networks' and the broadcast's,
are already reserved and not for free use.

#### Save Results to a Spreadsheet

```bash
$ subito create-netplan 172.16.5.0 40:300 10:100 500:150 30:300 -s startup_netplan
```
```
  [...]
 Broadcast addr:  172.16.14.127
        (i) Will not be routed: Private-Use Networks (RFC 1918)

4. Subnet 172.16.14.128/27
        Capable of 30 hosts at max
        Subnet mask:     255.255.255.224
        First host addr: 172.16.14.129
        Last host addr:  172.16.14.158
        Broadcast addr:  172.16.14.159
        (i) Will not be routed: Private-Use Networks (RFC 1918)
        
 ✅ Stored your spreadsheet at "./startup_netplan.xlsx"
```

If you are satisfied with a subnetting plan you created with Subito, you can **save it
to a spreadsheet file** in MS Excel format. Because it's widely spread, it can be viewed and
edited with basically any spreadsheet application of you choice, Open Source ones as well ;)
The file will be stored right inside you current working directory.

### Technical Inspection

```bash
# Gain technical information about an address inside 172.16.5.0/16
$ subito inspect 172.16.5.131
```
```
Inspection results for IP 172.16.5.131:

        Address class:  B
        Special use case: Private-Use Networks (RFC 1918)

        Default prefix: /16
        Default mask:   255.255.0.0
```
```bash
# Retrieve the domain custom subnet of 172.16.5.131/27
$ subito inspect 172.16.5.131 -p 27
```
```
Inspection results for IP 172.16.5.131:

        Address class:  B
        Special use case: Private-Use Networks (RFC 1918)

        Default prefix: /16
        Default mask:   255.255.0.0

        Network addr: 172.16.5.128/27
```

As you can see, the _inspection_ command will also **tell about special use cases** as they have been
defined by the IETF in [RFC 5735, Section 4](https://www.rfc-editor.org/rfc/rfc5735#section-4).

### Converting Subnet Masks and Prefixes

```bash
# Get the subnet mask for a less common prefix ...
$ subito convert 27
As a subnet mask: 255.255.255.224
```
```bash
# ... and vice versa
$ subito convert 255.255.255.224
As a prefix: /27
```

## Error Handling

Subito has been created on the mindset that **software should always act in the user's interests**.
If problems occur, nobody wants to be left in the cold. For this reason, Subito aims to support its
users as much as possible. The following examples show how Subito behaves in the most common cases.

**1) Insufficient subnetting:**

```bash
$ subito create-netplan 192.168.20.0 200:0x2
```
In this case, Subito delivers a **detailed analysis** on what's going wrong. You have much better chances
to identify the problem, because Subito makes **suggestions concerning obvious shortcomings** regarding the demanded configuration:
```
⚠️ Sorry, some of your demanded subnets for network 192.168.20.0/24 (class C) won't fit!
Please investigate the messages below:

1. Subnet: 254 hosts max
        host portion: BS=8 bits, 0 bits colliding with network portion
        subnet portion: BS=0 bits, 1 bits exploding

2. Subnet: 254 hosts max
        host portion: BS=8 bits, 0 bits colliding with network portion
        subnet portion: BS=0 bits, 1 bits exploding

(i) For class C networks, you most likely ran out of host block space.
 A 'subnet portion: BS=0 bits' means that the host block size is too large,
 preventing the creation of subnets at all.
 More than zero 'bits exploding' means you ran out of subnetting block space.
```

**2) Erroneous attempt to apply subnetting to a reserved address space:**

```bash
$ subito create-netplan 192.0.2.0 100:0x2
```
Here, the user chose a **network address which serves a special use case** and should
not be used for any productive ends. Subito recognizes such cases and responds succinctly:
```
⚠️ Address reserved for special purpose: TEST-NET-1 (RFC 5737)
```

## Final Thoughts

There are plenty of tools outside covering topics like subnetting. This project has been done primarily as an opportunity
to learn and from a standpoint of curiosity how certain coding challenges can be solved more effectively.

Subito is a utility covering basic cases only. Further it is fairly limited, because it completely ignores IPv6 which is
becoming more important every day. Feel free to fork this repo if you like - there is always lots of space for improvement!

## 🏆 Acknowledgements

- This project has been built **on top of [Click](https://click.palletsprojects.com/en/stable/)**, a very great CLI framework for Python!
- **[Real Python](https://realpython.com/team/)** and its team for their excellent tutorials - maybe the best out there on the Web. Thank you!
- Great appreciation to my former teacher, **Martin Schneider**, who brought me to Python. I owe him a lot!