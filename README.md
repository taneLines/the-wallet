# the-wallet
Python's Markowitz Portfolio

## File mode

File mode is useful for academic purposes, when one wants to show how Markowitz portfolio is performing.
To correct performance of file mode, you should prepare your file in this way, where columns are separated with semicolons, 
first row is reserved for stock names and next rows are prices, days in ascending order (from oldest to newest), prices are
written with dot as a separator:

<code>
	stockname1;stockname2;stockname3;
	4.20;2.29;23.17
	4.32;2.48;23.19
	4.10;2.48;23.23
</code>

File mode can be turn on with -f,--file argument parsed while turning on the app, and giving file path as an argument:

<code>
	python3 main.py -f mystocks.txt
</code>