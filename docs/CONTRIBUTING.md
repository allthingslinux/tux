# Contributing to Tux 🐧

## Topics
- [Contributing Flow](#contributing-flow)
- [Issues](#issues)
- [Branch Naming Conventions](#branch-naming-conventions)

## Contributing Flow
1. See [Issues](#issues) topic.
2. Fork the project.
3. Create a new branch (please, see [Branch Naming Conventions](#branch-naming-conventions) topic if you don't know our conventions).


4. After done with modifications, time to commit and push. Example:

```
git add tux/help.py
git commit -m "feat(tux): add help command" -m "Help command description"
git push origin feat/add-help-command
```

5. Send a PR with the modifications, referencing `main`.
6. Your contribution will be verified.


After merge:
- Delete the branch used to commit:
```
git checkout main
git push origin --delete feat/add-help-command
git branch -D feat/add-help-command
```

- Update your fork:
```
git remote add upstream https://github.com/allthingslinux/tux.git
git fetch upstream
git rebase upstream/main
git push -f origin main
```

## Issues
Before submitting a large PR, please open an [issue](https://github.com/allthingslinux/tux/issues/new) so we can discuss the idea. 

## Branch Naming Conventions 
- Documentation: `git checkout -b docs/contributing`
- Modifications: `git checkout -b chore/update-dependencies`
- Features: `git checkout -b feat/add-help-command`
- Fixing: `git checkout -b fix/help-command`