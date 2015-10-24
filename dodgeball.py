import pygame
import sys
import pickle
import g
import json
from supernode import allnodes
import subprocess
import time

config_default = {
	"host":"127.0.0.1",
	"port":"2015",
	"name":"player",
	"ex":"",
	"super":"",
}


try:
	f = open("config.json", "r")
	config = json.loads(f.read())
	f.close()
except:
	config = config_default


pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

joined = False

_screen = pygame.display.set_mode((640, 400))
screen = pygame.Surface((320, 200))

bg = pygame.image.load("images/setupscreen.png").convert()

pygame.font.init()
font = pygame.font.Font("visitor1.ttf", 20)

class Field:
	def __init__(self, name, x, y, value, w):
		self.name = name
		self.x = x
		self.y = y
		self.w = w
		self.value = value
		self.selected = False



namef = Field("name", 16, 136, config["name"], 160)
serverf = Field("server", 16, 177, config["host"], 160)
portf = Field("port", 184, 177, config["port"], 68)

fields = [namef, serverf, portf]

def save_config():
	config["name"] = namef.value
	config["host"] = serverf.value
	config["port"] = portf.value
	config["super"] = "".join([n.symbol for n in super])
	config["ex"] = "".join([n.symbol for n in ex])	
	f = open("config.json", "w+")
	f.write(json.dumps(config))
	f.close()

unShiftKeys = list("qwertyuiopasdfghjklzxcvbnm1234567890-=`[];',./")
shiftKeys = {
	',':'<', '.':'>', '/':'?', '[':'{', ']':'}', ';':':', '\'':'"', '\\':'|', '-':'_', '=':'+',
	'1':'!', '2':'@', '3':'#', '4':'$', '5':'%', '6':'^', '7':'&', '8':'*', '9':'(', '0':')','`':'~',
}

nodeTxt = ""

tileimages = {}
tilegrid = []
i = 0
for n in allnodes.values():
	tileimages[n.tile] = pygame.image.load("images/" + n.tile).convert()

	if i % 6 == 0:
		tilegrid.append([])
	tilegrid[i/6].append(n)
	i += 1

sClick = pygame.mixer.Sound("sounds/ui_click.wav")
sClick.set_volume(0.25)
sHover = pygame.mixer.Sound("sounds/ui_hover.wav")
sHover.set_volume(0.15)
sAddtile = pygame.mixer.Sound("sounds/ui_addtile.wav")
sAddtile.set_volume(0.25)

#pygame.mixer.music.load("sounds/setup.ogg")
#pygame.mixer.music.play()
pygame.mixer.music.set_volume(0.2)

superSelected = 0

ex = []
super = []

for symbol in config["ex"]:
	ex.append(allnodes[symbol])

for symbol in config["super"]:
	super.append(allnodes[symbol])	

def test(r, m):
	return m[0] >= r[0] and m[0] < r[2] and m[1] >= r[1] and m[1] < r[3]

def overNode(pos):
	x,y = pos
	x -= 10
	y -= 21
	x /= 12
	y /= 12
	n = None
	if x < 0 or y < 0:
		return None
	try:
		n = tilegrid[y][x]
	except:
		pass
	return n

lastover = False

done = False
while not done:
	for evt in pygame.event.get():
		if evt.type == pygame.QUIT:
			sys.exit()

		if evt.type == pygame.MOUSEBUTTONDOWN:
			mx, my = evt.pos
			mx /= 2
			my /= 2
			for f in fields:
				f.selected = False
				if mx >= f.x and mx < f.x + f.w and my >= f.y and my < f.y + 16:
					f.selected = True
					sClick.play()

			if test((260, 153, 312, 168), (mx, my)):
				sClick.play()
				ss = "".join([n.symbol for n in super])
				exs = "".join([n.symbol for n in ex])

				subprocess.Popen(["python", "server.py"])
				serverf.value = "127.0.0.1"

				time.sleep(2)

				import client
				client.run(serverf.value, int(portf.value), namef.value, exs, ss)

			if test((260, 176, 312, 191), (mx, my)):
				sClick.play()
				ss = "".join([n.symbol for n in super])
				exs = "".join([n.symbol for n in ex])
				import client
				client.run(serverf.value, int(portf.value), namef.value, exs, ss)					

			if test((167, 20, 167+81, 20+32), (mx, my)):
				sClick.play()
				superSelected = 0
			
			if test((134, 61, 134+158, 61+51), (mx, my)):
				sClick.play()
				superSelected = 1
				
			if test((92, 20, 130, 35), (mx, my)):
				sClick.play()
				if superSelected:
					super = super[:-1]
				else:
					ex = ex[:-1]
				save_config()

			if test((92, 39, 130, 54), (mx, my)):
				sClick.play()
				if superSelected:
					super = []
				else:
					ex = []
				save_config()

			n = overNode((mx, my))
			if n is not None:
				if superSelected and len(super) < 24:
					super.append(n)
				if not superSelected and len(ex) < 6:
					ex.append(n)
				sAddtile.play()
				save_config()
				
		if evt.type == pygame.MOUSEMOTION:
			mx, my = evt.pos
			mx /= 2
			my /= 2
			n = overNode((mx, my))
			if n != lastover and n is not None:
				sHover.play()
			if n is not None:
				nodeTxt = "("+n.symbol+") " + n.name + " [" + str(n.cost) + "]"
			lastover = n

		if evt.type == pygame.KEYDOWN:
			selected = None
			for f in fields:
				if f.selected:
					selected = f
			if selected:
				allkeys = pygame.key.get_pressed()
				if allkeys[pygame.K_LSHIFT] or allkeys[pygame.K_RSHIFT]:
					if pygame.key.name(evt.key) in shiftKeys:
						selected.value += shiftKeys[pygame.key.name(evt.key)]
					elif pygame.key.name(evt.key) in unShiftKeys:
						selected.value += pygame.key.name(evt.key)
				else:
					if pygame.key.name(evt.key) in unShiftKeys:
						selected.value += pygame.key.name(evt.key)

				if evt.key == pygame.K_SPACE:
					selected.value += " "

				if evt.key == pygame.K_BACKSPACE:
					selected.value = selected.value[:-1]
			save_config()

	screen.blit(bg, (0,0))

	if superSelected == 0:
		pygame.draw.rect(screen, (0,0,0), (166, 19, 83, 34), 1)
	else:
		pygame.draw.rect(screen, (0,0,0), (133, 60, 160, 53), 1)

	for f in fields:
		if f.selected:
			pygame.draw.rect(screen, (255,255,255), (f.x + 1, f.y, f.w, 13), 0)
		surf = font.render(f.value, False, (0,0,0))
		screen.blit(surf, (f.x + 3, f.y - 3), (0, 0, f.w - 4, 16))
		
	for i in range(len(tilegrid)):
		for j in range(len(tilegrid[i])):
			img = tileimages[tilegrid[i][j].tile]
			y = i * 12 + 21
			x = j * 12 + 10
			screen.blit(img, (x,y))
			
	for i in range(len(ex)):
		img = tileimages[ex[i].tile]
		x = i * 12 + 171
		y = 36
		screen.blit(img, (x,y))

	for i in range(len(super)):
		img = tileimages[super[i].tile]
		if i < 12:
			x = i * 12 + 138
			y = 77
		else:
			x = (i-12) * 12 + 144
			y = 96
		screen.blit(img, (x,y))

	surf = font.render(nodeTxt, False, (166,43,0))
	screen.blit(surf, (10, 2))

	exval = 15 - sum([n.cost for n in ex])
	if exval < 0:
		ex = ex[:-1]
		exval = 15 - sum([n.cost for n in ex])
	surf = font.render(str(exval), False, (166,43,0))
	screen.blit(surf, (214,19))

	superval = 100 - sum([n.cost for n in super])
	if superval < 0:
		super = super[:-1]
		superval = 100 - sum([n.cost for n in super])
	surf = font.render(str(superval), False, (166,43,0))
	screen.blit(surf, (243,60))

	pygame.transform.scale(screen, (640, 400), _screen)
	pygame.display.update()