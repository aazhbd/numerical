from numbapro import cuda
import numpy as np
from timeit import default_timer as timer

@cuda.jit
def cu_fact(d_primes, number, ffactor):
    bx = cuda.blockIdx.x
    bw = cuda.blockDim.x
    tx = cuda.threadIdx.x
    i = tx + bx * bw * 24

    # step 1
    if number % d_primes[i] == 0:
        ffactor[0] = d_primes[i]
        return

    # step 2
    if number % d_primes[i + cuda.blockDim.x * 1] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 1]
        return

    # step 3
    if number % d_primes[i + cuda.blockDim.x * 2] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 2]
        return

    # step 4
    if number % d_primes[i + cuda.blockDim.x * 3] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 3]
        return

    # step 5
    if number % d_primes[i + cuda.blockDim.x * 4] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 4]
        return

    # step 6
    if number % d_primes[i + cuda.blockDim.x * 5] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 5]
        return

    # step 7
    if number % d_primes[i + cuda.blockDim.x * 6] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 6]
        return

    # step 8
    if number % d_primes[i + cuda.blockDim.x * 7] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 7]
        return

    # step 9
    if number % d_primes[i + cuda.blockDim.x * 8] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 8]
        return

    # step 10
    if number % d_primes[i + cuda.blockDim.x * 9] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 9]
        return

    # step 11
    if number % d_primes[i + cuda.blockDim.x * 10] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 10]
        return

    # step 12
    if number % d_primes[i + cuda.blockDim.x * 11] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 11]
        return

    # step 13
    if number % d_primes[i + cuda.blockDim.x * 12] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 12]
        return

    # step 14
    if number % d_primes[i + cuda.blockDim.x * 13] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 13]
        return

    # step 15
    if number % d_primes[i + cuda.blockDim.x * 14] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 14]
        return

    # step 16
    if number % d_primes[i + cuda.blockDim.x * 15] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 15]
        return

    # step 17
    if number % d_primes[i + cuda.blockDim.x * 16] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 16]
        return

    # step 18
    if number % d_primes[i + cuda.blockDim.x * 17] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 17]
        return

    # step 19
    if number % d_primes[i + cuda.blockDim.x * 18] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 18]
        return

    # step 20
    if number % d_primes[i + cuda.blockDim.x * 19] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 19]
        return

    # step 21
    if number % d_primes[i + cuda.blockDim.x * 20] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 20]
        return

    # step 22
    if number % d_primes[i + cuda.blockDim.x * 21] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 21]
        return

    # step 23
    if number % d_primes[i + cuda.blockDim.x * 22] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 22]
        return

    # step 24
    if number % d_primes[i + cuda.blockDim.x * 23] == 0:
        ffactor[0] = d_primes[i + cuda.blockDim.x * 23]
        return


def cuda_factor(number, primes):
    device = cuda.get_current_device()
    ffactor = np.asarray([1])
    dfact = cuda.to_device(ffactor)
    length = len(primes)
    d_primes = cuda.to_device(np.asarray(primes))

    tpb = 720
    bpg = 334
    cu_fact[bpg, tpb](d_primes, number, dfact)
    c = dfact.copy_to_host()
    return c


class Factorization:
    number = 1
    primes = []
    facts = []
    def setPrimes(self, n=99999999):
        sieve = [True] * n
        for i in range(3, int(n**0.5) + 1, 2):
            if sieve[i]:
                sieve[i * i::2 * i] = [False] * ((n - i * i - 1) / (2 * i) + 1)
        self.primes = [2] + [i for i in xrange(3, n, 2) if sieve[i]]

    def setFactors(self, number):
        self.number = number
        self.facts = cuda_factor(self.number, self.primes)

    def getFactors(self):
        f = []
        for i in self.facts:
            f.append(str(i))
        return f

    def showFactors(self):
        print "Factors " + str(self.number) + " = ", self.facts


def main():
    f = Factorization()
    f.setPrimes()

    """
    start = timer()
    f.setFactors(9999996000000319)
    total = timer() - start
    print "Time taken : ", total
    print " X ".join(f.getFactors())
    """

    for num in xrange(10000, 10010):
        start = timer()
        f.setFactors(num)
        total = timer() - start
        print "Time taken : ", total
        f.showFactors()



if __name__ == '__main__':
    main()
