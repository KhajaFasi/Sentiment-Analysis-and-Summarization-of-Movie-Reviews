import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
import nltk

# Ensure nltk resources are available
nltk.download('vader_lexicon')

# Load the model and tokenizer from the saved files
model_directory = "fine_tuned_bert"  # Replace with the correct path to your model directory
model = AutoModelForSequenceClassification.from_pretrained(model_directory)
tokenizer = AutoTokenizer.from_pretrained(model_directory)

# Load pre-trained T5 model for summarization
summarizer = pipeline("summarization", model="t5-small")

# Sentiment analysis function for general sentiment (text as a whole)
def predict_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        logits = model(**inputs).logits
    sentiment = torch.argmax(logits, dim=1).item()  # Get the index of the highest score
    return sentiment

# Extract aspects using LDA
def extract_aspects(text, n_topics=3, n_words=5):
    # Tokenize text and apply LDA
    vectorizer = CountVectorizer(stop_words='english')
    X = vectorizer.fit_transform([text])
    
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)
    
    # Get top n_words for each topic
    feature_names = vectorizer.get_feature_names_out()
    aspects = []
    for topic_idx, topic in enumerate(lda.components_):
        top_words = [feature_names[i] for i in topic.argsort()[:-n_words - 1:-1]]
        aspects.append(" ".join(top_words))
    
    return aspects

# Visualize sentiment distribution with a pie chart
def visualize_sentiment(sentiment_data):
    df = pd.DataFrame(sentiment_data, columns=['Aspect', 'Sentiment', 'Count'])
    fig = px.pie(df, names='Sentiment', values='Count', title='Sentiment Distribution by Aspect')
    st.plotly_chart(fig)

# Generate Wordcloud from the input text
def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    # Create a figure and axis explicitly
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis('off')  # Hide axes
    
    # Now use st.pyplot with the figure object
    st.pyplot(fig)

# Summarize the input text using T5
def summarize_text(text):
    summary = summarizer(text, max_length=150, min_length=50, do_sample=False)
    return summary[0]['summary_text']

# Streamlit app interface
st.title("Sentiment Analysis and Summarization of Movie Reviews")

# Input text for sentiment analysis or summarization
input_text = st.text_area("Enter Movie Review Text", "")

analyze_button = st.button("Analyze Sentiment")
summarize_button = st.button("Summarize Text")
# Buttons for analyze and summarize
if input_text:    
    
    if analyze_button:
        # Perform general sentiment analysis and aspect-based sentiment analysis
        general_sentiment = predict_sentiment(input_text)
        general_sentiment_label = "Positive" if general_sentiment == 1 else "Negative"
        st.write(f"General Sentiment: {general_sentiment_label}")
        
        # Extract aspects using LDA
        aspects = extract_aspects(input_text, n_topics=3, n_words=5)
        
        # Predict sentiment for each aspect and store the results
        sentiment_data = []
        for aspect in aspects:
            sentiment = predict_sentiment(aspect)
            sentiment_label = "Positive" if sentiment == 1 else "Negative"
            sentiment_data.append([aspect, sentiment_label, 1])  # Each aspect gets a count of 1 (for visualization)
        
        # Visualize the sentiment distribution for each aspect
        visualize_sentiment(sentiment_data)
        
        # Generate word cloud from the text input
        generate_wordcloud(input_text)
    
    if summarize_button:
        # Summarize the text using T5
        summary = summarize_text(input_text)
        st.write(f"Abstractive Summary: {summary}")
