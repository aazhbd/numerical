from numba import cuda
import numpy as np
from timeit import default_timer as timer

import math
from decimal import *


@cuda.jit
def cu_fact(d_primes, number, ffactor):
    bx = cuda.blockIdx.x
    bw = cuda.blockDim.x
    tx = cuda.threadIdx.x
    i = tx + bx * bw #* 24

    if number % d_primes[i] == 0:
        ffactor[i] = d_primes[i]
        return


def cuda_factor(number, primes):
    device = cuda.get_current_device()
    ffactor = np.asarray([0]*len(primes))
    dfact = cuda.to_device(ffactor)
    d_primes = cuda.to_device(np.asarray(primes))

    limit = len(primes)

    getcontext().prec = 1000

    l = Decimal(limit) #/ Decimal(24)

    if l <= 1024:
        tpb = l
        bpg = 1
    else:
        tpb = 1024
        bpg = Decimal(l) / Decimal(tpb)

    itpb = int(math.ceil(tpb))
    ibpg = int(math.ceil(bpg))

    cu_fact[ibpg, itpb](d_primes, number, dfact)

    c = dfact.copy_to_host()
    k = []
    for d in c:
        if int(d) != 0:
            k.append(int(d))
    return k



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

        self.facts = cuda_factor(self.number, p)

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

    #f.setFactors(96081105597409)
    #f.setFactors(9999999999999999)
    #f.setFactors(10403)
    #f.setFactsSerial(9999996000000319)
    #f.showFactors()

    # for num in range(1000000000000000, 1000000000000010):
    #     #f.setFactsSerial(num)
    #     f.setFactors(num)
    #     f.showFactors()

    composites = [49, 49, 9409, 994009, 99460729, 9998200081, 999966000289, 99999820000081, 9999997800000121]

    #composites = [9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273, 9804448273]

    for composite in composites:
        f.setFactors(composite)
        f.showFactors()





if __name__ == '__main__':
    main()
