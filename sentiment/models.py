from django.db import models

# Create your models here.

class SentimentAnalysis(models.Model):
    review_text = models.TextField()
    sentiment = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sentiment
