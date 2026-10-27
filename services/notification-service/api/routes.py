"""Foundation endpoints; functional INotifications operations are not implemented yet."""
from gymarena_runtime import create_app

CONFIG = {'folder': 'notification-service', 'name': 'Notifications', 'interface': 'INotifications', 'requirements': 'FR-07, FR-08', 'tables': ['reminder_settings', 'reminder_offsets', 'reminder_jobs', 'message_records', 'delivery_attempts', 'message_status_events', 'renewal_cursors'], 'views': [], 'dependencies': {'IScoring': 'http://scoring-service:8000', 'IMembership': 'http://membership-service:8000'}, 'external_interfaces': ['IWhatsAppGateway']}

app = create_app(CONFIG)
