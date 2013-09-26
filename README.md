snowball
========

An Image packing module.

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

