"""Foundation endpoints; functional IScoring operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'scoring-service', 'name': 'Scoring and Leaderboards', 'interface': 'IScoring', 'requirements': 'FR-15, FR-16', 'tables': ['member_scores', 'processed_sessions', 'score_entries', 'leaderboard_state', 'leaderboard_outbox', 'leaderboard_outbox_members', 'registration_cursors'], 'views': ['overall_leaderboard', 'comparable_leaderboard'], 'dependencies': {'IMemberProfile': 'http://member-service:8000', 'ISessionControl': 'http://session-service:8000'}, 'external_interfaces': []}

app = create_app(CONFIG)
