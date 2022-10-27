import time
from django.core.management.base import BaseCommand
from ...fetcher import *


class Command(BaseCommand):
    help = "Fetches new commits from the repository under test every 10 minutes"

    def handle(self, *args, **options):
        while True:
            fetch_main_branch_revisions()
            fetch_staging_revisions()
            print("Sleeping for 10 mins...")
            time.sleep(10 * 60)
