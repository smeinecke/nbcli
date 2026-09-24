# Environment Variables

nbcli reads configuration from `$NBCLI_DIR/user_config.yml`
(default `~/.nbcli/user_config.yml`). Every value in that file can also be
set or overridden with an environment variable of the form
`NBCLI_<SECTION>_<ATTR>`.

For example:

```bash
export NBCLI_PYNETBOX_URL="http://localhost:8080"
export NBCLI_PYNETBOX_TOKEN="0123456789abcdef0123456789abcdef01234567"
export NBCLI_NBCLI_FILTER_LIMIT=10
export NBCLI_REQUESTS_VERIFY=false   # disable TLS verification
```

A section that does not exist in `user_config.yml` is created from env vars,
so `pynetbox` can be configured entirely from the environment (useful in CI).
Environment variables win over file values.

Strings `true`, `false`, and `none` (any case) are converted to `True`,
`False`, and `None`; JSON lists/objects in `[...]`/`{...}` are parsed as such.
Everything else stays a string — use sites convert numeric values themselves.

## Special variables

| Variable          | Effect                                          |
| ----------------- | ----------------------------------------------- |
| `NBCLI_DIR`       | Path of the nbcli config dir (default `~/.nbcli`) |
| `NBCLI_LOGLEVEL`  | Python logging level for nbcli (e.g. `DEBUG`)    |

`nbcli info --detailed` prints the currently active `NBCLI_*` variables;
values containing `TOKEN`, `KEY`, `SECRET`, or `PASSWORD` are masked.
