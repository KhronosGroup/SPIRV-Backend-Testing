from django.core.management.base import BaseCommand
from ...dispatcher import *



class Command(BaseCommand):
    help = 'Creates new jobs for newly fetched revisions'

    def handle(self, *args, **options):
        create_jobs()
