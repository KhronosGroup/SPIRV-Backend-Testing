from django.core.management.base import BaseCommand
from ...dispatcher import *


class Command(BaseCommand):
    help = "Cleans media files"

    def handle(self, *args, **options):
        dispose_dumps()
