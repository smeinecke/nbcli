# Create Examples

`nbcli create file.yml` creates or updates objects described by one or more
YAML documents. Two forms are supported per document key.

## List form — always create

```yaml
region:

- name: USA
  slug: usa

- name: New York
  slug: newyork
  parent: USA   # resolved via dcim.regions (nested 'parent' alias)
```

## Upsert form — update if found, create otherwise

```yaml
device:web-1:
  device_role: Server      # resolved, sent as 'role' on NetBox 4.x
  device_type: T600        # device_types resolve by 'model'
  serial: '000002'
  tenant: ENCOM
  site: DC 1
  rack: '1.1'
  position: 2
  face: front
```

`device:web-1` looks the device up by its `lookup` field (`name` by default;
`nbcli info --models` lists each model's lookup). If it exists, the mapping
is PATCHed onto it; otherwise the object is created with `name=web-1` plus
the mapping.

## Literal model fields

A field that names the object's own model is literal data, not a lookup:

```yaml
address:
- address: 10.0.0.5/24
  dns_name: spare-1.example.com
```

`address` above is stored verbatim — it is not resolved as a reference.
The same applies to `prefix:` on prefixes.

## Nested objects

Any `model:lookup:` key inside a mapping creates a child object after the
parent. The parent's reply fields (e.g. `id`) scope the child's existence
lookup and are added to its create/update data:

```yaml
prefix:10.0.2.0/24:
  status: active

  address:10.0.2.1/24:
    dns_name: nested-1.example.com
```

Here the nested address existence-check filters by `parent=<prefix>` (the
valid `ip_addresses` filter contributed by `resolve_reference.yml`).

Appending `^` to a model key (`model:lookup^:`) skips the parent args in the
existence lookup while still applying them to create/update — an escape
hatch for cases where the parent's reply fields are not valid filter
parameters on the child endpoint.

## Full example files

See `tests/upsert-test.yml`, `tests/create-test.yml`, and
`tests/update-test.yml` in the repository for a complete multi-document
worked example (manufacturers → device types → tenants → sites → racks →
roles → devices → device bays → prefixes → addresses).
