# nbcli search

```
$ nbcli search -h
usage: nbcli search [-h] [-v] [-q] [--json] [--limit LIMIT] [obj_type] searchterm

Search Netbox objects with the given searchterm.

The List of search objects can be modified in:
$CONF_DIR/user_config.yml

positional arguments:
  obj_type       Object type to search
  searchterm     Search term

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Show more logging messages
  -q, --quiet    Show fewer logging messages
  --json         Display results as json string.
  --limit LIMIT  Limit number of results per object type (overrides 'nbcli.filter_limit').

Run a search of Netbox objects and show a table view or json view of results.

Usage Examples:

- Search all object types for 'server1':
  $ nbcli search server1

- Search the interface object type for 'eth 1':
  $ nbcli search interface 'eth 1'

- Search all object types for 'server1' and return JSON for agents:
  $ nbcli search server1 --json

- Search only devices for 'server1' and return JSON:
  $ nbcli search device server1 --json

- Search all object types for 'server1' and return up to 5 results per type:
  $ nbcli search server1 --limit 5
```

The `search` command is designed to emulate the main search bar that can be found
at the top of the home page of the Netbox web interface.

By default it will search through a predefined list of object types and return
up to `filter_limit` (default `50`) results for each object type. If more than
that many results are found, it will display the filter command to show all the
results. The `--limit` option can be used to override the `filter_limit` value
from `user_config.yml` for a single search. Use `--limit 0` to return all
results.

If your search term needs to contain a space, make sure to wrap it in quotes.

```
nbcli search 'web server'
```

If you only want to search one object type you can specify if before the search
term. `nbcli search [obj_type] searchterm`.

* Searching all object types for `server1`:

    ```
    nbcli search server1
    ```

* Searching only devices for `server1`:

    ```
    nbcli search device server1
    ```

The list of predefined object types that will be searched can be modified by
editing the [user_config.yml](../init/#config-file) file.

```yaml
nbcli:
#  search_objects:
#    - provider
#    - circuit
#    - site
#    - rack
#    - location
#    - device_type
#    - device
#    - virtual_chassis
#    - cable
#    - power_feed
#    - vrf
#    - aggregate
#    - prefix
#    - address
#    - vlan
#    - secret
#    - tenant
#    - cluster
#    - virtual_machine
```

## Plugin objects

Object types provided by NetBox plugins can be added by enabling the plugin in
the `user_config.yml` file.

```yaml
nbcli:
  plugins:
    - netbox_dns
```

Enabling a plugin adds its object types to the list of objects that are
searched by default, and makes them available to the `search`, `filter`,
`create`, `info`, and `shell` commands.

Currently supported plugins:

- `netbox_dns` - [netbox-plugin-dns](https://github.com/sys4/netbox-plugin-dns)
  adds `nameserver`, `view`, `zone`, `record`, `registrar`, `contact`,
  `zone_template`, `record_template`, `dnssec_key_template`, and
  `dnssec_policy` object types.

```
$ nbcli search record 'www'
```

The plugin must be installed and enabled on the NetBox instance for its object
types to return results.

## JSON output

The `--json` flag returns a machine-readable JSON array of all matching records.
This is useful for agents, shell scripts, or any automation that needs to parse
search results.

Each record in the JSON output is a NetBox object with an extra `_nbcli_type`
field that identifies which object type the record belongs to. This makes it easy
to tell mixed search results apart.

```bash
$ nbcli search dmi01 --json | python3 -m json.tool
[
  {
    "_nbcli_type": "device",
    "id": 1,
    "name": "dmi01-akron-pdu01",
    "...": "..."
  },
  {
    "_nbcli_type": "device",
    "id": 2,
    "name": "dmi01-akron-rtr01",
    "...": "..."
  }
]
```

!!! info
    `nbcli search` relies on the `q` parameter being available for the GET
    method on the REST API endpoint. Make sure any object added to the
    `search_objects` list has the `q` parameter available for the GET method.

    Your Netbox instance API docs should be available at
    https://your.netbox.url/api/docs
