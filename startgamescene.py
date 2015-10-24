from scene import Scene
from vector2 import Vector2
from player import Player
from sprite import Sprite

import pygame
import content
import g

class StartGameScene(Scene):
	def __init__(self):
		Scene.__init__(self)


	def create(self):
		bg = Sprite(Vector2(0, 0))
		bg.addStaticImage(content.images["background.png"])
		self.add(bg)
		
		self.font = pygame.font.Font("visitor1.ttf", 20)
		self.playersInGame = 0

	def draw(self, screen):
		Scene.draw(self, screen)

		surf = self.font.render(str(self.playersInGame) + " players waiting.", False, (39, 65, 62))
		w, h = surf.get_size()
		w += 10
		pygame.draw.rect(screen, (39, 65, 62), (160 - w / 2 - 1, 100 - h / 2 - 1, w + 2, h + 2), 1)
		pygame.draw.rect(screen, (255, 255, 255), (160 - w / 2, 100 - h / 2, w, h), 0)
		w -= 10
		screen.blit(surf, (160 - w / 2, 100 - h / 2))
		
		if g.game.admin:
			surf = self.font.render("Press space to begin.", False, (39, 65, 62))
			w, h = surf.get_size()
			screen.blit(surf, (160 - w / 2, 8))