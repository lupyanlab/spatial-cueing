#!/usr/bin/env python
from unipath import Path
from psychopy.visual import ImageStim
from random import shuffle

class DynamicMask(object):
    def __init__(self, **kwargs):
        """ Create an ImageStim-like object that draws different images.

        Parameters
        ----------
        kwargs: Arguments to pass to each psychopy.visual.ImageStim object
        """
        util = Path(__file__).absolute().parent
        pngs = Path(util, 'dynamicmask').listdir(pattern = '*.png')

        # workaround: psychopy checks type of image argument and expects str
        pngs = map(str, pngs)

        self.masks = [ImageStim(image = img, **kwargs) for img in pngs]
        self._ix = 0

    def draw(self):
        """ Draws a single mask """
        self.masks[self._ix].draw()
        self._ix = (self._ix + 1) % len(self.masks)

        if self._ix == 0:
            shuffle(self.masks)

    def setPos(self, pos):
        """ Change the position for all masks"""
        for mask in self.masks:
            mask.setPos(pos)

if __name__ == '__main__':
    """ Demo of the dynamic mask in action """
    from psychopy import core
    from psychopy.visual import Window

    window = Window(size = (500, 500), units = 'pix', monitor = 'testMonitor')
    dynamic_mask = DynamicMask(win = window, size = (200, 200))

    for _ in xrange(25):
        dynamic_mask.draw()
        window.flip()
        core.wait(0.05)
