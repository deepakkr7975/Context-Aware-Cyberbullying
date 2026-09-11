from flask import Flask
from flask.wrappers import Request
from requests.models import Response
from flask import request
from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer
import pickle
import re
from deep_translator import MyMemoryTranslator

app = Flask(__name__)

def process_msg(msg):
    if msg == "hi":
        response = "Hello, Welcome to the cyberbullying detection bot!"
    else:
        # Normalize text to catch evasions
        replacements = {'@': 'a', '$': 's', '1': 'i', '0': 'o', '!': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b'}
        for symbol, letter in replacements.items():
            msg = msg.replace(symbol, letter)
            
        # Translate Devanagari to English to map correctly to ML model vocabulary
        if re.search(r'[\u0900-\u097F]', msg):
            try:
                msg = MyMemoryTranslator(source='hi-IN', target='en-GB').translate(msg)
            except:
                pass
        msg = msg.lower()
        msg = [msg]
        
        # List of stopwords 
        my_file = open("stopwords.txt", "r")
        content = my_file.read()
        content_list = content.split("\n")
        my_file.close()

        tfidf_vector = TfidfVectorizer(stop_words = content_list, lowercase = True,vocabulary=pickle.load(open("tfidf_vector_vocabulary.pkl", "rb")))
        data=tfidf_vector.fit_transform(msg)
        print(data)
        model = pickle.load(open("LinearSVC.pkl", 'rb'))
        pred = model.predict(data)
        response = str(pred[0])
        print(response)
        if(response=='1'):
            response = "Output from my ML Model :- bullying"
        else:
            response = "Output from my ML Model :- non-bullying"
            

    return response 

# Testing for postman

@app.route("/testing", methods = ["POST"])
def testing():
    f=request.form 
    print(f['Body'])
    msg=f['Body']
    sender=f['From']
    print(msg)
    response = process_msg(msg)
    return response,200