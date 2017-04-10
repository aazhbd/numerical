#!/home/zakir/Downloads/env/bin/python
"""
Integer Factorization
"""
import time
import sqlite3
import click

from random import randint

@click.command()
@click.option('--num', default=9999983600001683, help='The number to be factorized')
def main(num):
    """CLI tool to factorize an integer."""
    start = time.time()

    app = Factors(num)
    app.setPrimes()
    app.setFacts()
    app.showFactors()

    end = time.time()
    click.echo("Time taken : " + str(end - start))


class Factors:
    """deal with factors"""
    p_range = 99999999
    facts = []
    primes = []

    def __init__(self, number):
        self.number = int(number)

    def setPrimes(self):
        """Set all primes in range"""
        n = self.p_range
        sieve = [True] * n
        for i in range(3, int(n**0.5) + 1, 2):
            if sieve[i]:
                sieve[i * i::2 * i] = [False] * ((n - i * i - 1) / (2 * i) + 1)
        self. primes = [2] + [i for i in xrange(3, n, 2) if sieve[i]]

    def setFacts(self):
        """ set the factors """
        length = len(self.primes)
        click.echo("Using total primes : " + str(length))
        i = 0
        while i < length and self.primes[i] * self.primes[i] < self.number:
            while self.number % self.primes[i] == 0:
                self.facts.append(self.primes[i])
                self.number = self.number / self.primes[i]
            i = i + 1

        if self.number != 1:
            self.facts.append(self.number)

    def showPrimes(self):
        click.echo(self.primes)

    def showFactors(self):
        click.echo(self.facts)


if __name__ == '__main__':
    main()
