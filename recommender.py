from nltk import FreqDist
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import spacy
from rake_nltk import Rake
import requests

class BookRecommender:
	def __init__(self, content, max_count=5, alsoPhrases=True, api_url=r"https://www.googleapis.com/books/v1/volumes?q="):
		self.content = content
		self.max_count = max_count
		self.alsoPhrases = alsoPhrases
		self.api_url = api_url
		self.processed_content = None
		self.query = None
		self.keywords = None
		self.phrases = None
		self.entities = None
		self.necessary_fields = ["title", "authors", "description", "printType", "pageCount", "categories", "averageRating", "imageLinks", "canonicalVolumeLink"]
		self.books = []


	def preprocess_content(self):
		# Convert the text to lowercase
		self.content = self.content.lower()  
		
		# Tokenize the text into individual words
		tokens = word_tokenize(self.content)
		
		# Remove punctuation marks
		tokens = [token for token in tokens if token not in string.punctuation]
		
		# Remove stop words
		stop_words = set(stopwords.words('english'))
		tokens = [token for token in tokens if token not in stop_words]
		
		# Lemmatize the words
		lemmatizer = WordNetLemmatizer()
		tokens = [lemmatizer.lemmatize(token) for token in tokens]
		
		# Join the tokens back into a preprocessed text
		self.processed_content = ' '.join(tokens)
		

	def extract_keywords(self, top_n=5):
		# Tokenize the preprocessed content into individual words
		tokens = word_tokenize(self.processed_content)
		
		# Calculate the frequency distribution of the tokens
		freq_dist = FreqDist(tokens)
		
		# Extract the top n most frequent keywords
		self.keywords =  " ".join([token for token, freq in freq_dist.most_common(top_n)])
		return self.keywords


	def extract_phrases(self):
		r = Rake()
		r.extract_keywords_from_text(self.processed_content)

		# # To get keyword phrases ranked highest to lowest with scores.
		# for i in r.get_ranked_phrases():
		# 	print(i)
		self.phrases =  r.get_ranked_phrases()[0] #to get first ranked phrase
		return self.phrases


	def extract_named_entites(self):
		# Load the pre-trained English language model
		nlp = spacy.load('en_core_web_md')
		doc = nlp(self.processed_content)
		# Extract named entities excluding 'DATE' entities
		self.entities = " ".join([ent.text for ent in doc.ents if ent.label_ != 'DATE'])
		return self.entities


	def extract_book_data(self, data):
		if data['totalItems'] != 0:
			# to take only required fields from book api
			for item in data["items"]:
				new_item = {}
				volume_info = item.get("volumeInfo", {})
				average_rating = volume_info.get("averageRating")
				if average_rating is not None:
					for field in self.necessary_fields:
						new_item[field] = volume_info.get(field)
					self.books.append(new_item)

			# Sort the books based on average rating in descending order
			self.books = sorted(self.books, key=lambda x: x.get("averageRating", 0), reverse=True)

			# Select the top self.max_count books
			self.books = self.books[:self.max_count]
		else:
			print("No book results!")


	def fetch_results(self):
		self.preprocess_content()
		result = ""
		result += self.extract_named_entites()
		result += " "
		result += self.extract_keywords()
		result += " "
		if self.alsoPhrases:
			result += self.extract_phrases()
		
		self.query = result.replace(" ", "+")
		r = requests.get(self.api_url + self.query)
		data = r.json()
		self.extract_book_data(data)
		# # just to print json formatted self.books list for debugging
		# formatted_data = json.dumps(self.books, indent=4)
		# print(formatted_data)
