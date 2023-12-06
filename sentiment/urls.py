from django.urls import path
from .views import analyze_sentiment, bulk_upload, view_history

urlpatterns = [
    path('', analyze_sentiment, name='analyze_sentiment'),
    path('bulk-upload/', bulk_upload, name='bulk_upload'),
    path('history/', view_history, name='history'),
]