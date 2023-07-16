from bs4 import BeautifulSoup

# to extract plaintext from formatted text with html tags
def extract_plaintext(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    plaintext = soup.get_text()
    return plaintext

# to save books in db for specified author if not already recommended
def save_books(db, recommended_books, author_id):
	existing_books = [book['title'] for book in db.books.find({'author_id': author_id}, {'title': 1})]
	new_books = [book for book in recommended_books if book['title'] not in existing_books]

	if new_books:
		for book in new_books:
			book['author_id'] = author_id
		db.books.insert_many(new_books, ordered=False)