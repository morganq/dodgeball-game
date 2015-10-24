#Base class for basically everything in the game.

class Entity:
	def __init__(self):
		self.netinfo = {}
		self.name = "entity"

	def update(self, dt):
		pass

	def draw(self, screen):
		pass