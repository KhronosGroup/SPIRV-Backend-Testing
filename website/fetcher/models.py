from django.db import models
from django.utils.translation import gettext_lazy as _
import bleach


# Model representing a single commit in the staging repository
class Revision(models.Model):
    title = models.CharField(max_length=100)
    hash = models.CharField(max_length=40, primary_key=True)
    branch = models.CharField(max_length=100)
    staging = models.BooleanField(default=True)
    date = models.DateTimeField()
    skip = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Revision " + self.hash[:16] + " / " + self.title[:80]

    class Meta:
        ordering = ["-date"]

    def sanitize(self):
        """
        Sanitizes the object's data before passing to a view.
        """
        self.title = bleach.clean(self.title)
