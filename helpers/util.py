import random


def random_line(filename):
    lines = open(filename).read().splitlines()
    return random.choice(lines)