# nbcli create

```
$ nbcli create -h
usage: nbcli create [-h] [-v] [-q] file

Create and/or Update objects defined in YAML file.

positional arguments:
  file           YAML file.

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Show more logging messages
  -q, --quiet    Show fewer logging messages

Run command.

See documentation and reference examples.
https://nbcli.codeberg.page/latest/commands/create/
https://nbcli.codeberg.page/latest/reference/create-examples/

Usage Examples:

- Create/Update objects defined in YAML file
  $ nbcli create file.yml
```

## YAML file format

Each top-level key names an object type (alias or model, e.g. `address` or
`ipam.ip_addresses`). The value is either a list of objects to create, or a
mapping of fields.

```yaml
address:
- address: 10.0.0.1/24
  dns_name: host1.example.com
  status: active
```

A field whose value is another object's lookup value is resolved to that
object automatically (`site: DC 1` on a device resolves to the site named
"DC 1"). A field that names the object's own model — `address` on an
`address`, `prefix` on a `prefix` — is always treated as a literal value,
never as a reference.

### Upsert form

`model:lookup_value:` creates the object if no existing object matches the
lookup value, or updates it otherwise.

```yaml
address:10.0.0.1/24:
  dns_name: host1.example.com
```

### Nested objects

A `model:lookup:` key inside an object creates a child object. The parent
contributes its reply fields to the child's existence check and to the
created data (e.g. an `address` nested under a `prefix` is looked up with
NetBox's `parent=` filter). Appending `^` to the lookup value
(`address:10.0.0.1/24^`) skips the parent's contribution to the existence
check.

```yaml
prefix:10.0.9.0/24:
  status: active
  address:10.0.9.1/24:
    dns_name: host2.example.com
``` 
