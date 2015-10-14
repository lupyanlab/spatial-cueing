from psychopy import visual, event

class Experiment(object):
    def show_text(self, text, **kwargs):
        settings = {
            'wrapWidth': 1000,
        }
        settings.update(kwargs)
        text = visual.TextStim(self.window, text=text, **settings)
        text.draw()
        self.window.flip()
        event.waitKeys()
