from numbapro import cuda
import numpy as np
from timeit import default_timer as timer


@cuda.jit
def cu_fact(d_primes, number, ffactor):
    bx = cuda.blockIdx.x
    bw = cuda.blockDim.x
    tx = cuda.threadIdx.x
    i = tx + bx * bw * 24

    for j in xrange(0, 24):
        if number % d_primes[i + cuda.blockDim.x * j] == 0:
            ffactor[i + cuda.blockDim.x * j] = d_primes[i + cuda.blockDim.x * j]
            return


def cuda_factor(number, primes):
    device = cuda.get_current_device()
    ffactor = np.asarray([0]*len(primes))
    dfact = cuda.to_device(ffactor)
    d_primes = cuda.to_device(np.asarray(primes))

    tpb = 720
    bpg = 334
    start = timer()
    cu_fact[bpg, tpb](d_primes, number, dfact)
    total = timer() - start
    print "Time taken : ", total
    c = dfact.copy_to_host()
    k = []
    for d in c:
        if int(d) != 0:
            k.append(int(d))
    return k



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
        return self.facts

    def showFactors(self):
        print "Factors " + str(self.number) + " = ", self.facts


def main():
    f = Factorization()
    f.setPrimes()

    #f.setFactors(9999996000000319)
    f.setFactors(9999999999999999)
    print f.getFactors()
    
    """
    for num in range(1000000000000000, 1000000000000010):
        f.setFactors(num)
        f.showFactors()
    """



if __name__ == '__main__':
    main()