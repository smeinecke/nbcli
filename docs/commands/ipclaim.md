# nbcli ipclaim

```
$ nbcli ipclaim -h
usage: nbcli ipclaim [-h] [-v] [-q] [--address IP] [--description DESCRIPTION]
                     [--status STATUS] [--json]
                     prefix fqdn

Claim the next free (or a given) IP address within a NetBox prefix.

Creates an ipam.ip_addresses object carrying a dns_name; on NetBox
installations with netbox-dns IPAM coupling enabled, managed A/PTR
records are created automatically.

positional arguments:
  prefix                Prefix to claim the address in.
  fqdn                  DNS name (FQDN) for the address.

options:
  -h, --help            show this help message and exit
  -v, --verbose         Show more logging messages
  -q, --quiet           Show fewer logging messages
  --address IP          Specific IP to claim (default: first free host in the prefix).
  --description DESCRIPTION
                        Description for the IP address.
  --status STATUS       IP address status (default: active).
  --json                Display result as json string.

Usage Examples:

- Claim the next free address in a prefix:
  $ nbcli ipclaim 192.168.1.0/24 host1.example.com

- Claim a specific address:
  $ nbcli ipclaim 192.168.1.0/24 host2.example.com --address 192.168.1.10

- Claim with a description:
  $ nbcli ipclaim 192.168.1.0/24 host3.example.com --description "web server"
```
