#!/usr/bin/python3
#
# train to listen to code by hearing, and responding.
# track which letters cause errors and count, and remove the counts
# when they are corect
#
#
import time as time
import random
import sys
import pickle
import copy
from multiprocessing.connection import Client

historyfile = 'errors.pickle'
max_delay = 10
weights = {}
intr_address = ('127.0.5.1', 16323)
intr_conn = Client(intr_address)


# send interpretation of key stroke
def sendinterpret( msg ):
                
   global intr_conn

   try:
       intr_conn.send(msg)
   except Exception as err: 
       intr_conn = Client(intr_address)
       intr_conn.send(msg)
       print('err', err) 
      

def send(message):
    
        sendinterpret( message )

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
        return random.choices(list(weights.keys()), weights=weights, k=1)[0]

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
                start = time.perf_counter() # after the send
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

                time_taken = time.perf_counter() - start
                new_delay = min(max_delay, time_taken ) # max in case 
                old_delay = weights[nextword]
                delay = reweight(new_delay, old_delay)

                if user.upper() == nextword.upper():
                        print(f'{count:3d} CORRECT time {new_delay:5.2f}s  avg {delay:5.2f}s' )
                        weights[nextword] = delay
                else:
                        print(f'{count:3d} WRONG word was {nextword}' )
                        weights[nextword] = max_delay*2  # extra emphasis
   
                savehist(weights)
                time.sleep(2)
           

train(sys.argv)
