from django.db import models

class CertificatePok(models.Model):
    certificate_id = models.CharField(max_length=255, unique=True)
    user_id = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)
    issued_at = models.DateTimeField()
    pok_url = models.URLField()
    raw_response = models.JSONField()

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course_id} - {self.user_id}"
