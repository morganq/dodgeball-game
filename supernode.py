from math import *
from vector2 import Vector2
import random
from player import Player
from ball import Ball
import g

class SuperNode:
	sound = None
	tile = "s_empty.png"
	def __init__(self, game):
		self.ball = None
		self.game = game

	def begin(self, ball):
		pass

	def update(self, ball, dt):
		pass

	def end(self, ball):
		pass

allnodes = {}
def RegisterNode(c):
	allnodes[c.symbol] = c

@RegisterNode
class EmptyNode(SuperNode):
	cost = 1
	name = "no action"
	symbol = "."
	pass

@RegisterNode
class DamageNode(SuperNode):
	sound = "s_damage.wav"
	name = "increase damage"
	symbol = "+"
	cost = 5
	tile = "s_damage.png"
	def begin(self, ball):
		ball.damage += 2

@RegisterNode
class AccelNode(SuperNode):
	sound = "s_accel.wav"
	name = "accelerate"
	symbol = ">"
	tile = "s_accel.png"
	cost = 5
	def begin(self, ball):
		print "accel"
		mag = ball.velocity.length()
		ball.velocity.normalize()
		ball.velocity *= max(mag+ 50, 150)

@RegisterNode
class StopNode(SuperNode):
	sound = "s_stop.wav"
	name = "stop"
	symbol = "s"
	cost = 2
	tile = "s_stop.png"
	def begin(self, ball):
		ball.velocity.x *= 0.25

@RegisterNode
class UpNode(SuperNode):
	cost = 2
	name = "lateral up"
	symbol = "^"
	sound = "s_updown.wav"
	tile = "s_up.png"
	def begin(self, ball):
		self.old = ball.velocity.y
		ball.velocity.y = self.old - 80

	def end(self, ball):
		ball.velocity.y = self.old

@RegisterNode
class InvisibleNode(SuperNode):
	cost = 5
	name = "invisible"
	symbol = " "
	sound = "s_invis.wav"
	tile = "s_invisible.png"
	def begin(self, ball):
		ball.visible = False
		
	def end(self, ball):
		ball.visible = True

class RepeatNode(SuperNode):
	cost = 3
	def begin(self, ball):
		self.position = ball.position.clone()

	def update(self, ball, dt):
		ball.velocity *= 0.97

	def end(self, ball):
		ball.position = self.position.clone()
		ball.netinfo["teleporting"] = True
	
@RegisterNode
class RandomNode(SuperNode):
	cost = 5
	name = "random direction"
	symbol = "?"
	tile = "s_random.png"
	def begin(self, ball):
		mag = ball.velocity.length()
		ball.velocity.x = random.random() * 2 - 1
		ball.velocity.y = random.random() * 2 - 1
		ball.velocity.normalize()
		ball.velocity *= mag

@RegisterNode
class TeleportNode(SuperNode):
	sound = "s_teleport.wav"
	cost = 10
	name = "teleport"
	symbol = "t"
	tile = "s_teleport.png"
	def begin(self, ball):
		self.old = ball.velocity
		ball.velocity *= 0.5

	def end(self, ball):
		ball.position += ball.velocity.clone().normalize() * 20
		ball.velocity = self.old
		ball.netinfo["teleporting"] = True

@RegisterNode
class DownNode(SuperNode):
	cost = 2
	name = "lateral down"
	symbol = "v"
	sound = "s_updown.wav"
	tile = "s_down.png"
	def begin(self, ball):
		self.old = ball.velocity.y
		ball.velocity.y = self.old + 80

	def end(self, ball):
		ball.velocity.y = self.old

@RegisterNode
class LiftNode(SuperNode):
	sound = "s_lift.wav"
	cost = 5
	name = "lift"
	symbol = "l"
	tile = "s_lift.png"
	def begin(self, ball):
		ball.zVelocity = max(100, ball.zVelocity + 40)

@RegisterNode
class DropNode(SuperNode):
	sound = "s_drop.wav"
	name = "drop"
	symbol = "d"
	cost = 5
	tile = "s_drop.png"
	def begin(self, ball):
		ball.zVelocity = min(-70, ball.zVelocity - 30)

@RegisterNode
class BlackholeNode(SuperNode):
	sound = "s_drop.wav"
	name = "blackhole"
	symbol = "*"
	cost = 10
	tile = "s_blackhole.png"	#fix

	def update(self, ball, dt):
		for e in self.game.scene.sceneEntities:
			if (e.__class__ == Player and e.team != ball.throwTeam) or e.__class__ == Ball:
				off = ball.position - e.position
				strength = min(40 / (off.length() + 1), 3)
				off.normalize()
				e.position += off * 50 * strength * dt


@RegisterNode
class RepelNode(SuperNode):
	sound = "s_drop.wav"
	name = "repel"
	symbol = "o"
	cost = 10
	tile = "s_repel.png"	#fix

	def begin(self, ball):
		for e in self.game.scene.sceneEntities:
			if (e.__class__ == Player and e.team != ball.throwTeam) or e.__class__ == Ball:
				off = ball.position - e.position
				strength = min(40 / (off.length() + 1), 3)
				off.normalize()
				e.position -= off * 10 * strength
				
#@RegisterNode
class SplitNode(SuperNode):
	sound = "s_drop.wav"
	name = "split"
	symbol = ":"
	cost = 0
	tile = "s_repel.png"	#fix

	def end(self, ball):
		if not g.SERVER:
			return
		b = Ball(Vector2(ball.position.x, ball.position.y))
		ball.position.y += 5
		#ball.netinfo["teleporting"] = True
		self.game.scene.add(b)
		t = min(ball.superIndex, len(ball.super))
		b.super = [] #ball.super[t:]
		b.velocity = ball.velocity.clone() + Vector2(0, 0)
		b.thrower = ball.thrower
		b.throwTeam = ball.throwTeam
		ball.velocity += Vector2(0, 0)
		b.zVelocity = 10 #ball.zVelocity
		b.z = ball.z
		b.throw()
		self.game.net.spawn(b, "ball")

@RegisterNode
class FlattenNode(SuperNode):
	sound = "s_drop.wav"
	name = "flatten"
	symbol = "_"
	cost = 0
	tile = "s_repel.png" #fix
	def begin(self, ball):
		ball.zVelocity = 0

@RegisterNode
class TurnCWNode(SuperNode):
	cost = 6
	name = "turn cw"
	symbol = "("
	sound = "s_turn.wav"
	tile = "s_cw.png"
	def begin(self, ball):
		mag = ball.velocity.length()
		angle = ball.velocity.angle()
		x = cos(angle + pi / 4) * mag
		y = sin(angle + pi / 4) * mag
		ball.velocity = Vector2(x,y)
		
@RegisterNode
class TurnCCWNode(SuperNode):
	cost = 6
	name = "turn ccw"
	symbol = ")"
	sound = "s_turn.wav"
	tile = "s_ccw.png"
	def begin(self, ball):
		mag = ball.velocity.length()
		angle = ball.velocity.angle()
		x = cos(angle - pi / 4) * mag
		y = sin(angle - pi / 4) * mag
		ball.velocity = Vector2(x,y)
