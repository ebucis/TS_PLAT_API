import finplot as fplt


'''
class to draw chart
'''
class Plotter():
	def __init__(self, data_host):
		self.plots = []
		self.data_host = data_host
		symbol = data_host.request['symbol'] 
		fplt.create_plot(f"{symbol}", init_zoom_periods=75, maximize=True)
		self.update_plot()
		def upd():
			try:
				if self.data_host.changed:
					self.update_plot()
					self.data_host.changed = False
			except Exception as ex:
				print(ex)

		fplt.timer_callback(upd, 0.1) # update in 10 Hz
		fplt.autoviewrestore()
		fplt.show()

	def update_plot(self):
		df = self.data_host.df
		if df is not None:
			candlesticks = df[["DateTime", "Open", "Close", "High", "Low"]]
			if not self.plots: # 1st time
				candlestick_plot = fplt.candlestick_ochl(candlesticks)
				self.plots.append(candlestick_plot)
				# use bitmex colors
				candlestick_plot.colors.update(dict(
						bull_shadow = '#388d53',
						bull_frame  = '#205536',
						bull_body   = '#52b370',
						bear_shadow = '#d56161',
						bear_frame  = '#5c1a10',
						bear_body   = '#e8704f'))
			else: # update
				if self.data_host.changed:
					self.plots[0].update_data(candlesticks)
