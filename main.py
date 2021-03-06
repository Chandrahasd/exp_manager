import sys
import os
import time

import argparse

def getParser():
    parser = argparse.ArgumentParser(description="parser for arguments", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--number", type=int, help="argument 1", required=True)
    parser.add_argument("-g", "--gpu", type=int, help="gpu", default=0)
    parser.add_argument("-m", "--mul", type=int, nargs='+', help="multivalue argument")
    return parser

def printNumbers(args):
    for i in range(args.number):
        print(i)
    if args.mul is not None:
        for i in args.mul:
            print(i)

def main():
    parser = getParser()
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)
    printNumbers(args)

if __name__ == "__main__":
    main()
