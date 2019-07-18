import java.io.*;
import java.awt.*;
import java.math.*;
import javax.swing.*;
import java.awt.event.*;

public class Fermat extends JFrame
{
	private long n;
	private JTextField tf, lt;
	private JButton bt;
	private Container c;
	
	public Fermat()
	{
		super("Fermat's Little Test");

		tf = new JTextField(20);

		lt = new JTextField(31);

		bt = new JButton("Test Primality");

		c = getContentPane();

		c.setLayout(new FlowLayout());

		lt.setEditable(false);

		bt.addActionListener(new ActionListener()
		{
			public void actionPerformed(ActionEvent e)
			{
				n = Long.parseLong(tf.getText());

				if( isPrime(n) ) lt.setText("The Number " + n + " is a prime");

				else lt.setText("The Number " + n + " is not Prime");
			}
		});
		
		c.add(tf);
		
		c.add(bt);
		
		c.add(lt);
		
		setSize(380, 100);
		
		setVisible(true);
	}
	
	long modPower(long a, long n, long b)
	{
		long m, p, z;
		
		m = n;
		p = 1;
		z = a;
		
		while( m > 0 )
		{
			while( m % 2 == 0 )
			{
				m = m / 2;
				z = (z*z) % b;
			}
			m--;
			p = (p * z) % b;
		}
		
		return p;
	}
	
	boolean isPrime(long n)
	{
		long a, k;
		
		for(a = 2; a < n; a++)
		{
			k = modPower(a, (n-1), n);
			
			if(k != 1) return false;
		}
		
		return true;
	}
	
	boolean isPrime(long n, long p)
	{
		long i, a, k;

		for(i = 2; i < p; i++)
		{
			a = (long) Math.random() * n;

			k = modPower(a, (n-1), n);

			if(k != 1) return false;
		}

		return true;
	}
	
	public static void main(String args[]){
		new Fermat();
	}
}