import math
from decimal import *

from time import clock


def serial_factor(number, primes):
    facts = []
    for prime in primes:
        if number % prime == 0:
            facts.append(int(prime))

    return facts


class Factorization:
    """ Factorization procedures """
    number = 1
    primes = []
    facts = []

    def setPrimes(self, n=99999999):
        sieve = [True] * n
        for i in xrange(3, int(n**0.5) + 1, 2):
            if sieve[i]:
                sieve[i * i::2 * i] = [False] * ((n - i * i - 1) / (2 * i) + 1)
        self.primes = [2] + [i for i in xrange(3, n, 2) if sieve[i]]


    def setFactsSerial(self, number):
        """Serial procedure to set the factors"""
        self.number = number

        length = len(self.primes)
        i = 0
        while i < length and self.primes[i] * self.primes[i] < self.number:
            while self.number % self.primes[i] == 0:
                self.facts.append(self.primes[i])
                self.number = self.number / self.primes[i]
            i = i + 1

        if self.number != 1:
            self.facts.append(self.number)


    def closestPrimeIndex(self, values, item):
        low = 0
        high = len(values) - 1

        v = 0

        while low <= high:
            mid = int((low + high) / 2)
            v = values[mid]

            if item < v:
                high = mid - 1
            elif item > v:
                low = mid + 1
            else:
                return mid

        return mid


    def setFactors(self, number):
        """Parallel procedure to set the factors"""
        self.number = number
        length = len(self.primes)
        p = self.primes[:self.closestPrimeIndex(self.primes, self.number**0.5) + 1]

        start = clock()
        self.facts = serial_factor(self.number, p)
        print "Time taken ======================> ", clock() - start

        c = 1
        for fact in self.facts:
            c = c * fact

        if c != self.number:
            num = self.number / c
            for fact in self.facts:
                while num % fact == 0:
                    num = num / fact

            if num != 1:
                self.facts.append(num)


    def getFactors(self):
        return self.facts

    def showFactors(self):
        print "Factors of " + str(self.number) + " = ", self.facts


def main():
    f = Factorization()
    f.setPrimes()

    #f.setFactors(49)
    #f.showFactors()

    #composites = [91, 91, 931, 9797, 93593, 965231, 9888989, 94988291, 901992899, 9804448273, 96019084153, 969379543943, 9931238365777, 94481825288417, 996300203249485, 9697399759230751]

    composites = [9999846400589599,
                    9999850400559479,
                    9999851600550563,
                    9999856600513513,
                    9999863000469161,
                    9999865200454267,
                    9999867200440847,
                    9999869600425079,
                    9999872600405669,
                    9999877400375573,
                    9999883800337237,
                    9999887600315843,
                    9999892000291159,
                    9999899000254829,
                    9999902600237153,
                    9999905600222663,
                    9999908000211599,
                    9999908800207927,
                    9999909800203397,
                    9999911400196213,
                    9999915000180481,
                    9999917600169743,
                    9999920000159879,
                    9999922800148987,
                    9999924000144391,
                    9999926600134589,
                    9999932000115311,
                    9999938000095931,
                    9999942400082863,
                    9999949400063333,
                    9999956000048351,
                    9999960800038127,
                    9999964800030967,
                    9999966600027853,
                    9999968600024633,
                    9999977800010557,
                    9999987200004071,
                    9999990000002419,
                    9999993000001189,
                    9999996000000319]

    #composites = [9697399759230751, 9697399759230751, 9697399759230751, 9697399759230751, 9697399759230751, 9697399759230751, 9697399759230751, 9697399759230751, 9697399759230751, 9697399759230751]

    #composites = [97, 97, 10403, 9999996000000319]

    #composites = [49, 49, 9409, 994009, 99460729, 9998200081, 999966000289, 99999820000081, 9999997800000121]

    #composites = [9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273]

    for composite in composites:
        f.setFactors(composite)
        f.showFactors()



if __name__ == '__main__':
    main()
