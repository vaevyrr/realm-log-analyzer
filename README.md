# Realm Log Analyzer

A local CLI for turning Minecraft server and Realm-style text logs into a player activity report. It recognizes common join/leave wording, tracks sessions when both events exist, and exports the events and session totals to CSV.

## Requirements

Python 3.10+. No external packages.

## Run

```bash
python realm_analyzer.py path/to/server.log
python realm_analyzer.py path/to/server.log --events events.csv --players players.csv
```

The parser is deliberately conservative: unknown lines are counted, not guessed. Log formats differ between server software and versions, so add patterns in `realm_analyzer.py` if your log uses different wording.

## Tests

```bash
python -m unittest discover -s tests -v
```

MIT License.
