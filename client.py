from game import Game
from netclient import NetClient
from netshared import *
import g
import time
import pygame
import sys

unShiftKeys = list("qwertyuiopasdfghjklzxcvbnm1234567890-=`[];',./")
shiftKeys = {
	',':'<', '.':'>', '/':'?', '[':'{', ']':'}', ';':':', '\'':'"', '\\':'|', '-':'_', '=':'+',
	'1':'!', '2':'@', '3':'#', '4':'$', '5':'%', '6':'^', '7':'&', '8':'*', '9':'(', '0':')','`':'~',
}

class Client(Game):
	def __init__(self, addr, port = DEFAULT_CLIENT_LISTEN_PORT, name = "player", ex = "", super = ""):
		Game.__init__(self, 0)
		self.net = NetClient(int(port))
		self.net.connect(addr)
		time.sleep(1)
		self.net.sendPlayerInfo(name, ex, super)
		self.controller = None
		g.SERVER = False

		self.typingMode = False
		self.typingModeText = ""
		self.typingModeFont = pygame.font.Font("visitor1.ttf", 10)
		self.pauseInput = False

	def handleEvent(self, evt):
		if evt.type == pygame.KEYDOWN:
			if self.typingMode:

				allkeys = pygame.key.get_pressed()
				if allkeys[pygame.K_LSHIFT] or allkeys[pygame.K_RSHIFT]:
					if pygame.key.name(evt.key) in shiftKeys:
						self.typingModeText += shiftKeys[pygame.key.name(evt.key)]
					elif pygame.key.name(evt.key) in unShiftKeys:
						self.typingModeText += pygame.key.name(evt.key)
				else:
					if pygame.key.name(evt.key) in unShiftKeys:
						self.typingModeText += pygame.key.name(evt.key)

				if evt.key == pygame.K_SPACE:
					self.typingModeText += " "

				if evt.key == pygame.K_BACKSPACE:
					self.typingModeText = self.typingModeText[:-1]

				if evt.key == pygame.K_RETURN:
					self.typingMode = False
					self.net.sendToServer({"type":"chat", "text":self.typingModeText})
					self.typingModeText = ""
			else:
				if evt.key == pygame.K_SPACE and not self.started:
					self.net.sendToServer({"type":"start"})

				if evt.key == pygame.K_RETURN and self.started:
					self.typingMode = True
					self.net.sendDirectionInput(0,0)


		if self.controller and not self.typingMode and not self.pauseInput:
			self.controller.getEvent(evt)

	def preUpdate(self, dt):
		if self.controller and not self.typingMode and not self.pauseInput:
			self.controller.update(dt)


	def postDraw(self):
		Game.postDraw(self)
		if self.typingMode:
			surf = self.typingModeFont.render(">"+self.typingModeText, False, (39, 65, 62))
			self.screen.blit(surf, (1,1))

def run(*args):
	game = Client(*args)
	g.game = game
	game.run()

if __name__ == "__main__":
	g.SERVER = False
	if "python" in sys.argv[0]:
		args = sys.argv[2:]
	else:
		args = sys.argv[1:]
	if len(args) == 0:
		args = ["209.6.45.245"]
	run(*args)
