# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
import sys
import threading
import time
from datetime import datetime
from io import open
import json


def redirectOutput(f):
    logFile = open(f, 'w')
    stdout = sys.stdout
    sys.stdout = logFile
    return stdout


def timestamp():
    f = '%m-%d %H:%M:%S'
    value = time.localtime(int(time.time()))
    ct = time.strftime(f, value)
    return ct.decode('utf-8')


def log(*args, **kwargs):
    dt = timestamp()
    with open('log.txt', 'a', encoding='utf-8') as f:
        print(dt, *args, file=f, **kwargs)


def logParallel(*args, **kwargs):
    dt = timestamp()
    with open('log-{}.txt'.format(threading.current_thread().getName()), 'a', encoding='utf-8') as f:
        print(dt, *args, file=f, **kwargs)


def getNode(path="node.json"):
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()
        return json.loads(s)


def parallel(thrd):
    def real_decorator(func):
        def wrapper(*args, **kwargs):
            threadPool = [threading.Thread(
                target=func, args=args, kwargs=kwargs,
                name="thread-{}".format(i)) for i in range(thrd)]
            for t in threadPool:
                t.start()
                t.join()
        return wrapper
    return real_decorator


def auto(hour, minute, second, immediately=False):
    def real_decorator(job):
        def wrapper(*args, **kwargs):
            if immediately is True:
                job(*args, **kwargs)
            now = datetime.today()
            then = now.replace(day=now.day + 1, hour=hour,
                               minute=minute, second=second)
            deltaTime = then - now
            secs = deltaTime.seconds + 1
            time.sleep(secs)
            job(*args, **kwargs)
            while True:
                interval = 60 * 60 * 24
                time.sleep(interval)
                job(*args, **kwargs)
        return wrapper
    return real_decorator
