from collections import defaultdict

class AveragedData:
	def __init__(self, max_time = 10.0):
		self.data = defaultdict(list)
		self.max_time = max_time

	def add(self, time, key, value=True):
		d = {"value":value}
		d["t"] = time

		self.data[key].append(d)
		self.prune(time)

	def get_avg(self, time, key, back):
		self.prune(time)
		bd = filter(lambda x:x["t"] > time - back, self.data[key])
		if not bd:
			return 0
		return sum([d["value"] for d in bd]) / float(len(bd))

	def get_sum(self, time, key, back):
		self.prune(time)
		bd = filter(lambda x:x["t"] > time - back, self.data[key])
		if not bd:
			return 0
		return sum([d["value"] for d in bd])	

	def prune(self, time):
		for k,v in self.data.items():
			self.data[k] = filter(lambda x:x["t"] > time - self.max_time, v)

	def get_ct(self, time, key, back):
		self.prune(time)
		bd = filter(lambda x:x["t"] > time - back, self.data[key])
		return len(bd)