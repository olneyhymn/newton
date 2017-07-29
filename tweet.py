import os
import twitter as tw
import logging
import time

from nodb import NoDB
from random import shuffle

tweet_content = "tweet-content.txt"
tweet_lookup = "tweet-lookup.shelve"
logging.basicConfig(filename='tweet.log', level=logging.WARNING)


def get_raw_tweets():
    tweets = []
    with open(tweet_content, 'r') as f:
        raw_tweets = f.readlines()
        for tweet in raw_tweets:
            tweets.append(tweet.strip())
    return tweets


def send_tweet(s):
    cred = {
        "consumer_key": os.environ['NEWTON_CONSUMER_KEY'].strip(),
        "consumer_secret": os.environ['NEWTON_CONSUMER_SECRET'].strip(),
        "token": os.environ['NEWTON_TOKEN'].strip(),
        "token_secret": os.environ['NEWTON_TOKEN_SECRET'].strip(),
    }
    auth = tw.OAuth(**cred)
    t = tw.Twitter(auth=auth)

    s = s.replace(" / ", "\n")
    t.statuses.update(status=s)
    print("Sent tweet: {}".format(s))


def get_db(bucket="olneyhymnbots",
           serializer="json",
           index="content"):
    db = NoDB()
    db.bucket = bucket
    db.human_readable_indexes
    db.serializer = serializer
    db.index = index
    return db


def tweets_ordered_by_last_sent_time():
    db = get_db()
    last_sent = {}
    for tweet in get_raw_tweets():
        d = db.load(tweet)
        if d is None:
            last_sent[tweet] = 0
        else:
            last_sent[tweet] = d['last_sent']
    s = sorted([(time, tweet)
                for tweet, time in last_sent.items()])
    return [t for _, t in s]


def tweet(a, b):
    tweets = tweets_ordered_by_last_sent_time()
    tweets = tweets[0:10]
    shuffle(tweets)
    tweet = tweets[0]
    send_tweet(tweet)

    db = get_db()
    db.save({"content": tweet,
             "last_sent": int(time.time()),
             "from": "newton"})


if __name__ == '__main__':
    pass
