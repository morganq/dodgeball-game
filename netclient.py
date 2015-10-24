from netshared import *
from dodgeballscene import *
from player import PlayerController
import content

class NetClient(NetCommon):
	def __init__(self, listenPort = DEFAULT_CLIENT_LISTEN_PORT):
		NetCommon.__init__(self, listenPort)
		self.sendAddr = None
		self.sendPort = None

		self.cid = None
		self.timeSinceUpdate = 0

		self.latency = 0
		self.pingTimestamp = 0
		self.pingTimer = 0
		
		self.myPlayer = None

	def lookupEntity(self, scene, netid):
		for e in scene.sceneEntities:
			if "netid" in e.netinfo and e.netinfo["netid"] == netid:
				return e

	def update(self, game, dt):
		NetCommon.update(self, game, dt)
		self.timeSinceUpdate += dt

		self.pingTimer -= dt
		if self.pingTimer <= 0:
			self.pingTimer = 2.0 - self.pingTimer
			self.sendPing()

		for e in game.scene.sceneEntities:
			if "position1" in e.netinfo:
				p1 = e.netinfo["position1"]
				p2 = e.netinfo["position2"]
				t1 = e.netinfo["time1"]
				t2 = e.netinfo["time2"]
				deltat = max(t2 - t1, 0.01)
				deltap = p2 - p1
				tval = ((self.t - deltat) - t1) / deltat
				correctPos = deltap * tval + p1
				e.position = e.position * 0.5 + correctPos * 0.5

	def connect(self, addr, port = DEFAULT_SERVER_LISTEN_PORT):
		self.sendAddr = addr
		self.sendPort = port
		self.sendToServer( {"type":"hello"} )
		print("Connecting...")

	def sendToServer(self, data):
		self.sendPacket(data, self.sendAddr, self.sendPort)

	def sendPing(self):
		self.pingTimestamp = self.t
		self.sendToServer({"type":"ping"})

	def updateEntity(self, entity, edata, game):
		if entity is None:
			print("Entity is None!")
			return
		if entity == self.myPlayer:
			pos = Vector2(*edata["position"])
			os = entity.getOldState(self.latency)
			if os and (pos - os["position"]).lengthSquared() > 8*8:
				entity.correctPosition = entity.position - pos
			if os and abs(edata["z"] - os["z"]) > 10:
				entity.z = edata["z"]
			if os and (edata["zVelocity"] > 0 and os["zVelocity"] <= 0 or edata["zVelocity"] <= 0 and os["zVelocity"] > 0):
				entity.zVelocity = edata["zVelocity"]
			if edata["teleporting"]:
				entity.position = pos
		else:
			#entity.position = edata["position"]
			if not "position1" in entity.netinfo or edata["teleporting"]:
				entity.netinfo["position1"] = Vector2(*edata["position"])
				entity.netinfo["time1"] = self.t - 0.050
			else:
				entity.netinfo["position1"] = entity.position#entity.netinfo["position2"]
				entity.netinfo["time1"] = entity.netinfo["time2"]
			entity.netinfo["position2"] = Vector2(*edata["position"])
			entity.netinfo["time2"] = self.t
			entity.z = edata["z"]
			entity.zVelocity = edata["zVelocity"]
			entity.velocity = Vector2(*edata["velocity"])

		entity.visible = edata["visible"]



		
	def updatePlayer(self, player, pdata, game):
		#if player == self.myPlayer:
		#	player.xDirection = pdata["xDirection"]
		#	player.yDirection = pdata["yDirection"]
		if player is None:
			print("Player is None!")
			return
		if player is self.myPlayer:
			if player.stunTimer <= 0 and pdata["stun"] >= 0:
				player.stunTimer = pdata["stun"]
		else:
			player.stunTimer = pdata["stun"]
		player.health = pdata["health"]
		player.knockbackVelocity = pdata["knockback"]
		player.superTicks = pdata["superTicks"]

	def sendDirectionInput(self, x, y):
		self.sendToServer({"type":"directionInput", "x" : x, "y" : y})
		
	def sendButtonInput(self, button):
		self.sendToServer({"type":"buttonInput", "button":button})
		
	def sendPlayerInfo(self, name, exString, superString):
		self.sendToServer({"type":"playerInfo", "name":name, "super":superString, "ex":exString})

	def process_start(self, data, game, info):
		game.setScene(DodgeballScene())
		game.started = True
		game.pauseInput = False
		
	def process_numplayers(self, data, game, info):
		game.scene.playersInGame = data["value"]

	def process_spawn(self, data, game, info):
		entName = data["name"]
		ctor = self.netEntities[entName]
		ent = ctor(data["position"], *data["args"])
		ent.netinfo = data["netinfo"]
		game.scene.add(ent)

		if data["name"] == "player":
			ent.initialize()
			if  data["owner"] == self.cid:
				controller = PlayerController(ent, self)
				self.myPlayer = ent
				game.controller = controller

	def process_id(self, data, game, info):
		self.cid = data["cid"]
		if data["admin"]:
			game.admin = True
		print("Connected.")

	def process_state(self, data, game, info):
		self.timeSinceUpdate = 0
		for edata in data["entities"]:
			entity = self.lookupEntity(game.scene, edata["netid"])
			if entity:
				self.updateEntity(entity, edata, game)
			#print edata
		for pdata in data["players"]:
			player = self.lookupEntity(game.scene, pdata["netid"])
			if player:
				self.updatePlayer(player, pdata, game)

	def process_pickup(self, data, game, info):
		player = self.lookupEntity(game.scene, data["player"])
		ball = self.lookupEntity(game.scene, data["ball"])
		player.holding = ball
		ball.held = True

	def process_throw(self, data, game, info):
		player = self.lookupEntity(game.scene, data["player"])
		ball = self.lookupEntity(game.scene, data["ball"])
		player.holding = None
		ball.velocity = data["velocity"]
		ball.zVelocity = data["zVelocity"]
		ball.throwTeam = data["team"]
		ball.mode = data["mode"]
		ball.held = False

	def process_chat(self, data, game, info):
		p = self.lookupEntity(game.scene, data["netid"])
		if p is not None:
			p.chatText = data["text"]
			p.chatTimer = 5
		
	def process_animation(self, data, game, info):
		p = self.lookupEntity(game.scene, data["netid"])
		if p is not None:
			p.play(data["name"])

	def process_endround(self, data, game, info):
		game.score = data["score"]
		if data["winner"] == self.myPlayer.team:
			game.scene.victoryMessage = "Victory!"
			content.sounds["victory.wav"].play()
		else:
			game.scene.victoryMessage = "Defeat."
			content.sounds["defeat.wav"].play()
			
	def process_sound(self, data, game, info):
		content.sounds[data["name"]].play()

	def process_pong(self, data, game, info):
		self.latency = self.t - self.pingTimestamp
		print "latency (ping+pong): " + str(self.latency)