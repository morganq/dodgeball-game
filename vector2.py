# 2D Vector class ------------------
# mquirk note: I got this from http://www.kokkugia.com/wiki/index.php5?title=Python_vector_class
# random google search. It appears to be a port from java anyways? I guess it's okay?

from math import *

class Vector2:
	def __init__(self, x, y):
		self.x = float(x)
		self.y = float(y)

	def __repr__(self):
		return '<%s, %s>' % (self.x, self.y)
		
	def asTuple(self):
		return (self.x, self.y)

	def zero(self):
		self.x = 0.0
		self.y = 0.0
		return self

	def clone(self):
		return Vector2(self.x, self.y)

	def normalize(self):
		if self.x == 0 and self.y == 0:
			return self
		norm = float (1.0 / sqrt(self.x*self.x + self.y*self.y))
		self.x *= norm
		self.y *= norm
		return self

	def invert(self):
		self.x = -(self.x)
		self.y = -(self.y)
		return self

	def __sub__(self, t):
		return Vector2(self.x - t.x, self.y - t.y)
	
	def __add__(self, t):
		return Vector2(self.x + t.x, self.y + t.y)
		
	def __mul__(self, s):
		return Vector2(self.x * s, self.y * s)
		
	def __div__(self, s):
		return Vector2(self.x / s, self.y / s)

	def asIntTuple(self):
		return (int(self.x), int(self.y))

	def lengthSquared(self):
		return float((self.x*self.x) + (self.y*self.y))

	def length(self):
		return float(sqrt(self.x*self.x + self.y*self.y))

	def dot(self, v2):
		return (self.x * v2.x + self.y * v2.y)

	def angleBetween(self, v2):
		vDot = self.dot(v2) / (self.length() * v2.length())
		if vDot < -1.0 : vDot = -1.0
		if vDot > 1.0 : vDot = 1.0
		return float(acos(vDot))
		
	def angle(self):
		return atan2(self.y, self.x)

	def limit(self, size):
		if (self.length() > size):
			self.normalize()
			self.scale(size)

	def scale(self, s):
		self.x *= s
		self.y *= s
		return self
