from psychopy import visual, event

class Experiment(object):
    def show_text(self, text, **kwargs):
        settings = {
            'wrapWidth': 1000,
            'color': 'black',
            'height': 20,
            'font': 'Consolas'
        }
        settings.update(kwargs)
        text = visual.TextStim(self.window, text=text, **settings)
        text.draw()
        self.window.flip()
        event.waitKeys()
