import pandas as pd
import time
from connection import send_request
from rx3.core.observer import Observer
from enum import IntEnum
import debugpy
from rx3 import operators as ops

'''
the following lines are for reference from the actual Web API and the PriceSeriesProvider
'''
class eBarStatus(IntEnum):
	Unknown = 0
	New = 1
	Real_Time = 2
	Historical = 4
	Standard_Close = 8
	End_Of_Session_Close = 16
	Ghost_Bar = pow(2, 28)
	End_Of_History_Stream = pow(2,29)

def is_bar_status(bar_status, mask):
	return (bar_status & mask) > 0


CHART_TYPES = {
		"BARS" : 0,#DataChartType.Bars;
		"VOLUME": 1 # DataChartType.Volume;
}	

INTERVAL_TYPES = {
	"TICKS" : 0, #DataIntervalType.Ticks;
	"MINUTES" : 1, #DataIntervalType.Minutes;
	"DAILY" : 2, #DataIntervalType.Daily;
	"WEEKLY" : 3, #DataIntervalType.Weekly;	
	"MONTHLY" : 4, #DataIntervalType.Monthly;
	"SECONDS" : 14 #DataIntervalType.Seconds;
}		

INTERVAL_RANGE_TYPES = {
		"BARS" : 0,
		"DATE" : 5,
		"DAYS" : 1,
		"MONTHS" : 3,
		"WEEKS" : 2,
		"YEARS" : 4
}		


_status_bitmap = {
	0: 'NEW',
	1: 'REAL_TIME_DATA',
	2: 'HISTORICAL_DATA',
	3: 'STANDARD_CLOSE',
	4: 'END_OF_SESSION_CLOSE',
	5: 'UPDATE_CORPACTION',
	6: 'UPDATE_CORRECTION',
	7: 'ANALYSIS_BAR',
	8: 'EXTENDED_BAR',
	19: 'PREV_DAY_CORRECTION',
	23: 'AFTER_MARKET_CORRECTION',
	24: 'PHANTOM_BAR',
	25: 'EMPTY_BAR',
	26: 'BACKFILL_DATA',
	27: 'ARCHIVE_DATA',
	28: 'GHOST_BAR',
	29: 'END_OF_HISTORY_STREAM'
}	

def _getBarStatusDescription(id):

	binary = "{:b}".format(id)
	description = ""

	for bit_idx, bit_val in enumerate(reversed(binary)):
		if bit_val == '1':
			description += "{} ".format(_status_bitmap[bit_idx])

	return description


'''
to be used to subscribe to the data observable (subject)
why not just a function subscription???
'''
class _Observer(Observer):
	def __init__(self, data_host):
		self.data_host = data_host


	def on_next(self, data):
		#debugpy.breakpoint()
		bar_status = data['Status'] 

		changed = False

		#if history
		if self.data_host.data is not None: 
			bn = data["BarNumber"]
			if bn % 1000 == 0:
				print(f'{data["BarNumber"]} {data["DateTime"]} {data["Open"]:.2f} {data["High"]:.2f} {data["Low"]:.2f} {data["Close"]:.2f}')
			if is_bar_status(bar_status, eBarStatus.Historical) and not is_bar_status(bar_status, eBarStatus.End_Of_History_Stream):
				if not is_bar_status(bar_status, eBarStatus.Ghost_Bar) and \
						(is_bar_status(bar_status, eBarStatus.Standard_Close) or is_bar_status(bar_status, eBarStatus.End_Of_Session_Close)) :
					self.data_host.data.append(data)
			else:
				#debugpy.breakpoint()	
				print(data["BarNumber"], "	end of history")	
				changed = True
				sdata = self.data_host.data[-1]
				if sdata["DateTime"] != data["DateTime"] and not is_bar_status(bar_status, eBarStatus.Ghost_Bar):
					self.data_host.data.append(data)
				self.data_host.df = pd.DataFrame(self.data_host.data)
				self.data_host.df["DateTime"] = pd.to_datetime(self.data_host.df["DateTime"])
				self.data_host.data = None

		if self.data_host.df is not None:
			#debugpy.breakpoint()
			df = self.data_host.df
			l = len(df)-1
			#print(data["BarNumber"], "	there is dataset ")
			sdata = df.iloc[l]
			stime = sdata["DateTime"]
			sclose = sdata["Close"]
			dtime = pd.to_datetime(data["DateTime"])
			close = data["Close"]
			if dtime>=stime:
				if stime == dtime:
					data["DateTime"] = dtime
					self.data_host.changed = self.data_host.changed or changed or sclose!=close
					colno = len(df.columns)
					if not is_bar_status(bar_status, eBarStatus.Ghost_Bar):
						for idx in range(colno):
							col = df.columns[idx]
							if col in data:
								df.iloc[l, idx] = data[col]
				else:
					print(f'{data["BarNumber"]} {data["DateTime"]} {data["Open"]:.2f} {data["High"]:.2f} {data["Low"]:.2f} {data["Close"]:.2f}')
					data["DateTime"] = dtime	
					self.changed = True	
					if not is_bar_status(bar_status, eBarStatus.Ghost_Bar):
						self.data_host.df = df.append(data, ignore_index = True)	

def _getDictionaryKey(symb, chart_type, interval_type, unit, range_type, range_value):
	res = f'{symb}_{chart_type}_{interval_type}_{unit}_{range_type}_{range_value}'
	return res 

#https://api.tradestation.com/v2/stream/barchart/{symbol}/{interval}/{unit}/{startDate}/{endDate}
#https://api.tradestation.com/v2/stream/barchart/{symbol}/{interval}/{unit}/{barsBack}/{lastDate}
#https://api.tradestation.com/v2/stream/barchart/{symbol}/{interval}/{unit}
#https://api.tradestation.com/v2/stream/tickbars/{symbol}/{interval}/{barsBack}

'''
the data host and broker
'''
class DataHost:
	def __init__(self, symbol, chart_type, interval_type, unit, range_type, range_value):
		self.changed = False
		self.data = []
		self.df = None
		
		key = _getDictionaryKey(symbol, chart_type, interval_type, unit, range_type, range_value)

		request_data = {
			'id': key, 
			'symbol': symbol, 
			'chart_type':chart_type, 
			'interval_type': interval_type, 
			'interval_value': unit, 
			'range_type' : range_type,
			'range_value' : range_value
		}

		self.request = request_data

		subject = send_request(request_data)

		obs = _Observer(self)

		subject.subscribe(obs)

		self.data_subject = subject

		#subject.subscribe(lambda x: print("Original subscriber value is {0}".format(x)))
		#subject.subscribe(lambda x: store(x))    