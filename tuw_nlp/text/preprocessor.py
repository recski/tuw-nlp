import argparse
import sys

from tuw_nlp.text.preprocess.germeval import preprocess_germeval


PREPROCESSOR_FUNCTIONS = {
    "germeval": preprocess_germeval
}


class Preprocessor():
    def __init__(self, what):
        if what is None:
            self.fnc = lambda x: x
        else:
            self.fnc = PREPROCESSOR_FUNCTIONS[what]

    def __call__(self, input_text):
        return self.fnc(input_text)


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-p", "--preprocessor", default=None, type=str)
    return parser.parse_args()


def main():
    args = get_args()
    preproc = Preprocessor(args.preprocessor)
    for line in sys.stdin:
        print(preproc(line.strip()))


if __name__ == "__main__":
    main()
