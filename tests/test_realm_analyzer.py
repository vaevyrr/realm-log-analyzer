import unittest
from datetime import datetime
from realm_analyzer import parse_line

class ParserTests(unittest.TestCase):
    def test_join_line(self):
        event = parse_line("2026-02-01 12:30:00 [Server thread/INFO]: Alex joined the game", 4)
        self.assertIsNotNone(event)
        self.assertEqual(event.player, "Alex")
        self.assertEqual(event.event, "join")

    def test_leave_line(self):
        event = parse_line("2026-02-01 12:35:00 Steve left the game", 8)
        self.assertEqual(event.event, "leave")
        self.assertEqual(event.player, "Steve")

    def test_unrelated_line(self):
        self.assertIsNone(parse_line("Starting server...", 1))

if __name__ == "__main__":
    unittest.main()
