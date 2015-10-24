import pygame
import sys
import os

images = {}
sounds = {}

def loadImages(top, path):
	for (path, dirs, files) in os.walk(path, True):
		if ".svn" in path:
			continue
		if "\\" in path:
			pathDirs = path.split("\\")
		else:
			pathDirs = path.split("/")
		parent = images
		for p in pathDirs[1:]:
			if p not in parent:
				parent[p] = {}
			parent = parent[p]
		for d in dirs:
			if d[0] != ".":
				parent[d] = {}
		parent["imagelist"] = []
		files.sort()
		for f in files:
			if f[0] != ".":
				try:
					img = pygame.image.load(path + "/" + f).convert_alpha()
					parent[f] = img
					parent["imagelist"].append(img)
				except:
					print("Failed to load " + path + "/" + f)

def loadSounds(top, path):
	pygame.mixer.init()
	for f in os.listdir(path):
		if f[0] != ".":
			sounds[f] = pygame.mixer.Sound(path+"/"+f)
			sounds[f].set_volume(0.25)

def load():
	loadImages(images, "images")
	loadSounds(sounds, "sounds")