import sys
from modules import Pipeline

def initialize():
    processor = Pipeline.Pipeline()
    processor.readFiles(sys.argv)
    processor.readyOutput(sys.argv[4])
    return processor


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python simulator.py inst.txt data.txt config.txt result.txt")
    else:
        proc = initialize()
        proc.simulate()
