import pygame
from entity import Entity
from vector2 import Vector2
import content

#An animation is a list of frames, and the necessary state info
#A frame is a (image, rect) pair
class Animation:
	def __init__(self, frames, framerate, looping):
		self.frames = frames
		self.framerate = framerate
		self.looping = looping
		self.t = 0

	def update(self, dt):
		self.t += dt
		
	def getImage(self):
		#Figure out which frame index we're at based on time and framerate
		frameNum = int(self.framerate * self.t)
		if frameNum >= len(self.frames):
			if self.looping:
				frameNum = frameNum % len(self.frames)
			else:
				frameNum = len(self.frames) - 1
		return self.frames[frameNum]

class Sprite(Entity):
	def __init__(self, position):
		Entity.__init__(self)
		#Physics stuff
		self.position = position
		self.velocity = Vector2(0, 0)
		self.acceleration = Vector2(0, 0)

		#Image stuff
		self.animations = {}
		self.currentAnimation = None
		self.flipHorizontal = False
		self.offset = Vector2(0, 0)
		self.visible = True

		#z
		self.z = 0
		self.zVelocity = 0

		#self.shadow = content.images["shadow.png"]
		self.shadowSize = 14
		self.shadowOffset = Vector2(0, 0)
		self.shadowVisible = True
		
		#layering
		self.layerIndex = 0
		
		#rotation
		self.angle = 0

	def addAnimation(self, name, image, startX, startY, frameWidth, frameHeight, numFrames, framerate, looping = True):
		frames = []
		for i in range(numFrames):
			rect = pygame.Rect(startX + i * frameWidth, startY, frameWidth, frameHeight)
			frame = (image, rect)
			frames.append(frame)
		anim = Animation(frames, framerate, looping)
		self.animations[name] = anim
		self.currentAnimation = anim
		self.currentAnimation.name = name
		
	def play(self, name):
		if self.currentAnimation != self.animations[name]:
			self.currentAnimation = self.animations[name]
			self.currentAnimation.t = 0

	def addStaticImage(self, image):
		rect = image.get_rect()
		self.addAnimation("default", image, rect[0], rect[1], rect[2], rect[3], 1, 0, False)

	def update(self, dt):
		self.z += self.zVelocity * dt
		self.velocity += self.acceleration * dt
		self.position += self.velocity * dt
		if self.currentAnimation:
			self.currentAnimation.update(dt)

	def drawShadow(self, screen):
		if self.visible and self.currentAnimation:
			if self.shadowVisible:
				w = max(self.shadowSize - self.z / 5, 2)
				h = w * 0.5
				ss = pygame.surface.Surface( (w,h), pygame.SRCALPHA)
				pygame.draw.ellipse(ss, (0, 0, 0, 128), (0, 0, w, h), 0)
				screen.blit(ss, (self.position.x + self.shadowOffset.x - w / 2, self.position.y + self.shadowOffset.y - h / 2))


	def draw(self, screen):
		if self.visible and self.currentAnimation:
			(src, rect) = self.currentAnimation.getImage()
			image = pygame.Surface((rect[2], rect[3]),pygame.SRCALPHA)
			image.blit(src, (0,0), rect)
			if self.flipHorizontal:
				image = pygame.transform.flip(image, True, False)
			if self.angle != 0:
				image = pygame.transform.rotate(image, int(self.angle/90) * 90)
			screen.blit(image, (self.position - self.offset + Vector2(0, -self.z)).asTuple())
			#pygame.draw.circle(screen, (255,0,0), self.position.asIntTuple(), 1)