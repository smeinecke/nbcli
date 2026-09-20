# nbcli ipblocks

```
$ nbcli ipblocks -h
usage: nbcli ipblocks [-h] [-v] [-q] [--ongoing COUNT] [--pick COUNT] [--json]
                      [--limit LIMIT]
                      prefix

Find unused or ongoing IP blocks within a NetBox prefix.

positional arguments:
  prefix           Subnet/prefix to search (e.g. 192.168.1.0/24)

options:
  -h, --help       show this help message and exit
  -v, --verbose    Show more logging messages
  -q, --quiet      Show fewer logging messages
  --ongoing COUNT  Search for blocks with at least COUNT consecutive available IPs.
  --pick COUNT     Print COUNT free IPs from the first block with enough space.
  --json           Display results as json string.
  --limit LIMIT    Maximum number of addresses to evaluate (default: 10000).

Usage Examples:

- List all unused (available) IP blocks in a prefix:
  $ nbcli ipblocks 192.168.1.0/24

- Find blocks with at least 10 consecutive available IPs:
  $ nbcli ipblocks 192.168.1.0/24 --ongoing 10

- Print the next 2 free IPs (from one contiguous block):
  $ nbcli ipblocks 192.168.1.0/24 --pick 2

- Return results as json:
  $ nbcli ipblocks 192.168.1.0/24 --json
```
