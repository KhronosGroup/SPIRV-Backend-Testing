import time
from django.core.management.base import BaseCommand
from ...dispatcher import *


class Command(BaseCommand):
    help = "Cleans media files every 24 hours"

    def handle(self, *args, **options):
        while True:
            dispose_dumps()
            print("Sleeping for 24 hours...")
            time.sleep(24 * 60 * 60)
