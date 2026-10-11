#!/usr/bin/env python3
"""Lesson 5: interfaces, routes, ports, HTTP, and optional DNS."""

import platform
import secrets

from lesson_support import capture, run_lesson, task


def build_lesson(root, resources):
    token = secrets.token_hex(3)
    port = resources.http(token)
    system = platform.system()
    mac = system == "Darwin"
    addresses = "ifconfig" if mac else "ip -br address"
    routes = "route -n get default" if mac else "ip route"
    local_route = "route -n get 127.0.0.1" if mac else "ip route get 127.0.0.1"
    listeners = "lsof -nP -iTCP -sTCP:LISTEN" if mac else "ss -lnt"
    url = "http://127.0.0.1:{}/".format(port)
    tasks = [
        capture(root, "Guided: test loopback", ["Send THREE echo requests to your own machine.", "Capture the replies and summary."],
                "loopback-ping.txt", "ping -c 3 127.0.0.1", "-c limits the request count.",
                "Loopback reaches this machine. Ping tests ICMP replies, not whether HTTP or DNS works.", pattern=r"0(?:\.0)?% packet loss", guided=True),
        capture(root, "Inspect network interfaces", ["Show your network interfaces and their IP addresses."], "interfaces.txt", addresses,
                "Mac: ifconfig. Kali/Linux: ip -br address.", "A machine can have multiple interfaces and multiple addresses. Interface names are not IP addresses.", pattern=r"127\.0\.0\.1"),
        task("Identify the loopback address", ["Find the loopback interface in your address output.", "Identify its IPv4 address."],
             lambda a: a == "127.0.0.1", addresses, "Look for lo0 on Mac or lo on Linux. The /prefix is separate from the address.",
             "127.0.0.1 is the IPv4 loopback address used in this lab; it does not identify another computer on your Wi-Fi.", submit="Enter the IPv4 address only."),
        capture(root, "Inspect the default route", ["Show the default route and next-hop information.", "If this machine has no default route, type skip."],
                "default-route.txt", routes, "Mac: route -n get default. Kali/Linux: ip route.",
                "The default route is a fallback when no more specific route matches. Its presence does not prove internet access.", pattern=r"gateway:" if mac else r"^default"),
        capture(root, "Inspect the route to yourself", ["Ask the OS which route it uses for 127.0.0.1."], "local-route.txt", local_route,
                "Inspect the destination's selected route rather than assuming every packet uses the default gateway.",
                "A local loopback destination uses a local route. More specific routing information takes precedence over the default route.", pattern=r"\blo0\b" if mac else r"\b(local|lo)\b"),
        capture(root, "Locate the listening port", ["List listening TCP sockets.", "Locate the training port {}.".format(port)], "listeners.txt", listeners,
                "Keep port numbers numeric: lsof -nP on Mac, ss -n on Linux.",
                "An IP address identifies a network endpoint; a port helps select a particular service at that endpoint.", pattern=r":{}\b".format(port)),
        capture(root, "Request HTTP headers", ["Make a HEAD request to the local service."], "headers.txt", "curl -sSI " + url,
                "curl -I asks for response headers without the response body.",
                "The status line and headers show the service responded. They are different evidence from a successful ping.", pattern=r"(?i)X-Lesson-Code: " + token, source=url),
        capture(root, "Read an HTTP response body", ["Retrieve the training service's response body."], "body.txt", "curl -sS " + url,
                "Without -I, curl makes a GET request by default.",
                "GET retrieves the response body. HEAD inspects its headers. Both requests here stay on your own machine.", expected="Training server\nCase code: {}\n".format(token), source=url),
        capture(root, "Optional: query DNS", ["If dig is installed and DNS is available, query example.com.", "Otherwise skip this optional task."], "dns.txt", "dig example.com",
                "DNS lookups ask your configured resolver about names and records.",
                "DNS resolution, IP connectivity, and an HTTP response are separate things to investigate. This optional task contacts your configured DNS resolver.", pattern=r"status: NOERROR"),
        task("Challenge: evaluate your evidence", ["Review the interface, route, ping, and HTTP reports.", "Consider only the IP address and default route: do those two prove every website is reachable?"],
             lambda a: a.lower() == "no", "cat reports/interfaces.txt\ncat reports/default-route.txt",
             "Configuration tells you the intended path. Destination, DNS, filtering, and application behavior still matter.",
             "A good investigation separates configured settings from observed behavior. Your loopback HTTP test demonstrated one local service, not the whole internet.", submit="Enter yes or no, then explain your reasoning out loud."),
    ]
    return dict(title="NETWORKING BASICS", tasks=tasks, learn=[
        ("Address, interface, gateway, port", "Interface: a network connection. IP address: an address on an interface. Default gateway: the next router for traffic using a default route. Port: selects a service at an endpoint.\n\nMac and Kali use different inspection commands. The tasks pick commands for this machine."),
        ("Test one layer at a time", "127.0.0.1 means this machine. We will test it with ping, inspect a listening TCP port, and request an HTTP response.\n\nEach observation answers a different question. DNS maps names to records and is a separate check. DNS practice is optional; other network tasks are local inspection or loopback."),
    ])


if __name__ == "__main__":
    run_lesson(5, build_lesson)
