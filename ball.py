from sprite import Sprite
import content
from vector2 import Vector2
import g

class Ball(Sprite):
	def __init__(self, position):
		Sprite.__init__(self, position)

		self.addAnimation("still", content.images["ball.png"], 0, 0, 15, 15, 1, 1, True)
		self.addAnimation("moving", content.images["ball.png"], 15, 0, 15, 15, 1, 1, True)

		self.name = "ball"

		self.offset = Vector2(7, 13)
		self.held = False
		self.throwTeam = 0
		self.thrower = None
		self.timeSinceThrow = 0
		self.super = []
		self.superIndex = 0
		self.lastSuperNode = None
		self.damage = 15
		self.mode = 0
		
		self.pTimer = 0

	def throw(self):
		self.held = False
		self.timeSinceThrow = -0.375

	def update(self, dt):
		Sprite.update(self, dt)

		if self.velocity.x > 0:
			self.angle -= self.velocity.length() / 30
		else:
			self.angle += self.velocity.length() / 30

		if self.velocity.length() > 55:
			self.play("moving")
			if self.pTimer <= 0:
				if self.mode == 0:
					img = content.images['balltrail.png']
					life = 0.2
				elif self.mode == 1:
					img = content.images['exballtrail.png']
					life = 0.3
				else:
					img = content.images['superballtrail.png']
					life = 0.5
				if self.mode == 4:
					img = content.images['balltrail_extra.png']
					life = 0.3
				g.game.scene.particles.spawn(img, Vector2(self.position.x+1, self.position.y-6-self.z), Vector2(0,0), life)
				self.pTimer = 0.05
			else:
				self.pTimer -= dt
		else:
			self.play("still")

		#if self.velocity.length() < 10:
		#	self.velocity = Vector2(0, 0)
		if self.z <= 2 and abs(self.zVelocity) < 2:
			self.z = 0
			self.zVelocity = 0

		if self.held:
			self.shadowVisible = False
			self.layerIndex = 1
		else:
			superIndex = int(self.timeSinceThrow * 8.0)
			self.layerIndex = 0
			self.shadowVisible = True
			self.velocity *= 0.99
			if self.z > 0:
				if superIndex < len(self.super):
					if self.zVelocity > 0:
						self.zVelocity -= 80 * dt
				else:
					self.zVelocity -= 80 * dt
			if self.z < 0:
				self.zVelocity = abs(self.zVelocity) * 0.7
				self.z = 0
				self.velocity *= 0.7
				if self.zVelocity > 15:
					g.game.playSound("bounce.wav")

			self.superIndex = superIndex
			self.timeSinceThrow += dt
			if superIndex < len(self.super) and superIndex >= 0:
				node = self.super[superIndex]
				if node != self.lastSuperNode:
					if self.lastSuperNode is not None:
						self.lastSuperNode.end(self)
					node.begin(self)
					if node.sound is not None:
						g.game.playSound(node.sound)
				node.update(self, dt)
				self.lastSuperNode = node
			else:
				if self.lastSuperNode is not None:
					self.lastSuperNode.end(self)
					self.lastSuperNode = None
			self.bounceOffWalls()

	def bounceOffWalls(self):
		if self.position.y < 38:
			self.velocity.y = abs(self.velocity.y) * 0.8 + 5
			g.game.playSound("bounce.wav")

		if self.position.y > 187:
			self.velocity.y = -abs(self.velocity.y) * 0.8 - 5
			g.game.playSound("bounce.wav")

		if self.position.x < 35 - 0.2391 * (self.position.y - 38):
			self.velocity.x = abs(self.velocity.x) * 0.7 + 30
			g.game.playSound("bounce.wav")

		if self.position.x > 285 + 0.2391 * (self.position.y - 38):
			self.velocity.x = -abs(self.velocity.x) * 0.7 - 30
			g.game.playSound("bounce.wav")