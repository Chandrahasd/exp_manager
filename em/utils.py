import sys

class MultiOut(object):
    def __init__(self, *args):
        self.handles = args

    def write(self, s):
        for f in self.handles:
            f.write(s)

def testMultiOut():
    with open('q1', 'w') as f1, open('q2', 'w') as f2, open('q3', 'w') as f3:
    # add all the files (including sys.stdout) to which the output should be written
        sys.stdout = MultiOut(f1, f2, sys.stdout)
        for i, c in enumerate('abcde'):
            print(c, 'out')
            print(i, 'err')
