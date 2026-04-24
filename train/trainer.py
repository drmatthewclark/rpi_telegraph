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
import copy

qos = 0
historyfile = 'errors.pickle'
max_delay = 10
topic = 'telegraph'
host = 'localhost'
weights = {}

gap = 60

def send(message):
        client = mqtt.Client(protocol=mqtt.MQTTv5, client_id='trainer')
        res = client.connect(host)
        ecode, count  = client.publish(topic, message.encode('utf8'), qos)

def readwords(files):
        w = readhist()
        for wordfile in files[1:]:
            with open(wordfile, 'r') as file:
                for word in file:
                   word = word.strip()
                   if word in w:
                       weights[word] = min(max_delay, w[word] )
                   else:
                       print(f'{word} not in weights' )
                       weights[word.strip()] = max_delay
        analyze(weights)


def savehist(weights):
        with open(historyfile, 'wb') as f:
                pickle.dump(weights, f)

def readhist():
        
        try:
           with open(historyfile, 'rb') as file:
               wg = pickle.load(file)
               return wg

        except Exception as err:
           print(f'readhist: {err}' )

        return {}



def pickword(weights):
        return random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]

def analyze(weights):
   sort = dict(sorted(weights.items(), key=lambda item: item[1]))
   print(f'word\tdelay' )
   for item in sort:
      print(f'{item}\t{sort[item]:5.2f}' )


def reweight(new_delay, old_delay):
   delay = old_delay - (old_delay - new_delay)/3   #exponential decay
   return delay

def train(files):

        count = 0
        readwords(files)
        print('read', len(weights), 'words' )

        while True:
                count += 1
                nextword = pickword(weights)
                send(nextword)
                start = time.perf_counter()
                user = input('\nword: ').strip()   # wait for input

                if user == '@' or user.lower() == 'stop' :     #end
                        savehist(weights)
                        analyze( weights )
                        exit(0)

                elif user == '!':      # get stats
                        analyze(weights)
                        next

                while user == '#':   # ask for repeat
                        send(nextword) 
                        user = input('word: ')


                new_delay = min(max_delay, time.perf_counter() - start ) # max in case 
                old_delay = weights[nextword]
                delay = reweight(new_delay, old_delay)

                if user.upper() == nextword.upper():
                        print(f'CORRECT time {new_delay:5.2f}s  avg {delay:5.2f}s' )
                        weights[nextword] = delay
                else:
                        print(f'WRONG word was {nextword}' )
                        #weights[nextword] = reweight( max_delay, old_delay )
                        weights[nextword] = max_delay
   
                savehist(weights)
                time.sleep(2)
           

train(sys.argv)
