import sys

from tuw_nlp.text.utils import preprocess_tweet


def preprocess_germeval(tweet):
    tw = preprocess_tweet(tweet)
    tw = tw.replace(' |LBR| ', ' ')
    return tw


def main():
    for line in sys.stdin:
        print(preprocess_germeval(line.strip()))


if __name__ == '__main__':
    main()
