from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class Plotter:
	def __init__(self, db, start_date, end_date):
		self.db = db
		self.start_date = start_date
		self.end_date = end_date
		
	def fetch_data(self):
		pipeline = [
			{"$match": {
				"diary_created": {"$gte": self.start_date, "$lte": self.end_date}
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
			print(entry)