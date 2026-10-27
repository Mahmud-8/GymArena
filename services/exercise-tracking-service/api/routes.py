"""Foundation endpoints; functional IExerciseTracking operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'exercise-tracking-service', 'name': 'Exercise Tracking', 'interface': 'IExerciseTracking', 'requirements': 'FR-01, FR-02', 'tables': ['exercise_configs', 'phase_rules', 'tracking_diagnostics'], 'views': [], 'dependencies': {}, 'external_interfaces': ['ICameraFeed']}

app = create_app(CONFIG)
