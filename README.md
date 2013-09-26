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

The code and algorithm is loosely based on [the work of Jake Gordon](http://codeincomplete.com/posts/2011/5/7/bin_packing/)
However, Jake's hierarchy of nodes is organised different from my hierarchy of
boxes. More significantly, the input images in Jake's example *have* to be
sorted from largest to smallest, in order for his algorithm to work.
His write-up on the topic is very good though, and I wouldn't have written this
code without reading his article.

