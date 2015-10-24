from entity import Entity

#Scene is an entity which merely holds other entities (mainly sprites)

class Scene(Entity):
	def __init__(self):
		self.sceneEntities = []

	def create(self):
		pass

	def update(self, dt):
		map(lambda x:x.update(dt), self.sceneEntities)

	def draw(self, screen):
		map(lambda x:x.draw(screen), self.sceneEntities)
		
	def add(self, ent):
		self.sceneEntities.append(ent)