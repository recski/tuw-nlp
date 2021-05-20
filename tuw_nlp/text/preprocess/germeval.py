import sys

from tuw_nlp.text.utils import preprocess_tweet


def preprocess_germeval(tweet, keep_hashtag=True, keep_username=True):
    tw = preprocess_tweet(
        tweet, keep_hashtag=keep_hashtag, keep_username=keep_username)
    tw = tw.replace(' |LBR| ', '\n')
    return tw


def main():
    for line in sys.stdin:
        print(preprocess_germeval(line.strip()))


if __name__ == '__main__':
    main()
