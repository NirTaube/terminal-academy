# Terminal command reference

Examples assume you are inside your lab folder. Substitute actual paths. Most commands work on macOS and Linux; platform-specific commands are labelled. The installed manual, `man COMMAND`, describes your version.

## Navigation

| Command | Purpose |
| --- | --- |
| `pwd` | Current directory |
| `ls` | List entries |
| `ls -l` | Detailed listing |
| `ls -a` | Include hidden entries |
| `ls -lah` | Details, hidden entries, readable sizes |
| `cd reports` | Change directory |
| `cd ..` | Go to parent |
| `cd ~` | Go home |
| `cd -` | Return to previous directory |
| `tree -L 2` | Display two levels of the directory tree |
| `tree -a -L 2` | Include hidden entries |
| `tree -d` | Display directories only |

`.` means current directory; `..` means parent; `~` expands to home. `/` starts an absolute path. Quote filenames with spaces: `cat "analyst notes.txt"`.

## Files

| Command | Purpose |
| --- | --- |
| `mkdir reports` | Create a directory |
| `mkdir -p reports/daily` | Create missing parents |
| `touch notes.txt` | Create if absent; otherwise update timestamps |
| `cp source.txt copy.txt` | Copy, keeping source |
| `cp -i source.txt copy.txt` | Ask before overwriting |
| `cp -R docs docs-backup` | Copy a directory recursively |
| `mv -i draft.txt final.txt` | Rename, asking before overwrite |
| `mv final.txt reports/` | Move into a directory |
| `rm -i unwanted.txt` | Confirm file removal; this is not Trash |
| `rmdir empty-folder` | Remove an empty directory |

Source first, destination second. Check your path before changing or removing anything.

## Reading and searching

| Command | Purpose |
| --- | --- |
| `cat notes.txt` | Print contents |
| `less auth.log` | Browse contents; `/` searches, `n` advances, `q` exits |
| `head -n 5 auth.log` | First five lines |
| `tail -n 5 auth.log` | Last five lines |
| `tail -f auth.log` | Follow appended content; Ctrl+C stops |
| `wc -l auth.log` | Count newlines |
| `file evidence.bin` | Inspect likely file type |
| `nano notes.txt` | Edit; Ctrl+O saves, Enter confirms, Ctrl+X exits |
| `diff old.txt new.txt` | Compare text; exit status 1 means differences |
| `find . -type f -name '*.log'` | Find matching filenames recursively |
| `find . -type d -name 'reports'` | Find directories |
| `grep 'FAILED' auth.log` | Matching lines |
| `grep -n 'FAILED' auth.log` | Include line numbers |
| `grep -i 'failed' auth.log` | Ignore case |
| `grep -v 'INFO' auth.log` | Nonmatching lines |
| `grep -c 'FAILED' auth.log` | Count matching lines |
| `grep -r 'FAILED' logs/` | Search recursively |
| `grep -F '192.168.1.5' auth.log` | Literal substring match |

`find` locates entries; `grep` searches text. A literal substring can also appear inside a longer value: `.5` can match `.50`.

## Combining commands

| Syntax | Purpose |
| --- | --- |
| `grep 'FAILED' auth.log \| wc -l` | Filter, then count |
| `grep 'FAILED' auth.log > failed.txt` | Create or overwrite output |
| `echo 'Review complete' >> summary.txt` | Append |
| `ls missing.txt 2> errors.txt` | Save error output |
| `wc -l < auth.log` | Read standard input from a file |
| `mkdir -p reports && touch reports/ok.txt` | Run second command only after success |

Do not redirect output into the file being read: `grep 'FAILED' auth.log > auth.log` can truncate your input.

## Organising text

| Command | Purpose |
| --- | --- |
| `sort users.txt` | Sort lines |
| `sort -u users.txt` | Sort and deduplicate |
| `uniq users.txt` | Remove adjacent repetitions |
| `sort users.txt \| uniq -c` | Count occurrences |
| `cut -d ',' -f 2 data.csv` | Second field in simple comma-separated text |
| `sed -n '5,10p' auth.log` | Lines 5 through 10 |

`uniq` needs equal lines adjacent. `cut` is not a full parser for quoted CSV.

## Identity and permissions

| Command | Purpose |
| --- | --- |
| `whoami` | Effective username |
| `id` | User and group IDs |
| `groups` | Group memberships |
| `ls -l private.txt` | Basic mode bits and ownership |
| `chmod 600 private.txt` | Owner read/write; group and others none |
| `chmod 644 notes.txt` | Owner read/write; group and others read |
| `chmod u+x script.sh` | Add owner execute |
| `sudo COMMAND` | Run under configured elevated/alternate-user policy |

Permission values: read=4, write=2, execute=1. Numeric modes describe owner/group/others. Directory traversal uses execute permission; ACLs and privileged users can affect access beyond mode bits. No exercise requires sudo.

## Processes and system information

| Command | Purpose |
| --- | --- |
| `ps aux` | Process list |
| `top` | Changing process activity; `q` exits |
| `kill -TERM PID` | Request termination of an identified process |
| `df -h` | Filesystem space |
| `du -sh reports` | Directory disk usage |
| `uname -a` | Kernel/system identification |
| `date` | Date and time |

Only stop the disposable worker identified by the instructor when practising process control.

## Networking

| Command | System | Purpose |
| --- | --- | --- |
| `ip -br address` | Linux/Kali | Interface addresses |
| `ip route` | Linux/Kali | Routes |
| `ss -lnt` | Linux/Kali | Listening TCP sockets |
| `ifconfig` | macOS | Interface settings |
| `route -n get default` | macOS | Default route |
| `lsof -nP -iTCP -sTCP:LISTEN` | macOS | Visible listening TCP processes |
| `ping -c 4 127.0.0.1` | Both | Four loopback echo requests |
| `curl -I URL` | Both | HTTP HEAD request |
| `dig example.com` | Both, if installed | DNS query |

An address or route does not prove internet access. A blocked ping does not prove a destination is down. Course HTTP practice uses the local URL printed by the instructor.

## Help, shortcuts, and errors

| Command or key | Purpose |
| --- | --- |
| `man grep` | Installed manual; `q` exits |
| `python3 --help` | Program help, when supported |
| `command -v python3` | Shell command resolution |
| `history` | Command history |
| Tab | Completion |
| Up | Recall earlier command |
| Ctrl+C | Usually interrupt foreground work |
| Ctrl+D | End input; may exit at an empty shell prompt |
| `clear` | Clear display |
| `exit` | Leave current shell |

- **No such file:** inspect `pwd`, `ls`, spelling, and quoting.
- **Command not found:** inspect spelling, installation, and resolution.
- **Permission denied:** inspect ownership, mode bits, parent directories, and ACLs.
- **No output:** some successful commands are silent; inspect the result.

## Mastery loop

State your goal, choose a command, explain its arguments, predict the result, run it, verify it, and repeat later with different files. Use references while learning. Being able to recover from mistakes matters more than memorising every option.
