# Versioning

## Auto Generated Version Examples
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
> Keep in mind you cannot use .dev(NUMBER) as it clashes with the auto generated versioning.
