import random
import sys

import sqlite3

def is_probable_prime(n, k = 7):
   """use Rabin-Miller algorithm to return True (n is probably prime) or False (n is definitely composite)"""

   #print "Starting to check whether " + str(n) + " is prime"

   if n < 6:  # assuming n >= 0 in all cases... shortcut small cases here
      return [False, False, True, True, False, True][n]
   elif n & 1 == 0:  # should be faster than n % 2
      return False
   else:
      s, d = 0, n - 1
      while d & 1 == 0:
         s, d = s + 1, d >> 1
      # Use random.randint(2, n-2) for very large numbers
      for a in random.sample(xrange(2, min(n - 2, sys.maxint)), min(n - 4, k)):
         x = pow(a, d, n)
         if x != 1 and x + 1 != n:
            for r in xrange(1, s):
               x = pow(x, 2, n)
               if x == 1:
                  return False  # composite for sure
               elif x == n - 1:
                  a = 0  # so we know loop didn't continue to end
                  break  # could be strong liar, try another a
            if a:
               return False  # composite if we reached end of this loop
      return True  # probably prime if reached end of outer loop


def main():
    db = sqlite3.connect('primes99')
    cursor = db.cursor()
    
    cursor.execute('''create table if not exists primes(id INTEGER PRIMARY KEY, prime INTEGER)''')
    db.commit()

    num = 0

    cursor.execute('INSERT INTO primes(prime) VALUES(' + str(2) + ')')
    db.commit()
    num = num + 1

    i = 3
    while True:
        if is_probable_prime(i, 2):
            cursor.execute('INSERT INTO primes(prime) VALUES('+ str(i) +')')
            db.commit()
            print str(i) + ' is prime and inserted'
            num = num + 1

        i += 2
        if i >= 9999999999:
            print "total collected : ", num
            break

    db.close()


if __name__ == '__main__':
    main()
