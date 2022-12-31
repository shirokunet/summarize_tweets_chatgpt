#!/usr/bin/env python
# coding: utf-8

import datetime
import pprint
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
    # print(tweet_data)

    # Prepare tweet text list
    convertJstDate(tweet_data[0][0])
    input_str_month = []
    for i in range(12):
        input_str_month.append([])
    for tweet in tweet_data:
        month, date_s = convertJstDate(tweet[0])
        tweet_splited = tweet[1].split('\n')
        for tweet_s in tweet_splited:
            if tweet_s:
                input_str_month[month-1].append([date_s,tweet_s])

    # ChatGPT
    chat_gpt_api = ChatGPT(cfgs['chatgpt_session_token'], verbose=False)  # auth with session token
    chat_gpt_api.reset_conversation()
    chat_gpt_api.clear_conversations()

    while True:
        summarize_month = input("\n何月の Tweetを要約しますか？: ")

        target = input_str_month[int(summarize_month)-1]
        print('Tweet 情報は以下になります。\n')

        # filter worlds
        for twitter_filter_world in cfgs['twitter_filter_worlds']:
            target = [s for s in target if not twitter_filter_world in s[1]]
        pprint.pprint(target)
        print(len(target))

        # prepare send msgs
        start = int(input("ChatGPT へ送信する開始行数を入力して下さい。: "))
        end = int(input("ChatGPT へ送信する終了行数を入力して下さい。: "))
        input_msg = input("ChatGPT への要求文を入力して下さい。: ")
        send_data = input_msg + '\n'
        for date_and_tweet in target[start:end]:
            send_data += '- '+ date_and_tweet[0] + date_and_tweet[1] + '\n'
        # pprint.pprint(send_data)

        resp = chat_gpt_api.send_message(send_data)
        print(resp['message'])

        while True:
            input_msg = input("会話を終了する場合は END を、修正要求がある場合は文章を入力して下さい。: ")
            if input_msg == 'END':
                break
            resp = chat_gpt_api.send_message(input_msg)
            print(resp['message'])

if __name__ == '__main__':
    main()
