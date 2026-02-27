from django.core.management.base import BaseCommand
from gearapp.pahomqtt import mqtt_connect
import traceback

class Command(BaseCommand):
    help = 'Starts MQTT subscriber'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write(self.style.SUCCESS("🚀 Starting MQTT Subscriber..."))
            mqtt_connect()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ MQTT Error: {e}"))
            traceback.print_exc()
            raise



