# Tool starter lessons

These introductions follow the terminal foundations. Each has two short teaching screens and six exercises. They are not certifications or complete operational courses for the tools.

## Run a lesson

From the repository folder:

```bash
python3 tool_lessons/tool_lessons.py --list
python3 tool_lessons/tool_lessons.py nmap
```

Use two terminal tabs as in Lessons 1–6. Copy the generated `cd` command into the command tab. The instructor shows the current local target when a service is involved. Add `--no-clear` to keep previous screens visible.

`hint` provides a clue; a second `hint` shows an example. `task` redraws the instructions, `skip` moves on, and `quit` stops the session. Every run creates a fresh temporary environment. Files remain for review; short-lesson progress does not resume.

## Catalogue and references

| Lesson | Run argument | Focus and actual exercise mode | Official reference |
| --- | --- | --- | --- |
| 7 | `recon-ng` | Optional local workspace/schema inspection; supplied host records and provenance. No remote enrichment. | [Recon-ng features](https://github.com/lanmaster53/recon-ng/wiki/Features) |
| 8 | `maltego` | Guided GUI import of a fictional relationship CSV; entity/edge review. No transforms. | [Graph import wizard](https://docs.maltego.com/en/support/solutions/articles/15000010797-import-graph-from-table) |
| 9 | `nmap` | One-port TCP connect scan and light service detection against the lab's loopback server. | [Nmap scan techniques](https://nmap.org/book/man-port-scanning-techniques.html) |
| 10 | `wireshark` | Offline synthetic HTTP PCAP; guided GUI filters and checked TShark field extraction. | [TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html) |
| 11 | `aircrack-ng` | Installed help and synthetic AP-summary review. No radio capture, injection, or key recovery. | [Aircrack-ng WPA capture requirements](https://www.aircrack-ng.org/doku.php?id=cracking_wpa) |
| 12 | `metasploit` | Module information and the auxiliary HTTP version scanner against localhost. No exploit/payload session. | [Metasploit modules](https://docs.rapid7.com/metasploit/modules/) |
| 13 | `hydra` | One fictional user, three supplied candidates, one worker, local HTTP Basic service. | [Kali Hydra reference](https://www.kali.org/tools/hydra/) |
| 14 | `nikto` | Local web scan with a 15-second limit; direct verification of response headers and robots.txt. | [Kali Nikto reference](https://www.kali.org/tools/nikto/) |
| 15 | `sqlmap` | Boolean-only assessment of one local parameter; comparison with a bound-parameter endpoint. | [Kali sqlmap reference](https://www.kali.org/tools/sqlmap/) |
| 16 | `netcat` | Receive a loopback training banner; inspect nc/Ncat variant help. | [Ncat reference](https://nmap.org/book/ncat-man.html) |
| 17 | `empire` | Entry-point help and explicitly synthetic event review. No agent/listener deployment. | [Maintained Empire documentation](https://bc-security.gitbook.io/empire-wiki) |
| 18 | `john` | Offline recovery of one generated toy raw-MD5 hash from three supplied candidates; file permissions. | [Kali John reference](https://www.kali.org/tools/john/) |
| 19 | `powersploit` | Archived-project orientation and an original harmless PowerShell inventory function. Not execution of an upstream module. | [PowerSploit upstream](https://github.com/PowerShellMafia/PowerSploit) |
| 20 | `timestomp` | Modify only a generated file's timestamp and compare metadata with content integrity. Not an NTFS/Meterpreter session. | [MITRE timestomp technique](https://attack.mitre.org/techniques/T1070/006/) |
| 21 | `dnscat2` | Client-help orientation and synthetic DNS-like evidence review. No tunnel or native-protocol emulation. | [dnscat2 upstream](https://github.com/iagox86/dnscat2) |
| 22 | `burpsuite` | Guided GUI Repeater against the local greeting endpoint; preserve and compare HTTP responses. | [Burp Repeater](https://portswigger.net/burp/documentation/desktop/tools/repeater) |

Suggested order: netcat → Nmap → Wireshark → Burp → Nikto → sqlmap → John/Hydra → Recon-ng/Maltego. Wireless and post-exploitation framework work requires additional prerequisites; use these starters for orientation before a dedicated lab.

## Tool prerequisites and honest limits

The Python instructor uses only the standard library. It never installs or launches a security tool automatically. Use a machine with the relevant tool installed, usually your Kali VM, or skip a missing-tool task. Check installation with `command -v TOOL` and follow the linked official documentation for your version. Package/command names differ: netcat may be `nc` or `ncat`, the Kali dnscat2 client is `dnscat`, and maintained Empire's Kali entry point is `powershell-empire`.

John's exercise needs a Jumbo build supporting `raw-md5`; a core-only build may not include it. The hash and password are intentionally weak, fictional teaching data. Maltego's account/edition can affect access to import features. Burp and Maltego require a graphical desktop. Read the installed CLI help if options differ.

PowerSploit's upstream repository is archived. The supplied inventory function is original teaching code, clearly labelled as such, and does not claim to be a PowerSploit module. Empire and dnscat2 lessons use explicitly synthetic evidence, not authentic framework logs or protocol captures. Timestomp is also a technique/capability name; the Unix exercise uses `touch` on an owned fixture and makes no claim about NTFS timestamp semantics.

Aircrack-ng's starter does not include an authentication handshake. A VM's virtual network adapter is not a monitor-mode Wi-Fi radio. A future owned-access-point lab needs a compatible adapter or a valid, appropriately sourced offline authentication capture.

## What runs locally

The active lab server binds only to `127.0.0.1` on an automatically chosen port. It provides toy HTTP responses, one fictional Basic-auth account, or an intentionally unsafe SQLite query over three in-memory product records. The parameterized comparison endpoint treats input as data. Netcat uses a separate one-line banner service. The instructor stops its own service on exit; files stay available for review.

The Wireshark PCAP is generated from two synthetic Ethernet/IPv4/TCP packet records. It uses documentation addresses and contains no captured user traffic. CSVs and event snippets are marked synthetic. No actual passwords, captures, third-party module code, or account API keys are redistributed.

Scope active commands to the printed local target. Keep the instructor running while using it. Stop any manually launched tool before quitting the instructor. Do not replace the lesson target with an unrelated host. Some tools may use their own user-profile directories: Recon-ng's workspace, for example, is managed by Recon-ng rather than this instructor.

## What the tests establish

Tests validate the catalogue, generated fixtures, loopback binding, auth/query behavior, PCAP container, entry points, available CLI recipes, report checks, and GUI grading labels. They do not automate GUI interaction, demonstrate wireless key recovery, install framework agents, or exercise PowerSploit modules.

The dedicated Linux job installs Nmap, TShark, Hydra, sqlmap, Aircrack-ng, netcat, and John. John recovery is skipped when that build lacks raw-MD5 support. Other framework/tool invocations require a separately provisioned manual lab. Passing fixture/report tests is not proof that every upstream tool/version was exercised.

Build on these starters with deeper tool-specific lessons once learners can explain the observations, limits, and prerequisites.
