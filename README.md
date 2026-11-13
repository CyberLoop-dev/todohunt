<p align="center">
  <img src="assets/banner.svg" alt="todohunt banner" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-facc15?style=for-the-badge" alt="python">
  <img src="https://img.shields.io/badge/dependencies-zero-10b981?style=for-the-badge" alt="zero deps">
  <img src="https://img.shields.io/badge/license-MIT-3b82f6?style=for-the-badge" alt="MIT">
</p>

**todohunt** finds every `TODO`, `FIXME`, `HACK` and `XXX` comment in your project, groups them by tag, and can tell you how long each one has been sitting there using `git blame`.

## Usage

```bash
python todohunt.py                  # scan the current folder
python todohunt.py ~/myproject      # scan another folder
python todohunt.py --age            # add git age, oldest first
python todohunt.py --tags TODO BUG  # choose your own tags
python todohunt.py --json           # machine-readable output
```

Sample output:

```
FIXME  (2)
    2y  src/auth.py:41  token refresh races with logout
    3mo src/db.py:88    close the connection on error

TODO  (5)
    8mo app/main.py:12  split this into modules
    ...

7 item(s) found
```

## Use it in CI

Fail the build if the pile grows past a limit:

```bash
python todohunt.py --max 20
```

Exit code is `1` when more than `--max` items exist, otherwise `0`.

## How it works

- Matches a tag right after a comment marker (`#`, `//`, `/*`, `<!--`, `--`, `;`), so words inside strings are mostly ignored.
- Skips `.git`, `node_modules`, virtualenvs, build folders and binary files.
- `--age` runs `git blame` once per file that has hits. Files not tracked by git simply show `-`.

## Limits

Only comments that start with the tag are detected, for example `# TODO: fix` but not `# remember to TODO`. Tags are matched in upper case.

## License

MIT
