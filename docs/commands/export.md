# nbcli export

```
$ nbcli export -h
usage: nbcli export [-h] [-v] [-q] [-f FILE] [--upsert] [-e] model [args ...]

positional arguments:
  model                NetBox model.
  args                 Argument(s) to filter results.

options:
  -h, --help           show this help message and exit
  -v, --verbose        Show more logging messages
  -q, --quiet          Show fewer logging messages
  -f, --file FILE      Write YAML to file instead of stdout.
  --upsert             Export as 'model:lookup' mapping so re-import updates
                       existing objects.
  -e, --include-empty  Include fields with empty/null values.
```

Export matching objects as YAML in the format `nbcli create` reads. Useful for
migrating existing data to another NetBox instance or as a template for
additional entities.

Objects are selected with the same search term, keyword, auto-resolve, and
compound-resolve arguments as [`nbcli filter`](filter.md). Unlike `filter`,
`export` always returns all matching objects - `filter_limit` is not applied.

```yaml
$ nbcli export site
site:
- name: DC 1
  slug: dc-1
  status: active
  region: New York
- name: DC 2
  slug: dc-2
  status: active
```

## Field mapping

Related objects are written as the lookup value `nbcli create` would resolve
them by (usually `name`, e.g. `site: DC 1` or `device_type: A-2U-C`),
choice fields as their API value (`status: active`), and read-only fields such
as `id`, `url`, `display`, `created`, `last_updated`, and `*_count` counters
are omitted. Fields with empty values are omitted unless `-e`/`--include-empty`
is given.

Related fields that cannot be mapped to a resolvable object type (for example
generic relations like `scope` or `assigned_object`) are written as a
best-effort name and may need manual adjustment before re-import.

## Output

By default the YAML document is printed to stdout. Use `-f`/`--file` to write
it to a file, or redirect it.

```
$ nbcli export prefix tenant:ENCOM -f prefixes.yml
```

## Upsert form

With `--upsert` each object is exported as a `model:lookup` key, so re-importing
the file updates existing objects instead of only creating new ones (see
[create](create.md#upsert-form)).

```yaml
$ nbcli export device --upsert
device:web-1:
  device_type: A-2U-C
  role: server
  site: DC 1
  status: active
```
