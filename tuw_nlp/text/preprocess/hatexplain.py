import sys
import re

def regularize_im(tweet):
    tweet = re.sub(r"\bi[ ]*['´`’]*[ ]*m\b", "i'm", tweet, flags=re.I)
    return tweet

def preprocess_hatexplain(tweet):
    tweet = regularize_im(tweet)
    return tweet

def main():
    """
    test = ["I ' m super gay fuck",
        "im impatient im awesome i'm gay",
        "impatient I am",
        "m gay",
        "i ’ m super gay fuck",
        "im gay i love fathers dm for dilfs",
        "when i say i only like seven men i mean i only love seven men bc im fucking gay",
        "yeah im def gay"]
    """
    for line in sys.stdin:
        print(preprocess_hatexplain(line.strip()))


if __name__ == '__main__':
    main()
    