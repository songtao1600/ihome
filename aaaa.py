# nums = list(range(2,20))
# for i in nums:
#     nums = list(filter(lambda x:x == i or x % i,nums))
#
# print(nums)

from gevent import monkey
monkey.patch_all()

import gevent
import time

def f1():
    print("f1 begin")
    time.sleep(3)
    print("f1 end")

def f2():
    print("f2 begin")
    # time.sleep()
    print("f2 end")

# f = (f1, f2)
g1 = gevent.spawn(f1)
# g2 = gevent.spawn(f2)
# f = (g1, g2)
g1.join()
f2()
# gevent.joinall([g1,g2])





