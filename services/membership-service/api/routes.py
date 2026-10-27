"""Foundation endpoints; functional IMembership operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'membership-service', 'name': 'Membership', 'interface': 'IMembership', 'requirements': 'FR-03, FR-04', 'tables': ['memberships', 'renewal_records', 'renewal_outbox', 'renewal_feed_state'], 'views': [], 'dependencies': {'IMemberProfile': 'http://member-service:8000'}, 'external_interfaces': []}

app = create_app(CONFIG)
