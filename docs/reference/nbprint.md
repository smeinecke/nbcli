# nbprint()

```python
>>> devlist = Devices.filter('server')
>>> nbprint(devlist)
>>> nbprint(devlist, disable_header=True)
>>> nbprint(devlist, json_view=True)
>>> nbprint(devlist, detail_view=True)
>>> nbprint(devlist, cols=['name',
...                        'device_type.manufacturer',
...                        'device_type.model'])
>>> nbprint(devlist, cols=[('Name', 'name'),
...                        ('Manufacturer', 'device_type.manufacturer'),
...                        ('Model', 'device_type.model')])
>>> nbprint(devlist, view_model='MyDevicesView')
>>> from user_views import MyDevicesView
>>> nbprint(devlist, view_model=MyDevicesView)
```

## Attribute paths in `cols`

Each `cols` entry is an attribute path resolved by `BaseView.get_attr`:

- `.` traverses object attributes - nested NetBox objects are pynetbox
  `Record`s, so `device_type.manufacturer.name` works on them.
- `:key` does a dict lookup - useful for plain dict fields such as
  `custom_fields` (`custom_fields:env`).
- `:N` indexes into lists - `tags:0` renders the first tag,
  `tags:1.name` drills further into it.

```python
>>> nbprint(devlist, cols=['name',
...                        'tags:0',
...                        'tags:1.name',
...                        'custom_fields:env'])
```

Missing attributes, keys, or out-of-range indexes render as `-`.

```
>>> from nbcli.views.tools import Formatter
>>> f = Formatter(devlist)
>>> f.string
```
