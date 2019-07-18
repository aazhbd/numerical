#!/usr/bin/python

import random
import sys
import time

def is_probable_prime(n, k = 7):
   if n < 6:
      return [False, False, True, True, False, True][n]
   elif n & 1 == 0:
      return False
   else:
      s, d = 0, n - 1
      while d & 1 == 0:
         s, d = s + 1, d >> 1
      for a in random.sample(xrange(2, min(n - 2, sys.maxint)), min(n - 4, k)):
         x = pow(a, d, n)
         if x != 1 and x + 1 != n:
            for r in xrange(1, s):
               x = pow(x, 2, n)
               if x == 1:
                  return False
               elif x == n - 1:
                  a = 0
                  break
            if a:
               return False
      return True


def main():
    num = 203956878356401977405765866929034577280193993314348263094772646453283062722701277632936616063144088173312372882677123879538709400158306567338328279154499698366071906766440037074217117805690872792848149112022286332144876183376326512083574821647933992961249917319836219304274280243803104015000563790123
    start = time.time()
    if is_probable_prime(num, 2):
        print num, "is prime."
    else:
        print "not prime."
    print "taken %s seconds" % (time.time() - start)


if __name__ == '__main__':
    main()

