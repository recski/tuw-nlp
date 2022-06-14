import sys
import re

def regularize_im(tweet):
    tweet = re.sub(r"\bi[ ]*['´`’]*[ ]*m\b", "i am", tweet, flags=re.I)
    return tweet

def preprocess_hatexplain(tweet):
    tweet = regularize_im(tweet)
    return tweet

def main():
    for line in sys.stdin:
        print(preprocess_hatexplain(line.strip()))


if __name__ == '__main__':
    main()
    