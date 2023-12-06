from django import forms

class SentimentAnalysisForm(forms.Form):
    review_text = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter your review here...', 'rows': 5, 'cols': 40})
    )

class BulkUploadForm(forms.Form):
    csv_file = forms.FileField()
    