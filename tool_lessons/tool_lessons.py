#!/usr/bin/env python3
"""Choose a tool starter lesson after the terminal foundation course."""

import argparse

from catalog import TOOLS, build
from lab_environment import ToolResources
from lesson_support import run_lesson


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", nargs="?", choices=[item[0] for item in TOOLS])
    parser.add_argument("--list", action="store_true", help="List all sixteen tool starters")
    parser.add_argument("--no-clear", action="store_true", help="Keep earlier screens visible")
    args = parser.parse_args()
    if args.list or args.tool is None:
        print("TOOL STARTER TRACK | Lessons 7-22")
        for number, (slug, name, mode, _) in enumerate(TOOLS, 7):
            print("{:2}. {:14} {}".format(number, slug, mode))
        print("\nStart with: netcat, nmap, wireshark, then burpsuite.")
        print("Example: python3 tool_lessons/tool_lessons.py nmap")
        return
    number = next(index for index, item in enumerate(TOOLS, 7) if item[0] == args.tool)
    run_lesson(number, lambda root, resources: build(args.tool, root, resources),
               argv=["--no-clear"] if args.no_clear else [], resource_factory=ToolResources)


if __name__ == "__main__":
    main()
