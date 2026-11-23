#!/usr/bin/env python3
"""Summarize player joins and leaves from text logs."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

STAMP = r"(?P<stamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})"
PATTERNS = [
    re.compile(STAMP + r".*?:?\s*(?P<player>.+?) joined the game\b", re.I),
    re.compile(STAMP + r".*?:?\s*(?P<player>.+?) left the game\b", re.I),
    re.compile(STAMP + r".*?Player connected:\s*(?P<player>[^,]+)", re.I),
    re.compile(STAMP + r".*?Player disconnected:\s*(?P<player>[^,]+)", re.I),
]

@dataclass
class Event:
    timestamp: datetime
    player: str
    event: str
    line_number: int

@dataclass
class Session:
    player: str
    joined: datetime
    left: datetime | None

def parse_line(line: str, line_number: int) -> Event | None:
    for index, pattern in enumerate(PATTERNS):
        match = pattern.search(line)
        if not match:
            continue
        try:
            stamp = datetime.fromisoformat(match.group("stamp").replace(" ", "T"))
        except ValueError:
            return None
        event = "join" if index in (0, 2) else "leave"
        player = match.group("player").strip().strip("[]")
        if player:
            return Event(stamp, player, event, line_number)
    return None

def analyze(path: Path) -> tuple[list[Event], list[Session], int]:
    events: list[Event] = []
    total_lines = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            total_lines += 1
            event = parse_line(line, number)
            if event:
                events.append(event)
    events.sort(key=lambda e: (e.timestamp, e.line_number))
    active: dict[str, list[datetime]] = {}
    sessions: list[Session] = []
    for event in events:
        if event.event == "join":
            active.setdefault(event.player, []).append(event.timestamp)
        else:
            starts = active.get(event.player, [])
            if starts:
                sessions.append(Session(event.player, starts.pop(0), event.timestamp))
    for player, starts in active.items():
        sessions.extend(Session(player, start, None) for start in starts)
    sessions.sort(key=lambda s: s.joined)
    return events, sessions, total_lines

def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)

def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze player activity in a text log.")
    parser.add_argument("log", type=Path)
    parser.add_argument("--events", type=Path, default=Path("events.csv"))
    parser.add_argument("--players", type=Path, default=Path("players.csv"))
    args = parser.parse_args()
    if not args.log.is_file():
        parser.error(f"log file does not exist: {args.log}")
    try:
        events, sessions, line_count = analyze(args.log)
        counts = Counter(event.player for event in events if event.event == "join")
        durations: dict[str, int] = Counter()
        open_sessions: Counter[str] = Counter()
        for session in sessions:
            if session.left is None:
                open_sessions[session.player] += 1
            else:
                durations[session.player] += max(0, int((session.left - session.joined).total_seconds()))
        write_csv(args.events, ["timestamp", "player", "event", "line"], [
            [e.timestamp.isoformat(sep=" "), e.player, e.event, e.line_number] for e in events
        ])
        names = sorted(set(counts) | set(durations) | set(open_sessions), key=str.casefold)
        write_csv(args.players, ["player", "joins", "matched_play_seconds", "open_sessions"], [
            [name, counts[name], durations[name], open_sessions[name]] for name in names
        ])
    except OSError as exc:
        print(f"Could not process log: {exc}", file=sys.stderr)
        return 2
    print(f"Read {line_count} lines; found {len(events)} player events and {len(sessions)} sessions.")
    print(f"Wrote {args.events} and {args.players}")
    if not events:
        print("No supported join/leave lines were found. Check the log format and parser patterns.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
