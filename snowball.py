#!/usr/bin/python

"""Image packing module.

This module exports rectangle packing functionality. The code will try to 
pack a given number of differently sized rectangular objects into as small
a rectangular space as possible, while keeping the dimensions of the 
total rectangle as close to powers of two as possible.

The use case is for the rectangles to represent images, as is typical for
sprite sheets. These can be used in webpages, games and applications where the
number of individual images should be kept low, and sub-images can be used
easily.

Example:
	blocks = [Block(img.size, img) for img in images]
	packer = Packer()
	packer.fit(blocks)
	for block in blocks:
		print block.data, block.x, block.y, block.w, block.h
	
The module includes a sample main program, which will read in a number of image
files, and output the resultant spritesheet, and optionally a C-style header
containing a table of coordinates. It can also generate some other optional
output.
"""

# local helper functions

"""Returns the next higher power of 2 of value.

Internal function, used by grow_pow2()
"""
def _pow2(value):
	if value == 0: return 0
	value -= 1
	p = value.bit_length()
	return 1 << p

class Block:
	"""
	Describes a rectangular area.
	
	The area describes an object (in our case typically an image), and can
	store the associated data.
	
	It is initialised with a position (self.pos) of (0,0).
	This may be modified later when the block's position is finalised.
	"""
	
	def __init__(self, size, data):
		self.size = size
		self.data = data
		self.pos = (0, 0)

	@property
	def x(self):
		return self.pos[0]
	@property
	def y(self):
		return self.pos[1]

	@property
	def w(self):
		return self.size[0]
	@property
	def h(self):
		return self.size[1]

class Box:
	"""Describes a rectangular container.
	
	A box may either contain other boxes, a Block, or be empty.
	A box only has a size. Its position is determined by its relation to its
	siblings and/or parent box.
	
	An empty box may be "split" into two or three boxes, in which case those
	new boxes will be contained by it, or it may be assigned a Block.
	Any box may "grow", either right or down, in which case it acquires an empty
	sibling	in the corresponding direction.
	
	The hierarchy of boxes may be searched for a suitable box that can contain
	a given block. The hierarchy will return the suitable box if any, and None
	if none can be found.
	"""

	def __init__(self, size, first = None, right = None, down = None):
		self.size = size
		self.block = None
		self.first = first
		self.right = right
		self.down  = down
	
	@property
	def w(self):
		return self.size[0]
	@property
	def h(self):
		return self.size[1]

	def find(self, block):
		"""Searches for a suitable box.
		
		The box will be empty, and large enough to contain the given block.
		If none can be found, this function returns None.
		"""
		if self.first:
			return (self.first and self.first.find(block)) or \
				(self.right and self.right.find(block)) or \
				(self.down and self.down.find(block))
		elif not self.block:
			# the box is empty; does the block fit into it?
			if block.w <= self.w and block.h <= self.h:
				return self
		# box is either used, or block does not fit
		return None

	def split(self, block):
		"""Splits the box.
		
		The box is subdivided into at least one box, which is suitable to hold
		the given block. If any space to the right or below the box remains,
		the space is assigned to new boxes.
		"""
		assert(self.block is None)
		assert(not self.first)
		assert(block.w <= self.w and block.h <= self.h)
		self.first = Box(block.size)
		self.first.block = block
		a, b = self.w - block.w, block.h
		if a and b:
			self.right = Box((a, b))
		c, d = self.w, self.h - block.h
		if c and d:
			self.down  = Box((c, d))

	def _postprocess(self, x = 0, y = 0):
		"""Finalise the box's position.
		
		The final position of the box in the layout is recursively determined
		given the relative positions and sizes of its parent and/or siblings.
		"""
		if self.block:
			self.block.pos = (x, y)
		elif self.first:
			self.first._postprocess(x, y)
			w, h = self.first.size
			if self.right:
				self.right._postprocess(x + w, y)
			if self.down:
				self.down._postprocess(x, y + h)
	
class Packer:
	"""Packs a given set of blocks into a layout.
	
	The blocks are packed into a hierarchical set of dynamically allocated
	boxes. After layout is complete, the final positions of the blocks are
	calculated.
	
	The layout of the blocks are done in such a way as to try and maximise
	the area usage of the final containing box, as well as keep the dimensions
	of the containing box as close to powers of two as possible.
	"""
	
	def __init__(self, size = None):
		self.root = None
		if size is not None:
			self.root = Box(size)
	
	def fit(self, blocks):
		"""Fits a number of blocks.
		
		Fits the blocks, then calculates their final positions in the rectangle.
		"""
		if self.root is None:
			self.root = Box(blocks[0].size)
		for block in blocks:
			box = self.root.find(block)
			if not box:
				box = self._grow(block).find(block)
			box.split(block)
		self.root._postprocess()

	def _grow_right(self, block):
		w = block.w + self.root.w
		h = max(self.root.h, block.h)
		self.root = Box((w, h), first = self.root, right = Box((block.w, h)))
		return self.root.right
	
	def _grow_down(self, block):
		w = max(self.root.w, block.w)
		h = block.h + self.root.h
		self.root = Box((w, h), first = self.root, down = Box((w, block.h)))
		return self.root.down
	
	def _grow_square(self, block):
		# wrap the current root in a new root, and extending with either a down or a right box
		w = block.w + self.root.w
		h = block.h + self.root.h
		# extend in the smallest direction
		if w < h:
			return self._grow_right(block)
		else:
			return self._grow_down(block)

	def _grow_pow2(self, block):
		# wrap the current root in a new root, and extending with either a down or a right box
		w = block.w + self.root.w
		h = block.h + self.root.h
		# extend in the direction that will keep the dimensions closest to powers of two
		def _pow2diff(value):
			return _pow2(value) - value
		e1 = _pow2diff(w) + _pow2diff(self.root.h)
		e2 = _pow2diff(self.root.w) + _pow2diff(h)
		if e1 <= e2:
			return self._grow_right(block)
		else:
			return self._grow_down(block)
	
	def _grow(self, block):
		#return self.grow_square(block)
		return self._grow_pow2(block)

if __name__ == "__main__":

	import sys
	import os
	from PIL import Image
	from random import shuffle
	import getopt

	POW2 = False
	OUTPUT = "output.png"
	HEADER = None
	VERBOSE = False
	TEXT = False
	
	def usage():
		print """\
%s [-o OUTPUT][-j HEADER][-v][-t][-h] <images...>
This is a python script that reads in the names of a bunch of image files,
and proceeds to pack them into a rectangular image area.
Options:
   -p Force the output image to have power of two dimensions
   -o OUTPUT Places the image sheet into a file named OUTPUT
      (default: "output.png")
   -j HEADER Creates a C-style header with the placement information in a 
      file named HEADER
      (default: no header is created)
   -v Outputs summary data about utilised area to standard output
   -t Outputs the filenames and their placements to standard output\
""" % (sys.argv[0])

	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], "po:j:vth")
	except Exception as e:
		print "Error:", str(e)
		usage()
		sys.exit(1)
	for opt, arg in opts:
		if opt == "-p":
			POW2 = True
		elif opt == "-o":
			OUTPUT = arg
		elif opt == "-j":
			HEADER = arg
		elif opt == "-v":
			VERBOSE = True
		elif opt == "-t":
			TEXT = True
		elif opt == "-h":
			usage()
			sys.exit(0)
		else:
			usage()
			sys.exit(1)
	
	if len(args) == 0:
		print "Error: Missing input images"
		usage()
		sys.exit(1)
	
	# read and manipulate the images in full RGBA format
	fmt = 'RGBA'
	
	# load and sort the images
	images = [(Image.open(name).convert(fmt), name) for name in args]
	# note, the images can be sorted in any order, as the packer object can
	# dynamically adjust the boxes to accept any sized object at any time.
	# But the most efficient packing sort order seems to be some variant
	# of max..min, ie. largest images to smallest images, for some definition
	# of largest and smallest.
	# Randomising the image list can sometimes resultant in better utilisation
	# of the spritesheet, but the results are of course not deterministic.
	#images.sort(key = lambda x: x[0].size[0]*x[0].size[1], reverse = True)
	images.sort(key = lambda x: max(x[0].size), reverse = True)
	#shuffle(images)

	# create a Block per image that corresponds to the image size, and stores the image as data
	blocks = [Block(img[0].size, img) for img in images]

	# create a Packer instance, and fit all the blocks into it
	packer = Packer()
	packer.fit(blocks)
	
	# create a new image, which can hold the packer's layout
	if POW2:
		size = [_pow2(v) for v in packer.root.size]
	else:
		size = packer.root.size
	image = Image.new(fmt, size)
	# paste each image into its allocated spot, as calculated by the packer
	for block in blocks:
		image.paste(block.data[0], (block.x, block.y))
	image.save(OUTPUT)

	if VERBOSE:
		# output some utilisation info
	
		# calculate the total area used by the images
		imagearea = 0
		for block in blocks:
			imagearea += block.w * block.h
		print "total used area: %i pixels" % imagearea

		# calculate the area of the output image
		print "output image size: %ix%i" % (packer.root.w, packer.root.h)
		outputarea = packer.root.w * packer.root.h
		print "output image area: %i pixels" % outputarea
		print "output area usage: %0.1f%%" % (100.0*imagearea/outputarea)
	
		# calculate the area of the output image, enlarged to a power-of-two size
		w2, h2 = [_pow2(v) for v in packer.root.size]
		print "output image pow2 size: %ix%i" % (w2, h2)
		outputarea2 = w2*h2
		print "output image pow2 area: %i pixels" % outputarea2
		print "output image pow2 usage: %0.1f%%" % (100.0*imagearea/outputarea2)

	if HEADER:
		# output the C-style header
		# A number of enums are output, which are similar to the filenames
		# Then a table of positions and size are output.
		# The enums can be used to index into the table to find the image data.
		
		def scrub(name):
			return os.path.splitext(os.path.basename(name))[0].replace("-", "_")
		
		names = "\n".join(["\t% -24s, /* %s */" % (scrub(block.data[1]), block.data[1]) for block in blocks])
		coords = "\n".join(["\t{ % 5i, % 5i, % 5i, % 5i }," % (block.x, block.y, block.w, block.h) for block in blocks])
	
		cheader = open(HEADER, "w")
		cheader.write("""\
enum ImageID
{
%s
};

typedef struct Image Image;
struct Image
{
	uint32_t x, y, w, h;
};
Image gImages[] =
{
%s
};
""" % (names, coords))
		cheader.close()
	
	if TEXT:
		# output each block, using the associated filename, position and size
		for block in blocks:
			print block.data[1], block.x, block.y, block.w, block.h

