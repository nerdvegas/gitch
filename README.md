# gitch

Gitch syncs github release notes with your project's CHANGELOG.md. _How_ you
create your changelog is of no interest to gitch.

# Install

```
]$ pip install gitch
```

# Configure

You will first need to [create a github personal access token](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line).
You will need to give your access token `repo` scope.

Then, tell gitch about it like so:

```
]$ export GITCH_GITHUB_TOKEN=<token>
```

# Usage

Consider a `CHANGELOG.md` like so:

```
# Changelog

## 2.60.1 (2020-05-23)

**Merged pull requests:**

- did a thing to a thing.

## 2.60.0 (2020-05-12)

**Closed issues:**

- fixed some other thing that was fooing too much.
```

The `gitch` tool will assume that the _first token in each H2 header_ identifies
a tag in your github repository (in the example above, these are `2.60.1` and
`2.60.0`). It will then simply create github releases that match these tags. The
actual content within each tag section is copied verbatim into the release notes.

```
]$ gitch --all
gitch INFO Syncing '2.60.1' to github...
gitch INFO '2.60.1' synced, see https://github.com/jbloggs/foo/releases/tag/2.60.1
gitch INFO Syncing '2.60.0' to github...
gitch INFO '2.60.0' synced, see https://github.com/jbloggs/foo/releases/tag/2.60.0
```

## Examples

To list the tags present in your changelog:

```
]$ gitch -l
```

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
