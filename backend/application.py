import joblib
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as CM
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

application = Flask(__name__)

# Importing logistic regression and standard scaler pickle.
pipeline = joblib.load("./models/pipeline.pkl")

@application.route('/tweets', methods=['GET', 'POST'])
def predict_class():
    try:
        if request.method == 'POST':
            # Get the Twitter handle from the JSON request
            twitter_handle = request.json['twitter_handle']

            # Scrape tweets
            scraped_tweets = scrape_tweets(twitter_handle)

            # Extract tweet texts
            tweet_texts = scraped_tweets['tweets']

            # Use tweet texts as input for the model
            predictions = pipeline.predict(tweet_texts)

            # Calculate the majority prediction
            prediction = int(sum(predictions) > len(predictions) / 2)

            # Convert prediction to JSON
            prediction_json = {'prediction': prediction}

            return jsonify(prediction_json), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return render_template('.static/home.html')

def scrape_tweets(twitter_handle):
    service = Service(executable_path=CM().install())
    driver = webdriver.Chrome(service=service)

    driver.get('https://twitter.com/' + twitter_handle)
    time.sleep(5)

    for i in range(5):
        driver.execute_script("window.scrollBy(0,2000)")
        time.sleep(0.5)

    tweets = driver.find_elements(By.XPATH, '//div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div/div/div/article/div/div/div[2]/div[2]/div[2]')
    tweet_texts = [tweet.text for tweet in tweets]

    driver.quit()

    return {'tweets': tweet_texts}

if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5000)
