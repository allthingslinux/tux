# Versioning

## Auto Generated Version Examples
These are examples of how our configuration of [poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning) will generate the version number.

If branch is not main and there are commits since last tag:
```
tux 0.0.0.dev2106+b731156.dynamicversioning
^   ^     ^       ^       ^
name^     commits commit  branch (escaped), is empty if its main
    ver   since   hash
          last
          tag
```
If branch is main and there are commits since last tag:
```
tux 0.0.0.dev2106+b731156
^   ^     ^       ^
name^     commits commit
    ver   since   hash
          last
          tag
```
If branch is main and there are no commits since last tag:
```
tux 0.0.0
^   ^
name^
    ver
```

## Scheme
We use PEP 440 for formatting our version numbers, however we use SemVer for the versioning scheme.
> Keep in mind you cannot use .dev(NUMBER) as it clashes with the auto generated versioning. (e.g 0.1.0rc1.dev1 is invalid and won't show up properly)

## SemVer Summary
A example in tux would be:
Given a version number MAJOR.MINOR.PATCH, increment the:

MAJOR version when you make changes that may need significant manual setup from the last version (example would be a web panel, config overhaul, major db changes)
MINOR version when you make changes that needs little to no manual interference (at most maybe tweaking a config value or updating the db)
PATCH version when you make changes that need no manual interference

You can add stuff like "0.1.0**rc1**" to mark small changes leading up to a release. (release candidates)

You do not need to stick to this absolutely all the time, this is a guideline on how to make your versioning.
