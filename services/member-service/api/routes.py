"""Foundation endpoints; functional IMemberProfile operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'member-service', 'name': 'Member Profiles and Measurements', 'interface': 'IMemberProfile', 'requirements': 'FR-09, FR-10', 'tables': ['members', 'weight_measurements', 'member_registered_outbox', 'registration_feed_state'], 'views': [], 'dependencies': {}, 'external_interfaces': ['IScaleInput']}

app = create_app(CONFIG)
