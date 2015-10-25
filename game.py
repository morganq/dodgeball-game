import pygame
from startgamescene import *
import sys
import content

class Game:
	width = 320
	height = 200
	zoom = 2

	def __init__(self, flags):
		pygame.mixer.pre_init(44100, 16, -2, 1024)
		pygame.init()
		pygame.font.init()
		#flags |= pygame.SRCALPHA
		self._screen = pygame.display.set_mode( (self.width * self.zoom, self.height * self.zoom), flags )
		self.screen = pygame.surface.Surface((self.width, self.height), flags)
		self.scene = None
		self.net = None
		self.elapsed = 0
		
		self.started = False
		self.debugFont = pygame.font.Font("visitor1.ttf", 10)
		self.debugMode = False		

		self.admin = False
		self.score = [0, 0]
		
	def setScene(self, scene):
		self.scene = scene
		scene.create()

	def run(self):
		content.load()
		clock = pygame.time.Clock()
		self.setScene(StartGameScene())
		while 1:
			dt = clock.tick(60) / 1000.0
			self.update(dt)

	def handleEvent(self, evt):
		pass

	def preUpdate(self, dt):
		pass
		
	def postDraw(self):
		if self.debugMode:
			surf = self.debugFont.render("%.2f - %.2f" % (self.net.packetSize, self.net.packetsPerSecond), False, (255, 0, 0))
			self.screen.blit(surf, (240, 1))
			i = 0
			for k,v in self.net.packetloss.items():
				pl = self.net.averagedData.get_avg(self.net.t, "packetloss_" + k, 10) * 100.0
				surf = self.debugFont.render("%s: %.2f%%" %(k,pl), False, (255, 0, 0))
				self.screen.blit(surf, (7, 12 * i + 1))
				i += 1

			for (a,b) in self.net.debug_lines:
				pygame.draw.line(self.screen, (255,0,0,255),a.asIntTuple(), b.asIntTuple(), 1)
				pygame.draw.circle(self.screen, (255,255,0,255),b.asIntTuple(), 3)			

	def playSound(self, name):
		pass

	def update(self, dt):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			else:
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						sys.exit()
					if event.key == pygame.K_d:
						self.debugMode = not self.debugMode
				self.handleEvent(event)

		self.net.update(self, dt)

		self.preUpdate(dt)

		self.scene.update(dt)

		self.screen.fill((255,255,255))
		self.scene.draw(self.screen)
		
		self.postDraw()

		pygame.transform.scale(self.screen, (self.width * self.zoom, self.height * self.zoom), self._screen)
		pygame.display.update()
