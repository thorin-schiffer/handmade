import os
import sys
from invoke import cli


def main():
    path = os.path.dirname(__file__)
    cli.dispatch(sys.argv + ['-r', path])
