import schedule
import time
import os
import twitter as tw
import logging
import boto3
import botocore

from random import shuffle


logging.basicConfig(filename='tweet.log', level=logging.WARNING)

domain = 'newton_tweets' # sdb.create_domain(DomainName="newton_tweets")
last_seen = 'last_seen'
pace = 656 # minutes


def get_client():
    return boto3.client('sdb')


def initialize():
    sdb = get_client()
    with open('tweet-content.txt', 'r') as f:
        raw_tweets = f.readlines()
    for tweet in raw_tweets:
        tweet = tweet.strip()
        attributes = [
            {'Name': last_seen, 'Value': str(time.time())}
        ]
        expected = {'Name': 'last_seen',
                    'Exists': False}

        try:
            sdb.put_attributes(DomainName=domain,
                               ItemName=tweet,
                               Attributes=attributes,
                               Expected=expected)
        except botocore.exceptions.ClientError as e:
            logging.info(e)


def cleanup_db(c, raw_tweets):

    tweets_in_db = c.select(SelectExpression='select Name from newton_tweets')['Items']
    tweets_in_db = set(x['Name'] for x in tweets_in_db)
    # ... need to delete old tweets from db


def send_tweet(s):
    cred = {
        "consumer_key": os.environ['NEWTON_CONSUMER_KEY'],
        "consumer_secret": os.environ['NEWTON_CONSUMER_SECRET'],
        "token": os.environ['NEWTON_TOKEN'],
        "token_secret": os.environ['NEWTON_TOKEN_SECRET'],
    }
    auth = tw.OAuth(**cred)
    t = tw.Twitter(auth=auth)
    t.statuses.update(status=s)
    print("Sent tweet: {}".format(s))


def grab_old_tweet(c):
    q = "select Name, {} from {}".format(last_seen, domain)
    tweets = c.select(SelectExpression=q)['Items']
    tweets = {d['Name']: float(d['Attributes'][0]['Value'])
              for d in tweets}
    tweets = sorted(tweets, key=tweets.get) # sort by last tweeted
    tweets = tweets[0:10]
    shuffle(tweets)
    tweet = tweets[0]
    return tweet.replace(" / ", "\n")


def update_db(c, tweet):
    c.put_attributes(DomainName=domain,
                     ItemName=tweet,
                     Attributes=[{'Name': last_seen,
                                  'Value': str(time.time()),
                                  'Replace': True}])


def tweet():
    c = get_client()
    tweet = grab_old_tweet(c)
    send_tweet(tweet)
    update_db(c, tweet)


if __name__ == '__main__':
    initialize()

    tweet()
    schedule.every(pace).minutes.do(tweet)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logging.error(e)
        time.sleep(60)
