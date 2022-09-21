from django.core.management.base import BaseCommand
from ...fetcher import *

class Command(BaseCommand):
    help = 'Fetches new commits from the repository under test'

    def handle(self, *args, **options):
        fetch_main_branch_revisions()
        fetch_staging_revisions()
