# gitch

Syncs github release notes with your project's CHANGELOG.md.

# Install

```
]$ pip install gitch`
```

# Usage

Consider a `CHANGELOG.md` like so:

```
# Changelog

## 2.60.1 (2020-05-23)

**Merged pull requests:**

- did a thing to a thing.

**Closed issues:**

- fixed some other thing that was fooing too much.

## 2.60.0 (2020-05-12)
...
```

The `gitch` tool will assume that the _first token in each H2 header_ identifies
a tag in your github repository (in the example above, these are `2.60.1` and
`2.60.0`). It will then simply create github releases that match these tags. The
actual content within each tag section is copied verbatim into the release notes.

## Examples

To sync the latest changelog tag to github release notes:

```
]$ gitch
```

To sync a specific changelog tag to github release notes:

```
]$ gitch <tag>
```

To overwrite a github release (this does not happen by default):

```
]$ gitch <tag> --overwrite
```

To sync an entire changelog to github (ie create all associated releases):

```
]$ gitch --all
```

To sync an entire changelog to github and overwrite all existing releases:

```
]$ gitch --all --overwrite
```
