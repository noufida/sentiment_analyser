import pandas as pd
from django.shortcuts import render, redirect
from .models import SentimentAnalysis
from .forms import SentimentAnalysisForm, BulkUploadForm
from transformers import pipeline
import csv
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def perform_sentiment_analysis(review_text):
    classifier = pipeline('sentiment-analysis',model="nlptown/bert-base-multilingual-uncased-sentiment")
    result = classifier(review_text)
    star = int(result[0]['label'][0])
    score = result[0]['score']
    if (star == 2 and score>0.66) or star == 3  or (star==4 and score<0.33):
        return 'NEUTRAL',result[0]['label']
    elif star<3:
        return 'NEGATIVE',result[0]['label']
    else:
        return 'POSITIVE',result[0]['label']


# def perform_sentiment_analysis(review_text):
#     classifier = pipeline('sentiment-analysis')
#     result = classifier(review_text)
#     return result[0]['label']

def calculate_sentiment_summary(results):
    sentiments = [result.sentiment for result in results]

    total_reviews = len(sentiments)
    positive_reviews = sentiments.count('POSITIVE')
    negative_reviews = sentiments.count('NEGATIVE')
    neutral_reviews = sentiments.count('NEUTRAL')

    positive_percentage = (positive_reviews / total_reviews) * 100
    negative_percentage = (negative_reviews / total_reviews) * 100
    neutral_percentage = (neutral_reviews / total_reviews) * 100

    majority_sentiment = max(set(sentiments), key=sentiments.count)

    return {
        'total_reviews': total_reviews,
        'positive_reviews': positive_reviews,
        'negative_reviews': negative_reviews,
        'neutral_reviews': neutral_reviews,
        'positive_percentage': positive_percentage,
        'negative_percentage': negative_percentage,
        'neutral_percentage': neutral_percentage,
        'majority_sentiment': majority_sentiment
    }


def analyze_sentiment(request):
    if request.method == 'POST':
        form = SentimentAnalysisForm(request.POST)
        if form.is_valid():
            review_text = form.cleaned_data['review_text']
            sentiment,star_rating = perform_sentiment_analysis(review_text)
            result = SentimentAnalysis.objects.create(
                review_text=review_text,
                sentiment=sentiment
            )
            context ={
                'result': result,
                'star_rating': star_rating
            }
            return render(request, 'result.html', context)
    else:
        form = SentimentAnalysisForm()
        form_bulk = BulkUploadForm()


    return render(request, 'analyze_sentiment.html', {'form': form, 'form_bulk':form_bulk})

def bulk_upload(request):
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            df = pd.read_csv(csv_file)

            review_texts = df['Review']

            analysis_results = []
            for review_text in review_texts:
                sentiment = perform_sentiment_analysis(review_text)
                result = SentimentAnalysis.objects.create(
                    review_text=review_text,
                    sentiment=sentiment
                )
                analysis_results.append(result)

            summary = calculate_sentiment_summary(analysis_results)

            # Generate a bar chart
            labels = ['Positive', 'Negative', 'Neutral']
            values = [summary['positive_reviews'], summary['negative_reviews'], summary['neutral_reviews']]

            plt.bar(labels, values)
            plt.title('Sentiment Distribution')
            plt.xlabel('Sentiment')
            plt.ylabel('Count')

            # Save the plot to a BytesIO object
            img_data = BytesIO()
            plt.savefig(img_data, format='png')
            img_data.seek(0)
            plt.close()

            # Convert the BytesIO object to base64 for embedding in HTML
            img_base64 = base64.b64encode(img_data.getvalue()).decode('utf-8')


            return render(request, 'bulk_result.html', {'results': analysis_results, 'summary': summary,'chart': img_base64})
    else:
        form = BulkUploadForm()

    return render(request, 'bulk_upload.html', {'form': form})



def view_history(request):
    results = SentimentAnalysis.objects.all().order_by('-id')

    if request.method == 'POST' and 'download_csv' in request.POST:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sentiment_history.csv"'

        writer = csv.writer(response)
        writer.writerow(['Review Text', 'Sentiment', 'Created At'])

        for result in results:
            writer.writerow([result.review_text, result.sentiment, result.created_at])

        return response

    # Set the number of results per page
    results_per_page = 10
    paginator = Paginator(results, results_per_page)

    page = request.GET.get('page', 1)

    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)
    
    context = {
        'results': results
    }
    return render(request, 'history.html', context)