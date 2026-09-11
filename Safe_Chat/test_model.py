import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import warnings

warnings.filterwarnings("ignore")

model = pickle.load(open("LinearSVC.pkl", 'rb'))
my_file = open("stopwords.txt", "r")
content_list = my_file.read().split("\n")
my_file.close()

tfidf = TfidfVectorizer(stop_words=content_list, lowercase=True, vocabulary=pickle.load(open("tfidf_vector_vocabulary.pkl", "rb")))

tests = ["साला", "saala", "sala", "s@le", "saale", "bitch", "s@la"]

def normalize(text):
    replacements = {'@': 'a', '$': 's', '1': 'i', '0': 'o', '!': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b'}
    for symbol, letter in replacements.items():
        text = text.replace(symbol, letter)
    return text

for t in tests:
    orig = t
    t = normalize(t)
    t = transliterate(t, sanscript.DEVANAGARI, sanscript.ITRANS).lower()
    data = tfidf.fit_transform([t])
    pred = model.predict(data)[0]
    print(f"'{orig}' -> '{t}' => {'BULLYING' if pred == 1 else 'Non-bullying'}")
