"""Foundation endpoints; functional IChallenge operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'challenge-service', 'name': 'Assessment and Challenges', 'interface': 'IChallenge', 'requirements': 'FR-13, FR-14', 'tables': ['assessments', 'level_approvals', 'current_levels', 'challenge_rule_versions', 'challenge_assignments'], 'views': [], 'dependencies': {'IMemberProfile': 'http://member-service:8000', 'IScoring': 'http://scoring-service:8000'}, 'external_interfaces': []}

app = create_app(CONFIG)
