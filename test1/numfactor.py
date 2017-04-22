#!/home/zakir/Downloads/env/bin/python
"""
Integer Factorization
"""
import time
import sqlite3
import click
from timeit import default_timer as timer
from math import sqrt, ceil

from random import randint

@click.command()
@click.option('--num', default=9999983600001683, help='The number to be factorized')
def main(num):
    """CLI tool to factorize an integer."""
    app = Factors()
    app.setPrimes()

    """
    for n in range(1000000000000000, 1000000000000010):
        start = timer()
        app.facts = []
        app.setFacts(n)
        print 
        total = timer() - start
        print "Time taken : ", total
        app.showFactors()
    """
    start = timer()
    app.setFacts(num)
    total = timer() - start
    app.showFactors()
    print "Time taken : ", total



class Factors:
    """deal with factors"""
    p_range = 99999999
    facts = []
    primes = []

    def setPrimes(self):
        """Set all primes in range"""
        n = self.p_range
        sieve = [True] * n
        for i in range(3, int(n**0.5) + 1, 2):
            if sieve[i]:
                sieve[i * i::2 * i] = [False] * ((n - i * i - 1) / (2 * i) + 1)
        self. primes = [2] + [i for i in xrange(3, n, 2) if sieve[i]]


    def setFacts(self, number):
        self.number = int(number)
        length = len(self.primes)
        #click.echo("Using total primes : " + str(length))
        i = 0
        while i < length:
            if self.number % self.primes[i] == 0:
                self.facts.append(self.primes[i])
            i = i + 1


    def showPrimes(self):
        click.echo(self.primes)

    def showFactors(self):
        print "Factors " + str(self.number) + " = ", self.facts


if __name__ == '__main__':
    main()
