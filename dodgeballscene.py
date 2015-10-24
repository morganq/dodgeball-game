from scene import Scene
from vector2 import Vector2
from player import Player
from sprite import Sprite
import g

import content
import pygame
from particles import ParticleContainer

def layeringSort(a, b):
	if a.layerIndex == b.layerIndex:
		return int(a.position.y - b.position.y)
	else:
		return int(a.layerIndex - b.layerIndex)

class DodgeballScene(Scene):
	def __init__(self):
		Scene.__init__(self)

		self.font = pygame.font.Font("visitor1.ttf", 20)

	def create(self):
		self.bg = Sprite(Vector2(0, 0))
		self.bg.addStaticImage(content.images["background.png"])
		self.particles = ParticleContainer(100)
		self.particles.layerIndex = 0
		self.add(self.particles)
		self.victoryMessage = ""

	def draw(self, screen):
		self.bg.draw(screen)
		map(lambda x:x.drawShadow(screen), self.sceneEntities)
		
		sortedEntities = sorted(self.sceneEntities, cmp = layeringSort)
		map(lambda x:x.draw(screen), sortedEntities)
	
		surf = self.font.render(str(g.game.score[0]) + " - " + str(g.game.score[1]), False, (255, 255, 255))
		w, h = surf.get_size()
		screen.blit(surf, (160 - w / 2, 9))

		if self.victoryMessage != "":
			surf = self.font.render(self.victoryMessage, False, (39, 65, 62))
			w, h = surf.get_size()
			w += 10
			pygame.draw.rect(screen, (39, 65, 62), (160 - w / 2 - 1, 100 - h / 2 - 1, w + 2, h + 2), 1)
			pygame.draw.rect(screen, (255, 255, 255), (160 - w / 2, 100 - h / 2, w, h), 0)
			w -= 10
			screen.blit(surf, (160 - w / 2, 100 - h / 2))