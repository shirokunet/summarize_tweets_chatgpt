#!/usr/bin/env python
# coding: utf-8

import datetime
import pytz
import re
import sys
import time
import tweepy
import yaml
from pyChatGPT import ChatGPT


def convertJstDate(date_s):
    t = time.strptime(date_s,'%Y-%m-%dT%H:%M:%S.000Z')
    utc = pytz.timezone('UTC')
    d = datetime.datetime(*t[:6], tzinfo=utc)
    tm = d.astimezone(pytz.timezone('Asia/Tokyo'))
    return int(tm.strftime('%m')), tm.strftime('%m/%d: ')

def main():
    args = sys.argv

    # Load prams
    cfgs = yaml.load(open('params.yml'), Loader=yaml.SafeLoader)

    # Twitter
    tweepy_api = tweepy.Client(None, 
        cfgs['twitter_consumer_key'], cfgs['twitter_consumer_key_secret'], 
        cfgs['twitter_access_token'], cfgs['twitter_access_token_secret'])
    client = tweepy.Client(cfgs['twitter_bearer_token'])
    user=tweepy_api.get_user(username=cfgs['twitter_user_id'],
        user_fields=['description','protected','name','username','public_metrics','profile_image_url']
        ,user_auth=True)
    tweet_data = []
    for tweet in tweepy.Paginator(client.get_users_tweets, id=user.data.id, max_results=100, 
        tweet_fields=["created_at"], exclude="retweets,replies", since_id=cfgs['twitter_since_id']).flatten(limit=1000):
        tweet_filterd = re.sub(r"(https?)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+)", "" ,tweet.text)
        if tweet_filterd:
            tweet_data.append([tweet.data['created_at'],tweet_filterd])
    tweet_data.reverse()
    print(tweet_data)

    # Prepare input string
    convertJstDate(tweet_data[0][0])
    input_str_month = []
    for i in range(12):
        input_str_month.append('')
    for tweet in tweet_data:
        tweet_splited = tweet[1].split('\n')
        month, date_s = convertJstDate(tweet[0])
        for tweet_s in tweet_splited:
            if tweet_s:
                for twitter_filter_world in cfgs['twitter_filter_worlds']:
                    if not twitter_filter_world in tweet_s:
                        input_str_month[month-1] += '- '+ date_s + tweet_s + '\n'
    input_str_quater = []
    for i in range(4):
        input_str_quater.append(input_str_month[i*3] + input_str_month[i*3+1] + input_str_month[i*3+2])
    input_str_quater[0].splitlines(True)

    # ChatGPT
    chat_gpt_api = ChatGPT(cfgs['chatgpt_session_token'])  # auth with session token
    chat_gpt_api.reset_conversation()
    chat_gpt_api.clear_conversations()
    send_data = args[0] + '\n' + input_str_month[0]
    print('\n',send_data)
    resp = chat_gpt_api.send_message(send_data.splitlines(True))

if __name__ == '__main__':
    main()
