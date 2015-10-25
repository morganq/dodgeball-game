#Base class for basically everything in the game.

class Entity:
	def __init__(self):
		self.netinfo = {}
		self.name = "entity"
		self.oldStates = []

	def update(self, dt):
		st = self.recordState()
		self.oldStates.append(st)
		self.oldStates = [s for s in self.oldStates if s["t"] < 1.0]
		for s in self.oldStates:
			s["t"] += dt

	def recordState(self):
		st = {
			"z":self.z,
			"zVelocity":self.zVelocity,
			"position":self.position,
			"t" : 0.0
		}
		return st

	def getOldState(self, t):
		prev = None
		for i in range(len(self.oldStates)):
			next = self.oldStates[i]
			if next["t"] < t:
				prev = self.oldStates[i-1]
				break

		if not prev:
			return next

		tt = prev["t"] - next["t"]
		mt = prev["t"] - t
		if tt == 0:
			return next
		mh = mt / tt
		ml = 1-mh
		newState = self.prepareMidState(prev, next, mh)
		return newState

	def prepareMidState(self, prev, next, mh):
		ml = 1 - mh
		return {"t":next["t"] * mh + prev["t"] * ml}

	def draw(self, screen):
		pass