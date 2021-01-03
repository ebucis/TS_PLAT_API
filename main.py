from plotter import Plotter
from datahost import DataHost
import time


if __name__ == "__main__":
	dh = DataHost('BTCUSD', "BARS", "MINUTES", 1, "BARS", 1000)

	#we wait for history to be deployed...
	# TODO: create a more elegant way	
	while dh.data is not None:
		print(f'receiving data....({len(dh.data)})')	
		time.sleep(2)

	#once history has been loaded, create chart
	plotter = Plotter(dh)

	#finplot blocks the main thread...no need to wait
	