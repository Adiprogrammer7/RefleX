from datetime import datetime

class Plotter:
	def __init__(self, db, author_id, start_date, end_date):
		self.db = db
		self.author_id = author_id
		self.start_date = start_date
		self.end_date = end_date
		self.counts = []
		self.emotions = []
		self.piechart_path = "static/images/piechart.png"
		

	def fetch_data(self):
		start_datetime = datetime.combine(self.start_date, datetime.min.time())
		end_datetime = datetime.combine(self.end_date, datetime.max.time())
		pipeline = [
			{"$match": {
				"author_id": self.author_id,
				"diary_created": {"$gte": start_datetime, "$lte": end_datetime}
			}},
			{"$group": {
				"_id": "$emotion",
				"count": {"$sum": 1}
			}},
			{"$project": {
				"emotion": "$_id",
				"count": 1,
				"_id": 0
			}}
		]
		result = self.db.diary.aggregate(pipeline)
		for entry in result:
			self.counts.append(entry['count'])
			self.emotions.append(entry['emotion'])

		# execute plots that will be saved as img
		self.piechart()
