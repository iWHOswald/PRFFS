from types import SimpleNamespace
import unittest

from prffs_api.services.espn_client import EspnFantasyClient


class EspnClientTests(unittest.TestCase):
    def test_live_scores_support_current_espn_owner_format(self):
        team = SimpleNamespace(team_id=1, team_name="Test team", owners=[{"firstName": "Test", "lastName": "Owner"}])
        matchup = SimpleNamespace(home_team=team, away_team=None, home_score=80.5, home_projected=105.0)
        client = EspnFantasyClient(league_id=917761, year=2026)
        client._league = SimpleNamespace(current_week=3, box_scores=lambda week: [matchup])
        scores = client.live_scores()
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0].owner, "Test Owner")
        self.assertEqual(scores[0].score, 80.5)
        self.assertEqual(scores[0].projected_score, 105.0)


if __name__ == "__main__":
    unittest.main()
