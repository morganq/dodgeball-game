from sprite import Sprite
from vector2 import Vector2
import pygame
import content
import random
import g

MID = 160

class Player(Sprite):
	def __init__(self, position, team = 0):
		Sprite.__init__(self, position)
		self.addAnimation("stand", content.images['player3.png'],	32 * 0 , 0, 32, 32, 1, 0, True)
		self.addAnimation("runf", content.images['player3.png'],	32 * 1 , 0, 32, 32, 6, 9, True)
		self.addAnimation("runfh", content.images['player3.png'],	32 * 7 , 0, 32, 32, 6, 9, True)
		self.addAnimation("runb", content.images['player3.png'],	32 * 13, 0, 32, 32, 6, 9, True)
		self.addAnimation("runbh", content.images['player3.png'],	32 * 19, 0, 32, 32, 6, 9, True)
		self.addAnimation("catch", content.images['player3.png'],	32 * 25, 0, 32, 32, 1, 0, True)
		self.addAnimation("throw", content.images['player3.png'],	32 * 26, 0, 32, 32, 4, 7, True)
		self.addAnimation("hit", content.images['player3.png'],		32 * 30, 0, 32, 32, 2, 4, True)
		self.addAnimation("jumpf", content.images['player3.png'],	32 * 32, 0, 32, 32, 1, 0, True)
		self.addAnimation("jumpfh", content.images['player3.png'],	32 * 33, 0, 32, 32, 1, 0, True)
		self.addAnimation("jump", content.images['player3.png'],	32 * 34, 0, 32, 32, 1, 0, True)
		self.addAnimation("jumph", content.images['player3.png'],	32 * 35, 0, 32, 32, 1, 0, True)

		self.team = team

		self.name = "player"
		self.shadowSize = 19
		self.shadowOffset = Vector2(0, 1)

		self.super = []
		self.exThrow = []
		self.superTicks = 0

		#net
		self.chatMessage = ""
		self.chatTimer = 0
		self.chatFont = pygame.font.Font("visitor1.ttf", 10)

		self.lastAnimation = self.currentAnimation
		
		#dash
		self.dashTimer = 0
		self.dashDirection = (0,0)
		
		#knockback
		self.knockbackVelocity = Vector2(0, 0)
		
		#over the line logic
		self.runningHome = False
		
		#midair throw bonus
		self.midairBonus = False
		
		#particle timer
		self.pTimer = 0

	def initialize(self):
		self.health = 100
		
		self.xDirection = 0
		self.yDirection = 0

		self.play("stand")
		self.offset = Vector2(16, 30)

		self.holding = None
		self.angle = 0
		
		self.catchingTimer = 0.0
		self.stunTimer = 0.0
		self.clientStunTimer = 0.0
		self.throwTimer = 0.0
		self.hitTimer = 0.0
		self.dashVelocity = Vector2(0,0)
		
		self.correctPosition = Vector2(0,0)

	def holdingForward(self):
		return self.xDirection == (1, -1)[self.team]

	def holdingBack(self):
		return self.xDirection == (-1, 1)[self.team]

	def tryDash(self, direction):
		if self.stunTimer > 0 or direction == (0,0) or self.z > 0:
			return

		if self.dashDirection == direction and self.dashTimer > 0:
			self.dashVelocity = Vector2(direction[0] * 500, direction[1] * 500)
			self.stunTimer = 0.5
			g.game.playSound("dodge.wav")
			self.netinfo["teleporting"] = True
		else:
			self.dashDirection = direction
			self.dashTimer = 0.2

	def update(self, dt):
		Sprite.update(self, dt)

		self.dashTimer -= dt

		if self.health <= 0:
			if self.angle == 0:
				g.game.playSound("death.wav")
			self.angle = (self.team * 2 - 1) * -90
			self.offset = Vector2(16, 24)
			self.stunTimer = 1.0

		if self.holding:
			self.serverplay("catch")
		else:
			self.serverplay("stand")

		if self.hitTimer > 0:
			self.hitTimer -= dt

		if self.chatTimer > 0:
			self.chatTimer -= dt
			
		if self.catchingTimer > 0:
			self.catchingTimer -= dt

		speed = 1.0
		if abs(self.xDirection) + abs(self.yDirection) > 1:
			speed = 0.7

		xd = self.xDirection
		yd = self.yDirection
		


		
		if self.z <= 0:
			if self.team == 0 and self.position.x < MID-10:
				self.runningHome = False
			elif self.team == 1 and self.position.x > MID+10:
				self.runningHome = False

			if self.team == 0 and self.position.x > MID:
				self.runningHome = True
			elif self.team == 1 and self.position.x < MID:
				self.runningHome = True

			if self.team == 0 and self.runningHome:
				xd = -1
			elif self.team == 1 and self.runningHome:
				xd = 1
		else:
			self.runningHome = False

		if self.clientStunTimer > 0:
			self.clientStunTimer -= dt

		if self.stunTimer > 0:
			self.stunTimer -= dt
			xd = 0
			yd = 0
			if self.catchingTimer > 0:
				self.serverplay("catch")
			else:
				self.serverplay("hit")
			
		animname = None
		if self.z == 0:
			if xd == -1:
				self.velocity.x = -80 * speed
				if self.team == 0:
					animname = "runb"
				else:
					animname = "runf"
			elif xd == 1:
				self.velocity.x = 80 * speed
				if self.team == 0:
					animname = "runf"
				else:
					animname = "runb"
			elif xd == 0:
				self.velocity.x = 0
	
			if yd == -1:
				self.velocity.y = -60 * speed
				animname = "runf"
			elif yd == 1:
				self.velocity.y = 60 * speed
				animname = "runf"
			elif yd == 0:
				self.velocity.y = 0

			self.midairBonus = False
		else:
			if xd == -1:
				self.velocity.x = max(self.velocity.x - 100 * dt, -80 * speed)
			elif xd == 1:
				self.velocity.x = min(self.velocity.x + 100 * dt, 80 * speed)

			if yd == -1:
				self.velocity.y = max(self.velocity.y - 80 * dt, -60 * speed)
			elif yd == 1:
				self.velocity.y = min(self.velocity.y + 80 * dt, 60 * speed)
				
			if (self.team == 0 and self.velocity.x > 50) or (self.team == 1 and self.velocity.x < -50):
				animname = "jumpf"
			else:
				animname = "jump"

		if animname:
			if self.holding:
				animname += "h"
			self.serverplay(animname)

		self.pTimer -= dt

		self.pushVelocity = None
		if not self.knockbackVelocity.isZero():
			self.pushVelocity = self.knockbackVelocity
		elif not self.dashVelocity.isZero():
			self.pushVelocity = self.dashVelocity

		if self.pushVelocity:
			if self.pTimer <= 0:
				p = g.game.scene.particles.spawn(content.images['dashtrail.png'], Vector2(self.position.x, self.position.y-14-self.z), Vector2(0,0), 0.25)
				p.flipped = self.flipHorizontal
				self.pTimer = 0.05
			self.stunTimer = 0.1
			self.velocity = self.pushVelocity
			self.knockbackVelocity *= 0.8
			self.dashVelocity *= 0.8
			if self.pushVelocity.lengthSquared() < 10:
				self.knockbackVelocity.zero()
				self.dashVelocity.zero()

		if self.throwTimer > 0:
			self.throwTimer -= dt
			self.serverplay("throw")

		if self.team == 0:
			self.flipHorizontal = False
		else:
			self.flipHorizontal = True

		if self.holding is not None:
			xo = (8, -8)[self.flipHorizontal]
			self.holding.position = self.position + Vector2(xo, 1)
			self.holding.z = 6 + self.z

		if g.SERVER:
			self.serverCheckBallCollision()


		if self.z > 0:
			self.zVelocity -= 200 * dt
		else:
			if self.zVelocity < -20:
				self.stunTimer = 0.5
				if not g.SERVER:
					self.clientStunTimer = 0.5
			self.z = 0
			self.zVelocity = 0


		self.collideWalls()

		if g.SERVER:
			if self.currentAnimation != self.lastAnimation:
				g.game.net.broadcast({"type":"animation", "netid":self.netinfo["netid"], "name":self.currentAnimation.name})
		self.lastAnimation = self.currentAnimation

	def serverplay(self, name):
		if g.SERVER:
			self.play(name)

	def tryThrow(self, super = False):

		if self.stunTimer > 0:
			return
			
		if self.runningHome:
			return

		#Catch
		if self.holding is None:
			self.catchingTimer = 0.25
			self.stunTimer = 0.65
		#Throw
		else:
			forward = False
			#So we don't accidentally insta-catch our own ball.
			self.catchingTimer = 0.0
			#In the air
			if self.z > 0 and (self.holdingForward() or (self.xDirection == 0 and self.yDirection ==0)):
				self.holding.zVelocity = -60
			else:
				self.holding.zVelocity = 30

			speed = 130
			#Velocity based on forwards
			v = Vector2(self.xDirection, self.yDirection * 0.8)
			if v.lengthSquared() == 0:
				v.x = (1, -1)[self.team]
				speed += 70
				forward = True
			if self.holdingForward():
				speed += 50
				v.x += (1, -1)[self.team]
				if self.yDirection == 0:
					self.holding.zVelocity += 15
					speed += 50
				forward = True

			v.normalize()
			v *= speed
			self.holding.velocity = v
			self.holding.z += self.zVelocity * 0.25
			self.holding.mode = 0
			self.holding.throwTeam = self.team
			if super:
				self.holding.velocity = Vector2((speed, -speed)[self.team], 0)
				if self.superTicks >= 6:
					self.holding.super = self.super
					self.superTicks = 0
					self.holding.damage = 25
					g.game.playSound("super.wav")
					self.holding.mode = 2
				else:
					self.holding.super = self.exThrow
					self.holding.velocity *= 0.66
					self.holding.mode = 1
					g.game.playSound("ex.wav")
			else:
				self.holding.super = []
				g.game.playSound("normal.wav")
			if self.midairBonus:
				if self.holding.mode == 0:
					self.holding.mode = 4
				self.holding.damage += 10
			self.holding.throw()
			self.holding.thrower = self
			if forward:
				#self.holding.position.x += (-15, 15)[self.team]
				self.holding.z += 8
			g.game.net.sendThrowMessage(self, self.holding, self.holding.velocity, self.holding.zVelocity, self.holding.mode)
			self.holding = None
			self.throwTimer = 0.35
			self.stunTimer = 0.35

	def tryJump(self):
		if self.stunTimer > 0:
			return
		if self.z > 0:
			return
		if self.runningHome:
			return
		self.zVelocity = 120
		g.game.playSound("jump.wav")

	def serverCheckBallCollision(self):
		if self.health <= 0:
			return
		for ent in g.game.scene.sceneEntities:
			if (ent.position - self.position).lengthSquared() < (15 * 15) and abs(ent.z - (self.z + 7)) < 20 and ent.name == "ball" and not ent.held:
				if self.catchingTimer > 0 and self.holding is None:
					if ent.velocity.length() > 55 and ent.throwTeam != self.team:
						self.superTicks = min(self.superTicks + 2, 6)
						if self.z > 0:
							self.midairBonus = True
					self.holding = ent
					self.holding.z = 10
					self.holding.zVelocity = 0
					self.holding.velocity = Vector2(0,0)
					self.holding.held = True
					self.stunTimer = 0
					g.game.net.sendPickupMessage(self, ent)
					g.game.playSound("catch.wav")
				elif (ent.position - self.position).lengthSquared() < (9 * 9) and (ent.velocity.length() > 55 or ent.zVelocity < -45) and ent.throwTeam != self.team and self.hitTimer <= 0:
					self.health -= ent.damage
					self.knockbackVelocity = ent.velocity.clone()
					self.stunTimer = 0.65
					self.hitTimer = 0.75
					ent.thrower.superTicks = min(ent.thrower.superTicks + 1, 6)
					g.game.playSound("hit.wav")
					if ent.position.x > self.position.x:
						ent.velocity.x = abs(ent.velocity.x) * 0.8
						ent.velocity.y += random.random() * 60 - 30
					else:
						ent.velocity.x = -abs(ent.velocity.x) * 0.8
						ent.velocity.y += random.random() * 60 - 30


	def draw(self, screen):
		Sprite.draw(self, screen)
		x = self.position.x - 7
		y = self.position.y - 34 - self.z
		w = min(max(self.health, 0) / 100.0 * 14, 13)
		if self.health > 0:
			pygame.draw.rect(screen, (39,65,62), (x-1,y-1, 16, 3), 0)
			pygame.draw.line(screen, (255, 255, 255), (x, y), (x + 13, y))
			pygame.draw.line(screen, (67,102,125), (x, y), (x + w, y))
			
			for i in range(self.superTicks):
				c = (67,102,125)
				if self.superTicks == 6:
					pygame.draw.line(screen, (67,102,125), (x-1, y-2), (x+14, y-2))
					c = (39,65,62)
				pygame.draw.line(screen, c, (x - 1 + i * 3, y-3), (x - 1 + i * 3, y-2))

		if self.chatTimer > 0:
			surf = self.chatFont.render(self.chatText, False, (39, 65, 62))
			if self.flipHorizontal:
				x = x - 4 - surf.get_width()
			else:
				x = x + 18
			screen.blit(surf, (x, y + 2))
			
	def collideWalls(self):
		self.position.y = max(38, self.position.y)
		self.position.y = min(187, self.position.y)
		self.position.x = max(35 - 0.2391 * (self.position.y - 38), self.position.x)
		self.position.x = min(285 + 0.2391 * (self.position.y - 38), self.position.x)

	def clientCanAttemptThrow(self):
		if self.stunTimer >= 0.1:
			return False
		if self.z <= 0:
			if self.team == 0 and self.position.x > MID:
				return False
			if self.team == 1 and self.position.x < MID:
				return False
		return True

class PlayerController:
	def __init__(self, player, netClient):
		self.player = player
		self.netClient = netClient
		self.lastkx = 0
		self.lastky = 0

	def update(self, dt):
		keys = pygame.key.get_pressed()
		kx = 0
		ky = 0
		if keys[pygame.K_LEFT]:
			kx = -1
		if keys[pygame.K_RIGHT]:
			kx = 1
		if keys[pygame.K_UP]:
			ky = -1
		if keys[pygame.K_DOWN]:
			ky = 1
		if kx != self.lastkx or ky != self.lastky:
			self.netClient.sendDirectionInput(kx, ky, self.player.position)
			self.player.tryDash((kx, ky))

		if self.player.stunTimer <= 0:
			self.player.xDirection = kx
			self.player.yDirection = ky

		self.lastkx = kx
		self.lastky = ky

	def getEvent(self, evt):
		if evt.type == pygame.KEYDOWN:
			if evt.key == pygame.K_z:
				if self.player.clientCanAttemptThrow():
					self.netClient.sendButtonInput("super", self.player.position)
					self.player.stunTimer = 5.0
			if evt.key == pygame.K_x:
				if self.player.clientCanAttemptThrow():
					self.netClient.sendButtonInput("throw", self.player.position)
					self.player.stunTimer = 5.0
			if evt.key == pygame.K_c:
				self.netClient.sendButtonInput("jump", self.player.position)
				self.player.tryJump()

