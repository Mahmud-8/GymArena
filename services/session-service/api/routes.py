"""Foundation endpoints; functional ISessionControl operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'session-service', 'name': 'Session Control', 'interface': 'ISessionControl', 'requirements': 'FR-05, FR-06', 'tables': ['sessions', 'session_participants', 'participant_rule_snapshots', 'session_interruptions', 'session_outcomes'], 'views': [], 'dependencies': {'IMemberProfile': 'http://member-service:8000', 'IRecognition': 'http://recognition-service:8000', 'IExerciseTracking': 'http://exercise-tracking-service:8000', 'IChallenge': 'http://challenge-service:8000'}, 'external_interfaces': []}

app = create_app(CONFIG)
