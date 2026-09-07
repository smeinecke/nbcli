# nbcli init

```
$ nbcli init -h
usage: nbcli init [-h] [-v] [-q]

Initialize nbcli.

Default confg directory location $HOME/.nbcli
After running edit $HOME/.nbcli/user_config.yml with your credentials.

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Show more logging messages
  -q, --quiet    Show fewer logging messages

Create nbcli config directory and related files.

Example Usage:

- Initialize nbcli
  $ nbcli init
```

## Config Directory 

The default nbcli directory is :code:`~/.nbcli/` this can be changed by setting
the NBCLI_DIR to a new directory

```bash
export NBCLI_DIR=/path/to/alt/directory
```

## Config File

The config file `user_config.yml` is located in the root of the config directory.

Values defined under pynetbox will be directly used to create the [pynetbox
api instance](https://pynetbox.readthedocs.io/en/latest/#api>).  
at minimum **url** and **token** need to be set.


```yaml
pynetbox:
  url: http://localhost:8080
  token: nbt_test.0123456789abcdef0123456789abcdef01234567
```

Values defined under requests will be used to create a
[custom requests Session](https://pynetbox.readthedocs.io/en/latest/advanced.html#custom-sessions).

If you need to disable SSL verification, add (*or uncomment*) the following to your user_config.yml file. 

```yaml
requests:
  verify: false
```

Values defined under nbcli change the behavior of nbcli itself.

```yaml
nbcli:

  # Limit results returned from filter and search commands. Set to 0 to disable.
  filter_limit: 50

  # Number of workers if threading is enabled
  max_workers: 10

  # Enable support for NetBox plugins.
  # Adds the plugin's object types to 'nbcli search' results and enables
  # them for 'nbcli create', 'nbcli filter', 'nbcli info' and 'nbcli shell'.
  # Currently supported:
  #   netbox_dns - https://github.com/sys4/netbox-plugin-dns
  plugins:
    - netbox_dns
```
