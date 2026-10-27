"""Foundation endpoints; functional IRecognition operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'recognition-service', 'name': 'Face Recognition', 'interface': 'IRecognition', 'requirements': 'FR-11, FR-12', 'tables': ['face_enrollments', 'face_references', 'identity_contexts'], 'views': [], 'dependencies': {'IMemberProfile': 'http://member-service:8000'}, 'external_interfaces': ['ICameraFeed']}

app = create_app(CONFIG)
