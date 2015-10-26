from game import Game
from netserver import NetServer
import g

class Server(Game):
	def __init__(self):
		Game.__init__(self, 0)
		self.net = NetServer()
		self.debugMode = True

	def playSound(self, name):
		self.net.sendSoundMessage(name)


if __name__ == "__main__":
	g.SERVER = True
	game = Server()
	g.game = game
	game.run()