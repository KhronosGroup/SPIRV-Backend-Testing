import time
from django.core.management.base import BaseCommand
from ...dispatcher import *


class Command(BaseCommand):
    help = "Creates new jobs for newly fetched revisions every 10 mins"

    def handle(self, *args, **options):
        while True:
            create_jobs()
            print("Sleeping for 10 mins...")
            time.sleep(10 * 60)
