import java.awt.*;
import java.math.*;
import javax.swing.*;
import java.awt.event.*;
import java.io.*;

public class BigPolyPrimeInt
{
	private int k, count, facts[], primes[], N;
	private int l;
	private boolean comp[];
	public long time, s, e;

	public boolean isSmPrime(int n)
	{
		if(comp[n] == false) return true;
		else return false;
	}

	public int largeFact()
	{
		int max, i;

		max = 1;

		for(i = 0; i <= k; i++)
		{
			if( facts[i] > max ) max = facts[i];
		}

		return max;
	}
	
	public void setFacts(int v)
	{
		int i;

		k = 0;

		for(i = 0; i < count; i++)
		{
			if(primes[i] * primes[i] > v) break;

			while(v % primes[i] == 0)
			{
				facts[k] = primes[i];

				k++;

				v /= primes[i];
			}
		}

		if(v != 1) facts[k] = v;
	}

	public double bigLog(String s)
	{
		String t;
		int l;
		double d, r;

		l = s.length();
		t = "." + s;
		d = Double.parseDouble(t);
		r = Math.log10(d) + l;

		return r;
	}

	public double bigLog(BigInteger s)
	{
		String t;
		int l;
		double d, r;

		t = "." + s.toString();
		l = t.length() - 1;
		d = Double.parseDouble(t);
		r = Math.log10(d) + l;

		return r;
	}

	public boolean isPowerOf(BigInteger n, int i)
	{
		int l;
		double len;
		BigInteger low, high, mid, res;
		
		low = new BigInteger("10");
		high = new BigInteger("10");
		
		len = (n.toString().length()) / i;
		l = (int) Math.ceil(len);
		
		low = low.pow(l - 1);
		high = high.pow(l).subtract(BigInteger.ONE);
		
		while(low.compareTo(high) <= 0)
		{
			mid = low.add(high);
			
			mid = mid.divide(new BigInteger("2"));
			
			res = mid.pow(i);
			
			if(res.compareTo(n) < 0)
			{
				low = mid.add(BigInteger.ONE);
			}
			else if(res.compareTo(n) > 0)
			{
				high = mid.subtract(BigInteger.ONE);
			}
			else if(res.compareTo(n) == 0)
			{
				System.out.println("res = " + res + " mid = " + mid);
				return true;
			}
		}
		
		return false;
	}
	
	boolean isPower(BigInteger n)
	{
		int l, i;
		
		l = (int) bigLog(n);
		
		for(i = 2; i < l; i++)
		{
			if(isPowerOf(n, i))
			{
				return true;
			}
		}
		
		return false;
	}

	long mPower(long x, long y, long n)
	{
		long m, p, z;

		m = y;
		p = 1;
		z = x;

		while(m > 0)
		{
			while(m % 2 == 0)
			{
				m = (long) m / 2;

				z = (z * z) % n;
			}
			m = m - 1;

			p = (p * z) % n;
		}

		return p;
	}

	BigInteger mPower(BigInteger x, BigInteger y, BigInteger n)
	{
		BigInteger m, p, z, two;

		m = y;
		p = BigInteger.ONE;
		z = x;
		two = new BigInteger("2");

		while(m.compareTo(BigInteger.ZERO) > 0)
		{
			while( ( (m.mod(two)).compareTo(BigInteger.ZERO) ) == 0)
			{
				m = m.divide(two);

				z = (z.multiply(z)).mod(n);
			}

			m = m.subtract(BigInteger.ONE);

			p = (p.multiply(z)).mod(n);
		}

		return p;
	}
	
	public void Sieve()
	{
		int i, j;

		N = 1000000;

		count = 0;

		comp = new boolean[N+1];

		primes = new int[78600];

		facts = new int[10000];

		comp[1] = true;

		for(i = 2; i * i <= N; i++)
		{
			if(comp[i] != true)
			{
				for(j = i * i; j <= N; j += i)
				{
					comp[j] = true;
				}
			}
		}

		for(i=2; i<=N; i++)
		{
			if(!comp[i])
			{
				primes[count] = i;
				count++;
			}
		}
	}

	public boolean isPrime(BigInteger n)
	{
		int tr, q, tm, ai, up, o;
		BigInteger r, t, x, lh, rh, fm, yai;
		
		System.out.println("start processing " + n);
		
		s = System.currentTimeMillis();

		l = (int) bigLog(n);
		
		if( isPower(n) ) return false;

		r = new BigInteger("2");
		tr = r.intValue();

		while( r.compareTo(n) < 0 )
		{
			if( (r.gcd(n)).compareTo(BigInteger.ONE) != 0 ) return false;

			tr = r.intValue();

			if( isSmPrime(tr) )
			{
				setFacts(tr - 1);

				q = largeFact();

				o = (int) (tr - 1) / q;

				tm = (int) (4 * (Math.sqrt(tr)) * l);

				t = mPower(n, new BigInteger("" + o), r);

				if( q >= tm && (t.compareTo(BigInteger.ONE)) != 0 ) break;
			}

			r = r.add(BigInteger.ONE);
		}

		x = new BigInteger("2");

		fm = (mPower(x, r, n)).subtract(BigInteger.ONE);

		up = (int) (2 * Math.sqrt(tr) * l);
		
		System.out.println("r = " + r + " up = " + up);

		for(ai = 1; ai < up; ai++)
		{
			yai = new BigInteger("" + ai);
			lh = (mPower(x.subtract(yai), n, n)).mod(n);
			rh = (mPower(x, n, n).subtract(yai)).mod(n);

			if(lh.compareTo(rh) != 0) return false;
		}

		e = System.currentTimeMillis();
		
		time = e - s;

		return true;
	}
	
	public BigPolyPrimeInt()
	{
		Sieve();
	}

	public static void main(String args[])
	{
		String i, o;
		BigInteger si;

		BigPolyPrimeInt bp = new BigPolyPrimeInt();
		
		try{
			RandomAccessFile in = new RandomAccessFile("in.txt", "rw");
			RandomAccessFile out = new RandomAccessFile("out.txt", "rw");
			
			while( (i = in.readLine()) != null )
			{
				si = new BigInteger(i.trim());

				if( bp.isPrime(si) )
				{
					o = i + "\tis PRIME and it took " + bp.time + " mili seconds" + "\r\n";
					
					out.seek(out.length());
					out.writeBytes(o);
				}
				else
				{
				}
			}
		}
		catch(IOException ioe){
			System.out.println("Error Opening File : " + ioe);
		}
	}
}
