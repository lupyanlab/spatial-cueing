from psychopy.data import StairHandler

import numpy as np

def new_staircase(desired_accuracy):
    # after there have been how many incorrect trials
    # should you move the opacity up?
    nUp = 10 - desired_accuracy * 10

    # after how many correct trials should you
    # move the opacity down?
    nDown = desired_accuracy * 10

    starting_opacity = 0.8
    staircase = StairHandler(starting_opacity,
            nReversals = 4, stepSizes = [0.2, 0.1, 0.06, 0.03], stepType = 'lin',
            nTrials = 100, nUp = nUp, nDown = nDown,
            minVal = 0.01, maxVal = 1.0)

    return staircase

def simulate_trials(staircase, answers):
    for opacity in staircase:
        trial_n = staircase.thisTrialN
        print 'Running trial {} with opacity: {}'.format(trial_n, opacity)

        graded = answers[trial_n]
        print 'Got {} response: {}'.format({1:'incorrect', 0:'correct'}[graded], graded)

        staircase.addResponse(graded)

    print 'Final opacity = {}'.format(staircase.intensities[-1])
    print 'Final accuracy = {}'.format(np.array(answers).mean())

#all_correct_answers = [1 for _ in range(100)]
#staircase = new_staircase(0.5)
#simulate_trials(staircase, all_correct_answers)

def simulate_real_threshold(staircase, opacity_cutoff):
    for opacity in staircase:
        trial_n = staircase.thisTrialN
        graded = 1 if opacity > opacity_cutoff else 0

        if np.random.rand() >= 0.9:  # flip on 10% of trials
            print 'unhelpful trial'
            graded = 1 if graded == 0 else 0

        print 'Running trial {} with opacity {}: got response {}'.format(
            trial_n, opacity, graded)

        staircase.addResponse(graded)

    print 'Final opacity = {}'.format(np.array(staircase.intensities[-10:]).mean())
    print 'Final accuracy = {}'.format(np.array(staircase.data).mean())

staircase = new_staircase(desired_accuracy = 0.9)
simulate_real_threshold(staircase, opacity_cutoff = 0.5)

# notes
# - whether or not a staircase will work depends on the relative relationship
#   between desired accuracy, step sizes, and number of trials
# - piloting will be helpful here!
# - staircases reach a desired accuracy by specifying nUp and nDown to
#   approximate the desired boundaries
