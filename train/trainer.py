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
import morse
import os 
from choices import choices

qos = 1  # 1 or 2 will wait for completion, 0 will return immediately
historyfile = 'errors.pickle'

topic = 'telegraph'
host = 'localhost'

# set the host
if not os.getenv('THOST') is None:
   host = os.getenv('THOST')

errors = {}
times = {}

gap = 60

def send(message):
        client = mqtt.Client('trainer')
        res = client.connect(host)
        ecode, count  = client.publish(topic, message.encode('utf8'), qos)

def readwords(files):
        wordlist = []
        for wordfile in files[1:]:
            with open(wordfile, 'r') as file:
                for word in file:
                   wordlist.append(word.strip().upper())

        print(wordlist) 
        return wordlist


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



def update_weights(wordlist, weights, times):
        new_weights = weights.copy()
        for i,c  in enumerate(wordlist):
            if c in times:
                new_weights[i] = times[c]

        for i in times:
            val = "%5.2f %s" % (times[i], i )
            print( val  )

        return new_weights

def train(files):
        count = 0
        times = {}
        wordlist = readwords(files)
        weights = [1]*len(wordlist) 
        for c in wordlist:
            times[c] = 1

        print('read', len(wordlist), 'words' )
        total = 0.0

        while True:
                count += 1
                nextword = choices(wordlist, weights=weights).upper()
                send(nextword)
                time.sleep(1.0)
                #send(nextword)

                start = time.time()

                user = input('word:').upper()
                if user == '@':   # end
                        savehist()
                        exit(0)
           
                if user == '#':   # repeat
                   send(nextword)
                   user = input('word:').upper()
 
                delay = time.time() - start
                total += delay
                average = total/count
                
                if user == nextword:
                        print('CORRECT  %6.4f ave %6.4f\n' % (delay,average) )
                        times[user] += (delay - times[user] )/3
                        
                        if 'correct' not in errors:
                                errors['correct'] = 0
                        errors['correct'] += 1

                        if nextword in errors:
                                errors[nextword] -= 1
                                if errors[nextword] == 0:
                                        del errors[nextword]
                else:
                        print('word was ', nextword, morse.morse(nextword)  )
                        if nextword in errors:
                                errors[nextword] += 1
                        else:
                                errors[nextword] = 1
                        times[nextword] += 5

                #print(errors)
                savehist()
                if len(errors) > 5 and count % 50 == 0:
                        for e in errors:
                                print('char', e )
                                send(e)
                                time.sleep(2)
                time.sleep(1)
                weights = update_weights(wordlist, weights, times)

if __name__ == '__main__':
  #readhist()
  train(sys.argv)
