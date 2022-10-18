#!/usr/bin/python3
#
# train to listen to code by hearing, and responding.
# track which letters cause errors and count, and remove the counts
# when they are corect
#
#
import paho.mqtt.client as mqtt
import time as time
import random
import sys
import pickle

qos = 0
historyfile = 'errors.pickle'

topic = 'telegraph'
host = 'localhost'
wordlist = []
errors = {}
gap = 60

def send(message):
        client = mqtt.Client('trainer')
        res = client.connect(host)
        ecode, count  = client.publish(topic, message.encode('utf8'), qos)

def readwords(files):
        for wordfile in files[1:]:
            with open(wordfile, 'r') as file:
                for word in file:
                   wordlist.append(word.strip())


def savehist():
        with open(historyfile, 'wb') as f:
                pickle.dump(errors, f)

def readhist():
        global errors
        try:
                errors = pickle.load(historyfile)
                print('errors', errors )
        except:
                pass

def train(files):

        count = 0
        readwords(files)
        print('read', len(wordlist), 'words' )
        while True:
                count += 1
                nextword = random.choice(wordlist)
                send(nextword)
                time.sleep(3)
                send(nextword)
                user = input('word:')
                if user == '@':
                        savehist()
                        exit(0)
        
                if user.upper() == nextword.upper():
                        print('correct!')
                        if 'correct' not in errors:
                                errors['correct'] = 0
                        errors['correct'] += 1

                        if nextword in errors:
                                errors[nextword] -= 1
                                if errors[nextword] == 0:
                                        del errors[nextword]
                else:
                        print('word was ', nextword )
                        if nextword in errors:
                                errors[nextword] += 1
                        else:
                                errors[nextword] = 1

                print(errors)
                savehist()
                if len(errors) > 5 and count % 50 == 0:
                        for e in errors:
                                print('char', e )
                                send(e)
                                time.sleep(2)
                time.sleep(1)

readhist()
train(sys.argv)
