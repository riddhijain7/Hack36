from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from flask_cors import CORS
from webdriver_manager.chrome import ChromeDriverManager as CM
import spacy
import time
import joblib
import statistics

nlp = spacy.load("en_core_web_sm")

application = Flask(__name__)
CORS(application)

# Importing logistic regression and standard scaler pickle.
pipeline = joblib.load("./models/pipeline.pkl")

@application.route('/tweets', methods=['POST'])
def predict_class():
    try:
        if request.method == 'POST':
            # Get the Twitter handle from the JSON request
            twitter_handle = request.json['twitter_handle']

            # Scrape tweets
            scraped_tweets = scrape_tweets(twitter_handle)

            # Extract tweet texts
            tweet_texts = scraped_tweets['tweets']

            # Preprocess tweet texts
            preprocessed_texts = [preprocess(text) for text in tweet_texts]

            # Use preprocessed tweet texts as input for the model
            predictions = pipeline.predict(preprocessed_texts)

            # Calculate the majority prediction
            majority_prediction = get_majority_prediction(predictions)

            # Convert prediction to JSON
            prediction_json = {'prediction': majority_prediction}

            return jsonify(prediction_json), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return render_template('home.html')

def get_majority_prediction(predictions):
    # Convert predictions to numerical values (assuming binary)
    numerical_predictions = [int(x) for x in predictions]
    # Calculate the majority prediction
    majority_prediction = statistics.mode(numerical_predictions)
    return majority_prediction

def scrape_tweets(twitter_handle):
    service = Service(executable_path=CM().install())
    driver = webdriver.Chrome(service=service)

    driver.get('https://twitter.com/' + twitter_handle)
    time.sleep(5)

    for i in range(10):
        driver.execute_script("window.scrollBy(0,2000)")
        time.sleep(1)

    tweets = driver.find_elements(By.XPATH, '//div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div/div/div/article/div/div/div[2]/div[2]/div[2]')
    tweet_texts = [tweet.text for tweet in tweets]

    # Preprocess each tweet text
    preprocessed_tweets = [preprocess(text) for text in tweet_texts]

    driver.quit()

    return {'tweets': preprocessed_tweets}

def preprocess(text):
    doc = nlp(text)
    filtered_tokens = []
    for token in doc:
        if token.is_stop or token.is_punct:
            continue
        filtered_tokens.append(token.lemma_)
    return " ".join(filtered_tokens)

if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5000)