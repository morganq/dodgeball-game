#Particle system

from entity import Entity
from vector2 import Vector2
import pygame

def onefilter(l, f):
	for el in l:
		if f(el):
			return el
	return None

class Particle(Entity):
	def __init__(self):
		self.image = None
		self.position = Vector2(0,0)
		self.velocity = Vector2(0,0)
		self.life = 0
		self.dead = True
		self.flipped = False

	def update(self, dt):
		self.position += self.velocity * dt
		self.life -= dt
		if self.life < 0:
			self.dead = True

	def draw(self, screen):
		if not self.dead:
			pimage = pygame.surface.Surface(self.image.get_size(), pygame.SRCALPHA)
			pimage.blit(self.image, (0,0))
			if self.flipped:
				pimage = pygame.transform.flip(pimage, True, False)
			screen.blit(pimage, (self.position + Vector2(-self.image.get_width()/2, -self.image.get_height()/2)).asTuple())

class ParticleContainer(Entity):
	def __init__(self, maxParticles):
		Entity.__init__(self)
		self.position = Vector2(0,0)
		self.particles = [Particle() for i in range(maxParticles)]
		self.netinfo["ignore"] = True

	def spawn(self, image, position, velocity, life):
		p = onefilter(self.particles, lambda x:x.dead)
		if p:
			p.image = image
			p.position = position
			p.velocity = velocity
			p.life = life
			p.dead = False
		return p

	def update(self, dt):
		[p.update(dt) for p in self.particles]

	def draw(self, screen):
		[p.draw(screen) for p in self.particles]
		
	def drawShadow(self, screen):
		return None
		
