from datetime import datetime as dtdt
from datetime import timedelta
import inspect
import math
import  matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
import requests
import yfinance as yf


pd.options.display.precision = 2
pd.options.display.float_format = '{:,.2f}'.format
#Tip: en la fila de arriba, puedo poner un $ o % adelante/atrás de las {} y no deja de ser un float, pero te lo muestra como $ o %

class GetData:

	apikeyAV = 'UEE3SBFTYJR21T8E'
	apikeyTD = 'HPHFW7WEKPGMB1IF9VQMHTFQKSKJO0AI'
	apikeyAM = 'PKRRTJJ0ZEPCZPGHGXE4'
	secretkeyAM = '5aecoQkbv8o82Dn54wW9oqIXIORHr7kR5hxOd7m1'
	intra = ['1min', '5min', '15min', '30min', '60min']
	open_hour = '09:30:00'
	close_hour = '16:00:00'

	def __init__(self, ticker, interval='daily', start=None, end=None, auto_adjust=True, size='full', extended_hours=False):
		
		"""
		Input:
			ticker   (str): Ticker del activo a analizar
			interval (str): Compresión temporal. 
				accepted input: '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'month', 'year', 'ytd'
			start    (str): Fecha de inicio para recolectar datos. Default: None
				formato de input: 'yyyy-mm-dd'
			end      (str): Ultima fecha sobre la cual recolectar datos. Default: None. En gral las API te traen hasta ult día de trading
				formato de input: 'yyyy-mm-dd'
			auto_adjust (bool): Traer valores ajustados por dividendos y splits o no. Default: True
			size     (str): Para API de alphavantage. No cuenta con fechas de start y end. Este parametro determina si traer hist completa o light
				accepted input: 'full', 'compact'
			extended_hours (bool): Traer valores de pre y after market o no. Default: False
		"""

		self.ticker = ticker.upper()
		self.interval = interval
		self.start = start
		self.end = end
		self.auto_adjust = auto_adjust
		self.size = size
		self.extended_hours = extended_hours
        
	def SP500Tickers():
		sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
		sp500_tickers = list(sp500.Symbol)
		sp500_tickers = [e for e in sp500_tickers if e not in ('BRK.B','BF.B')]

		with open('sp500tickers.pickle', 'wb') as f:
			pickle.dump(sp500_tickers, f)
		return sp500_tickers

	"""
	Para levantar el pickle de los tickers del sp500:
	with open('sp500tickers.pickle', 'rb') as f:
		tickers = pickle.load(f)
	
	"""

	def yfinance(self, start = None, end = None, interval = None, auto_adjust=None):
		
		"""
		Input: start, end, interval & auto_adjust son parametros cargados al inicializar el objeto. Si
		deseo cambiarlos, paso valor deseado, y queda como el valor del atributo del objeto.
		
		Output: Dataframe con cols: 'open, high, low, close, volume, vol_mln_usd, pct_change, log_change',
		desde la fecha start hasta la fecha end, end timeframe dado por interval, ajustados o no.
		"""


		self.source = 'yfinance'
		self.start = start if start else self.start
		self.end = end if end else self.end
		self.interval = interval if interval else self.interval


		if self.end:
			try:
				end = dtdt.strptime(self.end, '%Y-%m-%d')
			except:
				print('Error: Invalid format for end date. Try yyyy-mm-dd')
		else:
			end = dtdt.now()

		if self.start:
			try:
				start = dtdt.strptime(self.start, '%Y-%m-%d')
			except:
				print('Error: Invalid format for start date. Try YYYY-mm-dd')
		else:
			start = None

		if self.interval in self.intra:
			interval = self.interval[:-2] # yfinance me pide 'm', no 'min', entonces le borro los ult dos caracteres ('in')

			if interval == '1m':
				date_range_limit = 7
			elif interval == '60m':
				date_range_limit = 730
			else:
				date_range_limit = 60

			if (not self.start) or ((end - start).days >= date_range_limit):
				print('''Error: intraday data available for a range within the last 730 days (60 min) /  
						60 days (30, 15 and 5 min) / 7 days (1 min).''')

		elif self.interval == 'daily':
			interval = '1d'		
		elif self.interval == 'weekly':
			interval = '1wk'
		
		try:
			data = yf.download(self.ticker, interval=interval, start=start,
		                       end=end, auto_adjust=self.auto_adjust, progress=False)
			if not self.auto_adjust:
				data.drop('Adj Close', axis=1, inplace=True)#Si no pido adjclose,yahoo me lo trae separado del close, pero si no lo pedí lo borro

			data['vol_mln'] = data.Volume * data.Close / 10**6
			data['pct_change'] = data.Close.pct_change() * 100
			data['log_change'] = np.log(data.Close / data.Close.shift()) * 100
			data.columns = ['open', 'high', 'low', 'close', 'volume', 'vol_mln_usd', 'pct_change', 'log_change']

		except Exception as e:
			print('Ocurrió el siguiente error: ', e)
			data = pd.DataFrame()

		self.data = data
		self.hodl = ((data.close[-1] / data.close[0]) - 1) * 100
		
		return data

	def alphavantage(self, interval = None, size = None, extended_hours = None, auto_adjust = None):

		"""
		Input: Interval, size, extended_hours & auto_adjust son parametros cargados al inicializar el objeto. Si
		deseo cambiarlos, paso valor deseado, y queda como el valor del atributo del objeto.

		Output: Output: Dataframe con cols: 'open, high, low, close, volume, vol_mln_usd, pct_change, log_change',
		desde la fecha start hasta la fecha end, end timeframe dado por interval, ajustados o no, con extended_hours o no.

		"""
		
		self.source = 'alphavantage'
		self.interval = interval if interval else self.interval
		self.size = size if size else self.size
		self.extended_hours = extended_hours if extended_hours else self.extended_hours
		self.auto_adjust = auto_adjust if auto_adjust else self.auto_adjust
		
		url = 'https://www.alphavantage.co/query'
		#AV me pide un str 'true' o 'false', no un bool. Transformo el bool en str
		adjusted = str(self.auto_adjust).lower() 

		if self.interval in self.intra:
			function = 'TIME_SERIES_INTRADAY'
			parametros = {'function': function, 'symbol': self.ticker, 'interval': self.interval, 
			'adjusted': adjusted, 'outputsize': self.size, 'apikey': self.apikeyAV}
		
		elif (self.interval == 'daily') or (self.interval == 'weekly'):
			if self.auto_adjust:
				function = f'TIME_SERIES_{self.interval.upper()}_ADJUSTED'
			else:
				function = f'TIME_SERIES_{self.interval.upper()}'
				
			parametros = {'function': function, 'symbol': self.ticker, 'outputsize': self.size, 'apikey': self.apikeyAV}

		else:
			print("Invalid interval. Try: '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly'.")

		try:
			r = requests.get(url, params = parametros)
			
			if self.interval in self.intra:
				data = r.json()[f"Time Series ({self.interval})"]
			elif self.interval == 'daily':
				data = r.json()["Time Series (Daily)"]
			elif self.interval == 'weekly':
				data = r.json()["Weekly Adjusted Time Series"]

			data = pd.DataFrame.from_dict(data, orient = 'index')
			indice = 'Datetime' if self.interval in self.intra else 'Date'
			data.index.name = indice
			
			for col in data.columns:
				data[col] = pd.to_numeric(data[col], errors='coerce')
				flotante = data[col] % 1 != 0
				if flotante.any():
					data[col] = data[col].astype('float')
				else:
					data[col] = data[col].astype('int')

			if self.interval not in self.intra:
				if self.auto_adjust:
					if self.interval == 'daily':
						data.drop(['7. dividend amount', '8. split coefficient'], axis=1, inplace=True)
					elif self.interval == 'weekly':
						data.drop(['7. dividend amount'], axis=1, inplace=True)

					data['factor'] = data['5. adjusted close'] / data['4. close']
					cols = [data['1. open'] * data.factor, data['2. high'] * data.factor, data['3. low'] * data.factor,
					        data['5. adjusted close'], data['6. volume']]
					data = pd.concat(cols, axis=1)
		
			data.index = pd.to_datetime(data.index)
			data = data.sort_values(indice, ascending=True)
			data.columns = ['open', 'high', 'low', 'close','volume']

			data['vol_mln_usd'] = (data.close * data.volume) / 10**6
			data['pct_change'] = data.close.pct_change() * 100
			data['log_change'] = np.log(data.close / data.close.shift()) * 100

			if (self.interval in self.intra) and not self.extended_hours:
				data = data.between_time(self.open_hour, self.close_hour) #AV tiene data desde 04:00 hasta 20:00. Acá filtro a horario de mercado

		except Exception as e:
			print('Ocurrió el siguiente error: ', e)
			data = pd.DataFrame()

		self.data = data
		self.hodl = ((data.close[-1] / data.close[0]) - 1) * 100

		return data


	def TDAmeritrade(self, start = None, end = None, interval = None, extended_hours = None,
	periodType=None, period=None, frequencyType=None):

		"""
		Input:
			periodType  (str): Tipo de periodo a mostrar. En caso de tener valores de start y endDate, queda sin uso. Default: 'day'
				accepted values: 'day', 'month', 'year', 'ytd'
			period      (str): Cantidad de periodos a mostrar. En caso de tener valores de start y endDate, queda sin uso.
				accepted values: Depende del periodType. day(1,2,3,4,5,10*); month(1*,2,3,6), year(1*,2,3,5,10,15,20); ytd(1*)
			frequencyType (str): Compresion de las velas.
				accepted values: Depende del periodType. day(minute); month(daily, weekly); year(daily, weekly, monthly); ytd(daily, weekly)
			frequency: Not a parameter itself. Its the amount of *frequencyType* in each candle. Default: 1. Solo en caso de periodType=day
			y frequencyType=minute hay otras opciones (1,5,10,15,30)
		"""

		self.source = 'TDAmeritrade'
		self.start = start if start else self.start
		self.end = end if end else self.end
		self.interval = interval if interval else self.interval
		self.extended_hours = extended_hours if extended_hours else self.extended_hours

		url = f'https://api.tdameritrade.com/v1/marketdata/{self.ticker}/pricehistory'
		
		extended_hours = str(self.extended_hours).lower()

		if self.interval in self.intra:
			frequency = self.interval[:-3]
			if self.interval == '60min':
				frequency = '30' #TDA no tiene compresion horaria. P q no tire error, le paso 30min y despues resampleo a 1h
			periodType = 'day'
			frequencyType = 'minute'
		else:
			frequency = 1 #Cuando no intra, la freq solo puede ser 1 (1día, 1sem, 1mes)
			if not periodType:
				periodType = 'year' #Cuando no intra, por default le mando year.
			if self.interval == 'month':
				frequencyType = 'monthly'
			else:
				frequencyType = self.interval

		if self.start:
			try:
				start = int(dtdt.strptime(self.start, '%Y-%m-%d').timestamp() * 1000) #Pongo int() pq sino queda en float. Y el epoch es un entero
			except:
				print('Invalid input for start date. Try again with format "yyyy-mm-dd".')

			try:
				end = int(dtdt.strptime(self.end, '%Y-%m-%d').timestamp() * 1000)
			except:
				end = int(dtdt.now().timestamp() * 1000) #Si tengo startDate, por default asumo q necesito un endDate. Si no paso parametro, ayer

			parametros = {'apikey': self.apikeyTD, 'periodType':periodType, 'frequencyType':frequencyType, 
			'frequency':frequency, 'endDate':end, 'startDate':start, 'needExtendedHoursData':extended_hours}

		else:
			parametros = {'apikey': self.apikeyTD, 'periodType':periodType, 'period':period,
			'frequency':frequency, 'frequencyType':frequencyType, 'needExtendedHoursData':extended_hours}

		try:
			r = requests.get(url, params = parametros)
			data = r.json()['candles']
			data = pd.DataFrame(data)
			data['fecha'] = pd.to_datetime(data['datetime'] - 3600*1000*3, unit='ms')
			if self.interval in self.intra:
				data.index = data['fecha']
				data.index.name = 'Datetime'
			else:
				data.index = data['fecha']
				data.index = data.index.date
				data.index.name = 'Date'

			data.drop(['datetime','fecha'], axis=1,inplace=True)
			data = data.loc[data.index[0]+timedelta(days=1):]
			
			if self.interval == '60min':
				data = data.resample('1H').first() #Consejo: No usar esta compresion. 

			data['vol_mln_usd'] = (data.close * data.volume) / 10**6
			data['pct_change'] = data.close.pct_change() * 100
			data['log_change'] = np.log(data.close / data.close.shift()) * 100
		
		except Exception as e:
			print('Ocurrió el siguiente error: ', e)
			data = pd.DataFrame()

		self.data = data
		self.hodl = ((data.close[-1] / data.close[0]) - 1) * 100

		return data

	def fundamentals(self):

		self.source = 'TDAmeritrade'
		url = 'https://api.tdameritrade.com/v1/instruments'
		parametros = {'apikey': self.apikeyTD, 'symbol': self.ticker, 'projection':'fundamental'}

		r = requests.get(url = url, params = parametros)

		self.fundamentals = r.json()[self.ticker]['fundamental']
		
		return self.fundamentals


	def options(self):

		url = 'https://api.tdameritrade.com/v1/marketdata/chains'
		parametros = {'apikey': self.apikeyTD, 'symbol': self.ticker}

		r = requests.get(url=url, params=parametros).json()

		v_calls = list(r['callExpDateMap'].values())
		v_calls_fechas = list(r['callExpDateMap'].keys())
		v_puts = list(r['putExpDateMap'].values())
		v_puts_fechas = list(r['putExpDateMap'].keys())

		calls = []
		for i in range(len(v_calls)):
			v = list(v_calls[i].values())    
			for j in range(len(v)):
				calls.append(v[j][0])

		puts = []
		for i in range(len(v_puts)):
			v = list(v_puts[i].values())    
			for j in range(len(v)):
				puts.append(v[j][0])

		contracts = pd.concat([pd.DataFrame(calls),pd.DataFrame(puts)])

		tabla = contracts.loc[contracts.daysToExpiration > 0]

		tabla = tabla.loc[:,['strikePrice', 'daysToExpiration', 'putCall', 'bid', 'ask',
		'last', 'volatility', 'openInterest', 'theoreticalOptionValue']]

		tabla.columns = ['Strike', 'Dias', 'Tipo', 'Bid', 'Ask', 'Ultimo', 'VI', 'OpenInt', 'PrimaT']

		self.options = tabla

		return tabla

	def alpaca(self):

		self.source = 'alpaca'

		url = f'https://data.alpaca.markets/v2/stocks/{self.ticker}/bars'

		if self.interval in self.intra:
			if self.interval == '60min':
				interval = '1Hour'
			else:
				interval = '1Min'#Es la unica compresion en minutos que me acepta. Desp resampleo a 5,15,30 si es necesario

		elif self.interval == 'daily':
			interval = '1Day'

		if self.start:
			start = self.start +'T00:00:00-03:00'
			
			if self.end:
				end = self.end +'T00:00:00-03:00'
			else:
				end = dtdt.today().strftime('%Y-%m-%d') +'T00:00:00-03:00'
		else:
			print('Error. Start y end no encontrados o formato inválido. Try again.')
		
		parametros = {'start':start, 'end':end, 'limit':10000, 'timeframe':interval}

		headers = {'APCA-API-KEY-ID':self.apikeyAM, 'APCA-API-SECRET-KEY':self.secretkeyAM}

		r = requests.get(url = url, headers = headers, params = parametros)
		js = r.json()
		data = pd.DataFrame(js['bars'])
		data.t = pd.to_datetime(data.t).apply(lambda x: dtdt(x.year,x.month,x.day,x.hour,x.minute,x.second))
		data.set_index('t', inplace=True)
		
		data.index.name = 'Datetime' 
		
		if self.interval not in self.intra:
			data.index = data.index.date
			data.index.name = 'Date'
		
		if (self.interval in self.intra) and (self.interval != '60min'): #Consejo: No usar 5, 15 y 30 min. Hice un cuasimodo.
		#Lo correcto sería resamplear volumen con .sum(). Es más lío que el beneficio que reporta. Dejo esto como parche básico.
			data = data.resample(self.interval.replace('m','M')).last()
			data.fillna(method='ffill', inplace=True) #Acciones ilíquidas -Argy- dejan huecos de op con NaN. Que asuma valor d ult quote

		data.columns = ['open', 'high', 'low', 'close', 'volume']

		data['vol_mln_usd'] = (data.close * data.volume) / 10**6
		data['pct_change'] = data.close.pct_change() * 100
		data['log_change'] = np.log(data.close / data.close.shift()) * 100

		self.data = data

		return data