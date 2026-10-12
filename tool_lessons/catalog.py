"""Six-exercise starter lessons, with explicit live/GUI/evidence-review modes."""

import datetime
import hashlib
import json
import secrets
import shlex
import shutil
import stat

from lab_environment import PASSWORD, http_capture, make_common
from lesson_support import capture, read, task, write


# Order matches the original requested list; prerequisites determine study order.
TOOLS = [
    ("recon-ng", "Recon-ng", "offline workspace and source review", "https://github.com/lanmaster53/recon-ng/wiki/Features"),
    ("maltego", "Maltego", "guided GUI graph import", "https://docs.maltego.com/en/support/solutions/articles/15000010797-import-graph-from-table"),
    ("nmap", "Nmap", "live loopback scanning", "https://nmap.org/book/man-port-scanning-techniques.html"),
    ("wireshark", "Wireshark", "offline PCAP and guided GUI", "https://www.wireshark.org/docs/man-pages/tshark.html"),
    ("aircrack-ng", "Aircrack-ng", "wireless evidence orientation", "https://www.aircrack-ng.org/doku.php?id=cracking_wpa"),
    ("metasploit", "Metasploit", "live local auxiliary scanner", "https://docs.rapid7.com/metasploit/modules/"),
    ("hydra", "Hydra", "three-candidate local login test", "https://www.kali.org/tools/hydra/"),
    ("nikto", "Nikto", "bounded local web scan", "https://www.kali.org/tools/nikto/"),
    ("sqlmap", "sqlmap", "local in-memory SQL training app", "https://www.kali.org/tools/sqlmap/"),
    ("netcat", "netcat / Ncat", "live loopback banner connection", "https://nmap.org/book/ncat-man.html"),
    ("empire", "Empire", "framework orientation and evidence review", "https://bc-security.gitbook.io/empire-wiki"),
    ("john", "John the Ripper", "offline toy password hash", "https://www.kali.org/tools/john/"),
    ("powersploit", "PowerSploit", "legacy framework and benign PowerShell review", "https://github.com/PowerShellMafia/PowerSploit"),
    ("timestomp", "Timestomp", "owned-file timestamp concept lab", "https://attack.mitre.org/techniques/T1070/006/"),
    ("dnscat2", "dnscat2", "synthetic DNS evidence review", "https://github.com/iagox86/dnscat2"),
    ("burpsuite", "Burp Suite", "guided GUI Repeater on localhost", "https://portswigger.net/burp/documentation/desktop/tools/repeater"),
]


def build(slug, root, resources):
    entry = next(item for item in TOOLS if item[0] == slug)
    token = secrets.token_hex(3)
    make_common(root, slug, token)
    tasks = []
    details = ""
    scope = task("Guided: establish the lab's scope", ["Read the scope file before using this tool.", "Locate this session's case code."],
                 lambda a: a == token, "cat fixtures/scope.txt", "Read the Case code field.",
                 "Use the generated files and the printed loopback target for these exercises. Tool output is evidence to interpret, not a verdict.",
                 source="fixtures/scope.txt", submit="Enter only the case code.", guided=True)
    tasks.append(scope)

    def answer(title, steps, expected, command, clue, why, source=None):
        return task(title, steps, lambda a: a.strip().lower() == expected.lower(), command, clue, why,
                    source=source, submit="Enter the requested value only.")

    def summary(sentence):
        expected = sentence + "\n"
        return capture(root, "Challenge: record the lesson's conclusion", ["Create a one-line report containing the text below.", sentence],
                       "conclusion.txt", "printf '%s\\n' " + shlex.quote(sentence),
                       "Use an editor or printf, then inspect the saved report.", "Separate an observation from a confirmed security finding.", expected=expected)

    def optional(item, program):
        item["steps"] = item["steps"] + ["Needs {}. If unavailable, skip and continue the evidence exercises.".format(program)]
        item["requires"] = program
        if not shutil.which(program):
            item["steps"] += ["{} is not currently on this machine's command path.".format(program)]
        return item

    def gui(item):
        item["guided"] = True
        item["walkthrough"] = True
        return item

    if slug == "nmap":
        port = resources.web(token)
        write(root / "fixtures/example-scan.txt", "SYNTHETIC EXAMPLE, not a live scan\n8080/tcp open http\n8443/tcp filtered https\n")
        tasks += [
            optional(capture(root, "Scan one local port", ["Use a TCP connect scan against the one training port."], "scan.txt",
                             "nmap -sT -Pn -n -p {} 127.0.0.1".format(port), "-sT uses ordinary TCP connections; -p selects the printed port.",
                             "Open means a connection was accepted. It does not establish that the application is vulnerable.", pattern=r"{}/tcp\s+open".format(port)), "nmap"),
            answer("Interpret a supplied scan example", ["Read the clearly labelled synthetic example.", "Which port is filtered?"], "8443", "cat fixtures/example-scan.txt",
                   "Read the state column; do not substitute a likely service name for an observation.", "Filtered describes uncertainty caused by filtering or missing responses.", "fixtures/example-scan.txt"),
            optional(capture(root, "Inspect the local service", ["Add light version detection for the same single port."], "service.txt",
                             "nmap -sT -sV --version-light -Pn -n -p {} 127.0.0.1".format(port), "-sV probes the service; --version-light reduces probe selection.",
                             "A detected service name is a fingerprint, not a vulnerability confirmation.", pattern=r"{}/tcp\s+open".format(port)), "nmap"),
            capture(root, "Extract the example's open entry", ["Save only the synthetic example's open entry."], "open-example.txt", "grep ' open ' fixtures/example-scan.txt",
                    "Filter the state column using grep.", "Preserve the provenance of sample data; keep it separate from actual scan reports.", expected="8080/tcp open http\n"),
            summary("Open ports require application-level review"),
        ]
        details = "Nmap discovers and characterizes network services. This lab offers one live TCP port on 127.0.0.1. -sT does not require raw-packet privileges. Example scan excerpts are explicitly synthetic."

    elif slug == "netcat":
        port = resources.banner(token)
        program = "ncat" if shutil.which("ncat") else "nc"
        command = ("ncat --recv-only -w 2" if program == "ncat" else "nc -w 2") + " 127.0.0.1 " + str(port)
        write(root / "fixtures/banner-example.txt", "TRAINING sample-code\n")
        tasks += [
            optional(capture(root, "Connect and save a banner", ["Connect to the local banner server and save what it sends."], "banner.txt", command,
                             "The server sends one line and closes the connection. nc and Ncat have different options.", "netcat moves bytes; it does not automatically understand the application protocol.", expected="TRAINING " + token + "\n"), program),
            answer("Read the example's message type", ["Read the supplied banner example.", "Enter its first word."], "TRAINING", "cat fixtures/banner-example.txt",
                   "The first word identifies this toy message type.", "A banner is application data. Its claims should not be treated as trusted identity.", "fixtures/banner-example.txt"),
            optional(capture(root, "Inspect your variant's help", ["Capture the help output for the variant used here."], "netcat-help.txt",
                             program + " -h 2>&1", "Help output may be written to standard error; 2>&1 captures it with standard output.",
                             "Check your installed variant rather than assuming every nc/Ncat flag is interchangeable.", pattern=r"(?i)(usage|ncat|netcat)"), program),
            capture(root, "Keep a reference banner", ["Copy the supplied example into a report without changing it."], "banner-reference.txt", "cat fixtures/banner-example.txt",
                    "Use a different destination file from the one you are reading.", "The reference is synthetic; the live banner has this session's case code.", expected="TRAINING sample-code\n"),
            summary("A successful TCP connection does not prove a secure application"),
        ]
        details = "netcat and Ncat are related tools for TCP/UDP connections and byte streams. This starter uses only a loopback banner server. It does not launch shells or expose a listener on your network."

    elif slug == "wireshark":
        http_capture(root / "fixtures/http.pcap")
        tasks += [
            gui(task("Guided: open an offline capture", ["Open fixtures/http.pcap in Wireshark using File > Open.", "Apply the display filter http.request.", "Expand HTTP and read the request method."],
                     lambda a: a == "GET", "Use Wireshark's GUI to open the supplied PCAP.", "This is an offline, synthetic capture. No live capture privileges are needed.",
                     "The PCAP contains two valid synthetic packet records, not traffic captured from your computer. GUI interaction is self-reported.",
                     source="fixtures/http.pcap", submit="Enter the HTTP request method.")),
            optional(capture(root, "Filter requests with TShark", ["Read the PCAP and save its HTTP request method."], "methods.txt",
                             "tshark -r fixtures/http.pcap -Y http.request -T fields -e http.request.method", "-r reads a file; -Y applies a display filter; -e selects a field.",
                             "TShark is Wireshark's command-line companion. A display filter selects decoded packets.", expected="GET\n"), "tshark"),
            optional(capture(root, "Extract the response status", ["Read HTTP responses and save their status codes."], "status.txt",
                             "tshark -r fixtures/http.pcap -Y http.response -T fields -e http.response.code", "Select responses rather than requests.",
                             "HTTP 200 is an application response code, distinct from TCP connection state.", expected="200\n"), "tshark"),
            capture(root, "Inspect visible plaintext", ["Extract readable strings from this synthetic HTTP capture."], "plaintext.txt", "strings fixtures/http.pcap",
                    "HTTP in this fixture is unencrypted. strings is a rough content inspection, not protocol decoding.", "Seeing readable application content illustrates why transport encryption matters.", pattern=r"Hello reader"),
            summary("Packet evidence must be interpreted in protocol context"),
        ]
        details = "Wireshark decodes packet captures. This lab generates a synthetic Ethernet/IPv4/TCP PCAP with one HTTP request and response. GUI tasks are guided and self-reported; TShark output tasks can be checked."

    elif slug in ("nikto", "metasploit", "hydra", "sqlmap", "burpsuite"):
        port = resources.web(token)
        url = "http://127.0.0.1:" + str(port)
        if slug == "nikto":
            tasks += [
                capture(root, "Inspect the local response", ["Save the target's HTTP headers before scanning."], "headers.txt", "curl -sSI " + url,
                        "Start with a simple observation of the response.", "This training server intentionally omits some security headers.", pattern=r"X-Tool-Lab: " + token, guided=True),
                optional(task("Run a bounded web scan", ["Run Nikto against only the printed local URL.", "Limit it to 15 seconds and save a text report."],
                              lambda a: "127.0.0.1" in read(root / "reports/nikto.txt"),
                              "nikto -host " + url + " -maxtime 15s -timeout 2 -nocheck -ask no -nointeractive -nolookup -Format txt -output reports/nikto.txt",
                              "Use the host URL, maxtime, and output options shown by your installed help.", "Scanner findings need manual verification; a report is not proof of exploitation.", output="reports/nikto.txt"), "nikto"),
                capture(root, "Inspect robots.txt directly", ["Retrieve robots.txt to check what it actually says."], "robots.txt", "curl -sS " + url + "/robots.txt",
                        "Confirm an observation independently of the scanner.", "A robots entry is a crawler instruction, not access control.", expected="User-agent: *\nDisallow: /training-admin/\n"),
                answer("Evaluate a missing header", ["Inspect the saved headers.", "Does one missing security header alone prove a successful compromise?"], "no", "cat reports/headers.txt",
                       "A configuration observation and a compromise are different claims.", "Assess context, impact, and the relevant browser protections before drawing a conclusion."),
                summary("Scanner observations require manual verification"),
            ]
            details = "Nikto checks web-server configuration and known exposures. The local training scan disables update checks and submissions and has a short time limit. Findings here concern a deliberately simple training server."
        elif slug == "metasploit":
            module = "auxiliary/scanner/http/http_version"
            write(root / "fixtures/modules.txt", "SYNTHETIC ORIENTATION LIST\nauxiliary: scanner or utility\nexploit: vulnerability-triggering module\npayload: code executed through a session\n")
            tasks += [
                optional(capture(root, "Inspect a scanner module", ["Open the module's information in msfconsole and save it."], "module-info.txt",
                                 'msfconsole -q -n -x "info ' + module + '; exit -y"', "-n avoids database support; info describes a module without running it.",
                                 "Module type, options, and purpose should be understood before execution.", pattern=r"(?i)(http|scanner)"), "msfconsole"),
                optional(capture(root, "Run only the local HTTP scanner", ["Set RHOSTS to 127.0.0.1 and RPORT to the printed port.", "Run the auxiliary HTTP version scanner."], "scanner.txt",
                                 'msfconsole -q -n -x "use ' + module + '; set RHOSTS 127.0.0.1; set RPORT ' + str(port) + '; run; exit -y"',
                                 "This module inspects an HTTP service; no exploit or payload is needed.", "An auxiliary scanner result is not an exploit session.", pattern=r"TerminalToolLab|127\.0\.0\.1"), "msfconsole"),
                answer("Identify the module category", ["Read the orientation list.", "Which category includes this scanner?"], "auxiliary", "cat fixtures/modules.txt",
                       "The path begins with its category.", "Metasploit includes scanners and utilities as well as exploitation modules.", "fixtures/modules.txt"),
                capture(root, "Confirm the banner independently", ["Request the local HTTP headers with curl."], "confirmation.txt", "curl -sSI " + url,
                        "Compare direct HTTP evidence with a scanner fingerprint.", "Independent confirmation helps distinguish observations from tool assumptions.", pattern=r"TerminalToolLab"),
                summary("An auxiliary scanner does not establish exploitation"),
            ]
            details = "Metasploit organizes functionality into modules. This starter uses information lookup and an auxiliary HTTP scanner on a local target. Exploit sessions and payload operation require a separate controlled lab and are not simulated here."
        elif slug == "hydra":
            tasks += [
                capture(root, "Observe the authentication challenge", ["Request the protected local endpoint without credentials."], "unauthenticated.txt",
                        "curl -sS -o /dev/null -w '%{http_code}\\n' " + url + "/protected", "401 signals that this endpoint requires authentication.",
                        "This endpoint belongs to the lesson and uses one fictional account.", expected="401\n", guided=True),
                optional(task("Test only the three training candidates", ["Use username trainee and the supplied three-word file.", "Use one worker and stop after the first success."],
                              lambda a: PASSWORD in read(root / "reports/hydra.txt") and resources.auth_successes > 0,
                              "hydra -l trainee -P fixtures/words.txt -s {} -t 1 -f -o reports/hydra.txt 127.0.0.1 http-get /protected".format(port),
                              "-l supplies the user, -P the file, -s the port, -t the worker count, and -f stops after success.",
                              "This is an online authentication test against a loopback-only toy service, distinct from offline hash recovery.", output="reports/hydra.txt"), "hydra"),
                capture(root, "Verify the training credential", ["Make one authenticated request using the fictional credential."], "accepted.txt",
                        "curl -sS -u trainee:" + PASSWORD + " " + url + "/protected", "Use HTTP Basic credentials for this local endpoint.",
                        "A successful response verifies this training credential for this one service.", expected="Training login accepted\n"),
                answer("Count your candidate set", ["Count the supplied wordlist's lines."], "3", "wc -l fixtures/words.txt", "Keep the training candidate set small and explicit.",
                       "Authentication attempts have operational effects; scope and limits matter.", "fixtures/words.txt"),
                summary("Authentication defenses need rate limits and appropriate MFA"),
            ]
            details = "Hydra tests network authentication. This lab provides one fictional user, three candidates, and its own HTTP Basic endpoint. No external account or host is part of the exercise."
        elif slug == "sqlmap":
            write(root / "fixtures/request.txt", "GET /item?id=1 HTTP/1.1\nHost: 127.0.0.1:" + str(port) + "\n")
            comparison = "curl -sSG --data-urlencode 'id=1 AND 1=1' " + url + "/item\ncurl -sSG --data-urlencode 'id=1 AND 1=2' " + url + "/item"
            tasks += [
                capture(root, "Guided: compare true and false conditions", ["Request the deliberately unsafe item endpoint with true and false conditions.", "Save both response bodies in order."], "comparison.txt",
                        "{ " + comparison.replace("\n", "; ") + "; }", "The true condition selects Notebook; the false one selects no rows.",
                        "The response difference illustrates a data/input boundary failure in this toy query.", expected="Notebook\n\n", guided=True),
                optional(capture(root, "Check the one training parameter", ["Run a low-level boolean-only check for id on the unsafe endpoint.", "Keep concurrency at one and store output inside this lab."], "sqlmap.txt",
                                 'sqlmap -u "' + url + '/item?id=1" -p id --technique=B --batch --level=1 --risk=1 --threads=1 --timeout=3 --retries=0 --output-dir=reports/sqlmap',
                                 "The target is the generated in-memory application. B selects boolean-based techniques.",
                                 "This confirms only the intentionally unsafe training input. The database contains three fictional product names.", pattern=r"(?i)(boolean-based blind|parameter .?id.? is vulnerable)"), "sqlmap"),
                capture(root, "Compare the parameterized endpoint", ["Send the same true-condition text to safe-item, which uses a bound parameter."], "safe-response.txt",
                        "curl -sSG --data-urlencode 'id=1 AND 1=1' " + url + "/safe-item", "The safe endpoint treats the whole value as data rather than SQL syntax.",
                        "Parameterization preserves the code/data boundary for this query.", expected="\n"),
                answer("Identify the tested input", ["Inspect the supplied request.", "Name its query parameter."], "id", "cat fixtures/request.txt", "The name comes before = in the query string.",
                       "Record the specific input and endpoint, not just the tool's name.", "fixtures/request.txt"),
                summary("Fix: use parameterized database queries"),
            ]
            details = "sqlmap assesses SQL injection. The instructor creates a loopback-only app with an intentionally unsafe query and a parameterized comparison endpoint. Its SQLite database is in memory and contains fictional products."
        else:
            request = "GET /hello?name=reader HTTP/1.1\r\nHost: 127.0.0.1:{}\r\nConnection: close\r\n\r\n".format(port)
            write(root / "fixtures/request.txt", request)
            tasks += [
                gui(task("Guided: get a request into Repeater", ["Open Burp Suite and a temporary project.", "Use Burp's browser, with interception off, to open " + url + "/hello?name=reader.", "In HTTP history, send that request to Repeater and send it again."],
                         lambda a: "/hello?name=reader" in resources.requests, "curl -sS " + url + "/hello?name=reader",
                         "Keep the target HTTP, host 127.0.0.1, and the printed port. Use the official Repeater guide if your UI differs.",
                         "The instructor verifies a local request arrived, not that Burp generated it. GUI use is self-reported.")),
                gui(task("Guided: change one input", ["In Repeater, change only name=reader to name=analyst.", "Send it and inspect the response body."],
                         lambda a: a == "Hello analyst" and "/hello?name=analyst" in resources.requests,
                         "curl -sS " + url + "/hello?name=analyst", "Observe how changing one input changes the response.",
                         "Controlled changes help isolate cause and effect. This greeting endpoint is not a vulnerability demonstration.", submit="Enter the response body text.")),
                capture(root, "Save a response for review", ["Save an HTTP response from the analyst request. You can copy it from Repeater or use curl."], "response.txt",
                        "curl -sSi " + url + "/hello?name=analyst", "Include headers and the body in the report.",
                        "Preserved responses support review; request origin is not monitored.", pattern=r"Hello analyst"),
                answer("Read the input name", ["Read the original request and identify the query parameter name."], "name", "cat fixtures/request.txt",
                       "Separate the parameter's name from its value.", "Repeater lets you reissue and modify requests; interpret the resulting behavior.", "fixtures/request.txt"),
                summary("Changing input is not itself proof of a vulnerability"),
            ]
            details = "Burp Suite is a GUI web-testing toolkit. Repeater resends and modifies requests. These tasks use only the generated local HTTP service; the application-specific steps are guided and self-reported."

    elif slug == "john":
        tasks += [
            optional(task("Recover the one toy hash", ["Use John Jumbo's raw-md5 format and the supplied three candidates.", "Keep its pot and session files inside reports."],
                          lambda a: PASSWORD in read(root / "reports/john.pot"),
                          "john --format=raw-md5 --wordlist=fixtures/words.txt --pot=reports/john.pot --session=reports/john-session fixtures/hash.txt",
                          "Kali's Jumbo build supports raw-md5. A core-only build may not; skip if the format is unavailable.",
                          "This intentionally weak, unsalted training hash belongs to a fictional account. No network login is attempted.", output="reports/john.pot"), "john"),
            optional(capture(root, "Show recovered training results", ["Display the result using the same format and pot file."], "john-show.txt",
                             "john --show --format=raw-md5 --pot=reports/john.pot fixtures/hash.txt", "--show reads recovery results instead of starting a new search.",
                             "Record both the hash format and how the recovery result was obtained.", pattern=PASSWORD), "john"),
            answer("Count the supplied candidates", ["Count the wordlist's lines."], "3", "wc -l fixtures/words.txt", "This exercise supplies the candidate, not a realistic estimate of password strength.",
                   "A small successful dictionary demonstration does not predict all password-recovery outcomes.", "fixtures/words.txt"),
            task("Protect the training hash file", ["Give the hash file owner read/write and no group/other permissions."],
                 lambda a: stat.S_IMODE((root / "fixtures/hash.txt").stat().st_mode) == 0o600, "chmod 600 fixtures/hash.txt",
                 "Use the private-file mode from Lesson 3.", "Password-hash material should be handled as sensitive data, even though this fixture is fictional.", source="fixtures/hash.txt"),
            summary("Toy raw MD5 is not suitable password storage"),
        ]
        details = "John the Ripper tests offline password hashes. This starter needs a Jumbo build supporting raw-md5. It uses one generated, intentionally weak hash and three known candidates; it is not a real credential dataset."

    elif slug == "recon-ng":
        write(root / "fixtures/hosts.csv", "host,address,source\nweb.lab.invalid,192.0.2.10,supplied\nmail.lab.invalid,192.0.2.20,supplied\nweb.lab.invalid,192.0.2.10,supplied\n")
        write(root / "fixtures/module-requirements.txt", "TRAINING CHECKLIST\nRemote enrichment may need provider API keys.\nSource provenance must remain attached to claims.\n")
        tasks += [
            optional(capture(root, "Inspect a local workspace schema", ["Create a named training workspace and inspect its database schema.", "Disable version, analytics, and marketplace requests for this orientation."], "schema.txt",
                             "recon-cli --no-version --no-analytics --no-marketplace -w terminal-training-" + token + " -C 'db schema'",
                             "Workspaces separate investigations; db schema describes the local tables.", "This task performs no enrichment query. Recon-ng may store its workspace under your user profile.", pattern=r"(?i)(hosts|domains)"), "recon-cli"),
            capture(root, "Deduplicate supplied host records", ["Select the supplied host records and remove exact duplicate lines."], "hosts.txt",
                    "grep 'supplied' fixtures/hosts.csv | sort -u", "Keep the source field while deduplicating.", "Organization and provenance come before enrichment.",
                    expected="mail.lab.invalid,192.0.2.20,supplied\nweb.lab.invalid,192.0.2.10,supplied\n"),
            answer("Identify a record's source", ["Read the supplied records. What is the source field?"], "supplied", "cat fixtures/hosts.csv",
                   "These fictional records are provided by the lesson, not gathered from the internet.", "A claim without its source is difficult to evaluate.", "fixtures/hosts.csv"),
            capture(root, "Keep the module prerequisites", ["Save the checklist line mentioning API keys."], "prerequisites.txt", "grep 'API keys' fixtures/module-requirements.txt",
                    "Modules and providers have different prerequisites.", "A framework being installed does not mean every enrichment provider is available.", expected="Remote enrichment may need provider API keys.\n"),
            summary("Record provenance before performing enrichment"),
        ]
        details = "Recon-ng organizes reconnaissance into workspaces, database tables, and modules. This starter inspects a local schema and reviews supplied fictional records. Remote enrichment and provider-account setup are separate follow-up labs."

    elif slug == "maltego":
        write(root / "fixtures/relationships.csv", "source,target,relationship\nlab.invalid,web.lab.invalid,contains\nlab.invalid,mail.lab.invalid,contains\nweb.lab.invalid,192.0.2.10,resolves-to\n")
        tasks += [
            gui(task("Guided: import a supplied graph table", ["In Maltego Graph, import fixtures/relationships.csv as a third-party table.", "Map source and target to appropriate entities and relationship to links.", "Inspect the resulting graph; do not run enrichment transforms."],
                     lambda a: a.lower() == "done", "Follow Maltego's Graph Import Wizard; enter done afterward.",
                     "The official import wizard lets you map columns to entities and link properties. An account/edition may be needed.",
                     "This GUI completion is self-reported. Every relationship here is fictional supplied data.", source="fixtures/relationships.csv", submit="Enter done after the GUI walkthrough.")),
            answer("Find the mail entity", ["Inspect the supplied table or graph. Enter the entity containing mail."], "mail.lab.invalid", "grep 'mail' fixtures/relationships.csv",
                   "Read entity values, not just their positions in a layout.", "A graph visualizes records and their relationships; source reliability remains important.", "fixtures/relationships.csv"),
            capture(root, "Preserve one relationship", ["Save the row describing resolves-to."], "resolution.txt", "grep 'resolves-to' fixtures/relationships.csv",
                    "Keep both endpoints and the relationship name.", "An edge represents a supplied claim, not proof of a person or organization's identity.", expected="web.lab.invalid,192.0.2.10,resolves-to\n"),
            answer("Count the supplied relationships", ["Count the data rows, excluding the header."], "3", "tail -n +2 fixtures/relationships.csv | wc -l",
                   "A CSV header is not a relationship.", "Data quality affects the graph's interpretation.", "fixtures/relationships.csv"),
            summary("Graph relationships retain the uncertainty of their sources"),
        ]
        details = "Maltego Graph represents entities and links. This starter imports a fictional local CSV; it does not query real people or domains. GUI access and table-import availability depend on your installed edition/account."

    elif slug == "aircrack-ng":
        write(root / "fixtures/wireless-summary.csv", "SYNTHETIC TRAINING DATA, not a capture\nssid,bssid,channel,security\nTrainingAP,02:00:00:00:00:01,6,WPA2-PSK\nGuestExample,02:00:00:00:00:02,11,OPEN\n")
        tasks += [
            optional(capture(root, "Inspect the suite's help", ["Read aircrack-ng's installed help without selecting an interface or target."], "aircrack-help.txt",
                             "aircrack-ng --help 2>&1", "The suite has distinct capture, analysis, and key-recovery tools.",
                             "This orientation runs no radio capture or packet injection.", pattern=r"(?i)(aircrack|WPA)"), "aircrack-ng"),
            answer("Read the fictional AP's channel", ["Inspect the synthetic summary. Which channel does TrainingAP use?"], "6", "grep 'TrainingAP' fixtures/wireless-summary.csv",
                   "Channel and security type are separate fields.", "Metadata describes a supplied observation; it is not itself an authentication capture.", "fixtures/wireless-summary.csv"),
            capture(root, "Separate the open-network example", ["Save the row whose security field says OPEN."], "open-network.txt", "grep ',OPEN$' fixtures/wireless-summary.csv",
                    "Match the final field rather than a substring in a name.", "This example is synthetic and does not identify a real nearby network.", expected="GuestExample,02:00:00:00:00:02,11,OPEN\n"),
            answer("Evaluate the evidence type", ["Can this CSV summary substitute for a valid WPA/WPA2 authentication capture?"], "no", "cat fixtures/wireless-summary.csv",
                   "A table of AP properties does not contain the authentication exchange.", "Real wireless labs require an appropriate owned capture or suitable lab hardware; VM networking alone is not a monitor-mode radio."),
            summary("Wireless metadata is not an authentication handshake"),
        ]
        details = "Aircrack-ng is a wireless assessment suite. This is a help-and-evidence starter, not a wireless key-recovery lab. A later owned-AP lab needs compatible hardware or a valid supplied authentication capture."

    elif slug == "empire":
        write(root / "fixtures/events.txt", "SYNTHETIC TRAINING EVENTS, not Empire's native log format\nagent=lab-agent-01 event=REGISTER\nagent=lab-agent-01 event=CONNECT\nagent=lab-agent-01 event=CONNECT\nagent=lab-agent-01 event=CONNECT\n")
        tasks += [
            optional(capture(root, "Inspect framework entry-point help", ["Read the installed Empire entry point's help; do not start a server."], "empire-help.txt",
                             "powershell-empire -h", "Current maintained Empire differs from old tutorials. Check the installed help.",
                             "Entry-point help establishes available commands without deploying a listener, stager, or agent.", pattern=r"(?i)(server|setup|empire)"), "powershell-empire"),
            answer("Identify the fictional agent", ["Read the synthetic events. Enter their agent name."], "lab-agent-01", "cat fixtures/events.txt",
                   "These events are simplified teaching data, not an actual Empire trace.", "A framework identifier is a correlation key, not proof of a person's identity.", "fixtures/events.txt"),
            capture(root, "Extract the repeated events", ["Save the CONNECT entries with original line numbers."], "connections.txt", "grep -n 'event=CONNECT' fixtures/events.txt",
                    "Keep a reference to the original evidence lines.", "Repetition can motivate investigation; it does not by itself identify the framework used.", pattern=r"event=CONNECT"),
            answer("Count the repeated events", ["Count CONNECT entries in the synthetic events."], "3", "grep -c 'event=CONNECT' fixtures/events.txt",
                   "Count the selected event type, not the header or registration.", "This starter covers terminology and evidence review. Operational agent labs are a separate advanced track.", "fixtures/events.txt"),
            summary("Repeated connection events need contextual investigation"),
        ]
        details = "Empire is a post-exploitation framework; use documentation for the maintained BC Security project rather than assuming historical command syntax. This starter covers help, terminology, and explicitly synthetic evidence. It deploys no agent or listener."

    elif slug == "powersploit":
        write(root / "fixtures/inventory.ps1", "# Original benign teaching script, NOT a PowerSploit module.\nfunction Get-LabFiles { param([string]$Path) Get-ChildItem -LiteralPath $Path | Select-Object Name }\n")
        write(root / "fixtures/project-status.txt", "PowerShellMafia/PowerSploit: upstream repository archived on 2021-01-21.\nSource: https://github.com/PowerShellMafia/PowerSploit\n")
        tasks += [
            answer("Review a benign PowerShell function", ["Read the original teaching script. What function does it define?"], "Get-LabFiles", "cat fixtures/inventory.ps1",
                   "Read the name after function. This file is not copied from PowerSploit.", "Code review comes before running unfamiliar scripts.", "fixtures/inventory.ps1"),
            optional(capture(root, "Run the benign inventory example", ["If PowerShell is installed, load only the supplied benign script and list the lab fixtures."], "inventory.txt",
                             "pwsh -NoProfile -Command '. ./fixtures/inventory.ps1; Get-LabFiles -Path ./fixtures | ConvertTo-Json'",
                             "This exercise teaches PowerShell function/import mechanics; it is not a PowerSploit module execution.",
                             "The script only lists the provided directory. It demonstrates reviewing scope before execution.", pattern=r"inventory\.ps1"), "pwsh"),
            capture(root, "Preserve the provenance comment", ["Save the script's comment identifying its origin."], "provenance.txt", "grep '^#' fixtures/inventory.ps1",
                    "Keep original teaching examples distinct from upstream tool code.", "A familiar function style does not establish a script's source or trustworthiness.", expected="# Original benign teaching script, NOT a PowerSploit module.\n"),
            answer("Identify project status", ["Read the source-status note. Is the upstream repository archived?"], "yes", "cat fixtures/project-status.txt",
                   "Check upstream project status before following old installation instructions.", "Archived code can be studied, but compatibility and provenance require attention.", "fixtures/project-status.txt"),
            summary("Review script provenance and scope before execution"),
        ]
        details = "PowerSploit is a legacy PowerShell post-exploitation collection whose upstream repository is archived. This starter reviews project status and uses an original harmless inventory script to teach PowerShell mechanics; it does not execute upstream offensive modules."

    elif slug == "timestomp":
        write(root / "fixtures/timeline-note.txt", "Timestamp concept training\n")
        expected_hash = hashlib.sha256((root / "fixtures/timeline-note.txt").read_bytes()).hexdigest()
        baseline = {"sha256": expected_hash, "mtime": (root / "fixtures/timeline-note.txt").stat().st_mtime}
        write(root / "fixtures/baseline.json", json.dumps(baseline, indent=2) + "\n")
        tasks += [
            capture(root, "Inspect the recorded baseline", ["Save the file's original metadata/hash record as a report."], "baseline.txt", "cat fixtures/baseline.json",
                    "Separate content integrity from metadata.", "A hash describes file contents; mtime describes one timestamp.", expected=read(root / "fixtures/baseline.json")),
            task("Change only this lab file's modification time", ["Set the generated note's modification time to January 1, 2020, at midnight.", "Keep its contents unchanged."],
                 lambda a: datetime.datetime.fromtimestamp((root / "fixtures/timeline-note.txt").stat().st_mtime).strftime("%Y%m%d%H%M") == "202001010000"
                 and hashlib.sha256((root / "fixtures/timeline-note.txt").read_bytes()).hexdigest() == expected_hash,
                 "touch -m -t 202001010000 fixtures/timeline-note.txt", "-m selects the owned fixture's modification time; this does not demonstrate NTFS/Meterpreter behavior.",
                 "This is a filesystem concept exercise. Timestomp commonly refers to a technique or Meterpreter capability, not a generic Linux command.", source="fixtures/timeline-note.txt"),
            answer("Check content integrity", ["Hash the note's contents and compare with the saved baseline.", "Did the contents stay the same?"], "yes",
                   "python3 -c \"import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('fixtures/timeline-note.txt').read_bytes()).hexdigest())\"",
                   "Compare the SHA-256 value, not the displayed modification date.", "Metadata can change without changing a content hash.", "fixtures/timeline-note.txt"),
            answer("Interpret Unix ctime", ["What does Unix ctime record: creation time or metadata-change time?"], "metadata-change time",
                   "man stat", "Unix ctime is not a portable creation-time field.", "Timestamp meanings differ across filesystems and platforms. A single date is not a complete timeline."),
            summary("A file timestamp alone does not prove its history"),
        ]
        details = "Timestomping concerns timestamp manipulation. This starter modifies only a newly generated lab file with touch and compares metadata with content integrity. It is not a Meterpreter session or an NTFS MFT experiment."

    elif slug == "dnscat2":
        write(root / "fixtures/dns-events.csv", "SYNTHETIC DNS-LIKE EVIDENCE, not dnscat2 wire format\nclient,type,name\nlab-client,A,ordinary.lab.invalid\nlab-client,TXT,747261696e696e67.tunnel.lab.invalid\nlab-client,TXT,68656c6c6f.tunnel.lab.invalid\n")
        tasks += [
            optional(capture(root, "Inspect client help", ["Read the installed client's help without making a connection."], "dnscat-help.txt",
                             "dnscat --help 2>&1", "Kali's client binary is named dnscat; dnscat2 names the project/package.",
                             "Help orientation does not create a tunnel. This starter reviews synthetic DNS-like evidence.", pattern=r"(?i)(dnscat|usage)"), "dnscat"),
            capture(root, "Extract the TXT examples", ["Select TXT entries from the synthetic evidence."], "txt-events.txt", "grep ',TXT,' fixtures/dns-events.csv",
                    "Query type is one clue; do not assume all TXT use is malicious.", "These records are teaching examples, not an authentic dnscat2 capture.", pattern=r"747261696e696e67"),
            answer("Decode the harmless example label", ["Decode the hex label 747261696e696e67 as UTF-8."], "training",
                   "python3 -c \"print(bytes.fromhex('747261696e696e67').decode())\"", "This demonstrates encoding, not decryption of a real tunnel.",
                   "Readable encoded content can motivate further analysis, but ordinary services also encode data.", "fixtures/dns-events.csv"),
            answer("Count the TXT records", ["Count the TXT data rows."], "2", "grep -c ',TXT,' fixtures/dns-events.csv",
                   "Select the record type and exclude the header.", "Frequency, labels, endpoints, and baseline context are needed for a useful investigation.", "fixtures/dns-events.csv"),
            summary("DNS anomalies require context before attributing a tunnel"),
        ]
        details = "dnscat2 carries a command channel over DNS. This starter covers client-help orientation and synthetic DNS evidence; it does not deploy a command channel or emulate dnscat2 encryption/wire format."

    if resources.port:
        target = ("127.0.0.1:" if slug == "netcat" else "http://127.0.0.1:") + str(resources.port)
        write(root / "fixtures/scope.txt", read(root / "fixtures/scope.txt") + "Live target: " + target + "\n")
        for item in tasks:
            item["target"] = target
    assert len(tasks) == 6, (slug, len(tasks))
    return dict(title=entry[1].upper() + " STARTER", tasks=tasks, learn=[
        ("Purpose and prerequisites", details + "\n\nOfficial reference: " + entry[3]),
        ("How this starter is checked", "The instructor never installs or runs the security tool for you. Run commands in the other tab. Missing tools can be skipped; evidence-review tasks still work.\n\nSome tasks need earlier output files. Use hint to recreate a missing prerequisite. GUI use is self-reported. Synthetic artifacts are labelled; live reports and sample evidence must remain distinct.\n\nKeep active tests on the printed local target. This is an introduction, not proof of tool mastery."),
    ])
