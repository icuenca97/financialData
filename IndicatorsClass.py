from GetDataClass import *

class Indicators(GetData):
	

	def dobleSMA(self, source=None, fast=5, slow=20, **kwargs):
		
		"""
		Lógica del script:
			Source por default es None. 
			1º pregunto si le pasé source (source != None), caso en el que pruebo aplicar la funcion de tal source. 
			Es importante que nombre de source == nombre del método en GetData.
			2º Si no, pregunto si el objeto ya tiene el atributo source. Esto me indicaría que previamte ejecuté método de GetData, 
			o sea que ya cuento con un df con columnas básicas. En tal caso, data será igual al data que ya trae aparejado el objeto.
			3º Si no se especifiqué source a la cual acudir, ni el objeto trae consigo un df, me lo hace saber.
		"""
				
		if source:
			try:
				data = getattr(self, source)().copy()
			except Exception as e:
				print('Ocurrió el siguiente error: ', e)
				print("Invalid source. Please try: 'yfinance', 'alphavantage', 'TDAmeritrade'.")
		
		elif hasattr(self, 'source'):
			#data = getattr(self, self.source)()
			data = self.data.copy()

		else:
			print("Neither source specified, nor previous dataframe with price history found. Please specify source or assign data attribute.")

		try:
			data['sma_fast'] = data.close.rolling(fast).mean()
			data['sma_slow'] = data.close.rolling(slow).mean()
			data.dropna(inplace=True)

		except:
			data = pd.DataFrame()

		self.data_dobleSMA = data
		
		return data #Retorna el data con las sma, no el base. Acá el base es self.data, pero a data ya le agregué las sma

	
	def tripleEMA(self, source=None, ema_fast=4, ema_medium=9, ema_slow=18, **kwargs):
		
		if source:
			try:
				data = getattr(self, source)().copy()
			except Exception as e:
				print('Ocurrió el siguiente error: ', e)
				print("Invalid source. Please try: 'yfinance', 'alphavantage', 'TDAmeritrade.")
		
		elif hasattr(self, 'source'):
			#data = getattr(self, self.source)()
			data = self.data.copy()

		else:
			print("Neither source specified, nor previous dataframe with price history found. Please specify source or assign data attribute.")
			
		try:
			data['ema_fast'] = data.close.ewm(span = ema_fast).mean()
			data['ema_medium'] = data.close.ewm(span = ema_medium).mean()
			data['ema_slow'] = data.close.ewm(span = ema_slow).mean()
			data.dropna(inplace=True)
			data = data.iloc[ema_slow:].copy() #Con ewm, las 1ras slow filas no quedan NaN, sino q promedia las q tenga hasta entonces. Elimino manual

		except:
			data = pd.DataFrame()

		self.data_tripleEMA = data
		
		return data

	def ATR(self, ma='rma', period=14, source=None, **kwargs):

		if source:
			try:
				data = getattr(self, source)().copy()
			except Exception as e:
				print('Ocurrió el siguiente error: ', e)
				print("Invalid source. Please try: 'yfinance', 'alphavantage', 'TDAmeritrade.")
		
		elif hasattr(self, 'source'):
			#data = getattr(self, self.source)()
			data = self.data.copy()

		else:
			print("Neither source specified, nor previous dataframe with price history found. Please specify source or assign data attribute.")

		x = data.high - data.low
		y = abs(data.high - data.shift().close)
		z = abs(data.low - data.shift().close)

		tr = pd.DataFrame([x,y,z]).max()

		if ma == 'ema':
			data['ATR'] = tr.ewm(span=period).mean()
		elif ma == 'rma': #Por default uso esta pq es la que usa TradingView
			data['ATR'] = tr.ewm(alpha=1 / period).mean()
		elif ma == 'sma':
			data['ATR'] = tr.rolling(period).mean()
		else:
			print('Wrong moving average kind introduced. Try "ema", "rma", "sma".')

		self.data_ATR = data
		self.atr = data['ATR']

		return data


	def ADXDMI(self, ma='rma', period=14, source=None, **kwargs):

		data = self.ATR(ma=ma, period=period, source=source).copy()

		
		moveUp = data.high - data.shift().high
		moveDown = data.shift().low - data.low

		pdm = pd.Series((np.where(((moveUp > 0) & (moveUp > moveDown)), moveUp, 0)), index = data.index)
		ndm = pd.Series((np.where(((moveDown > 0) & (moveDown > moveUp)), moveDown, 0)), index = data.index)
		
		if ma == 'ema':
			data['PDI'] = (pdm.ewm(span=period).mean() / data['ATR']) * 100
			data['NDI'] = (ndm.ewm(span=period).mean() / data['ATR']) * 100
		elif ma == 'rma':
			data['PDI'] = (pdm.ewm(alpha=1 / period).mean() / data['ATR']) * 100
			data['NDI'] = (ndm.ewm(alpha=1 / period).mean() / data['ATR']) * 100
		elif ma == 'sma':
			data['PDI'] = (pdm.rolling(period).mean() / data['ATR']) * 100
			data['NDI'] = (ndm.rolling(period).mean() / data['ATR']) * 100

		dx = (abs(data['PDI'] - data['NDI']) / (data['PDI'] + data['NDI'])) * 100
		data['ADX'] = dx.rolling(period).mean()

		data.dropna(inplace=True)
		
		self.data_ADXDMI = data
		self.pdi = data['PDI']
		self.ndi = data['NDI']
		self.adx = data['ADX']

		return data


	def ADXsma(self, period=14, ma='rma', source=None, fast=5, slow=20, **kwargs):

		data = self.ADXDMI(period=period, ma=ma, source=source).copy()

		data['sma_fast'] = data.close.rolling(fast).mean()
		data['sma_slow'] = data.close.rolling(slow).mean()
		data.dropna(inplace=True)

		self.data_ADXsma = data

		return data


	def aroon(self, source, timeframe, **kwargs):
		
		if source:
			try:
				data = getattr(self, source)().copy()
			except Exception as e:
				print('Ocurrió el siguiente error: ', e)
				print("Invalid source. Please try: 'yfinance', 'alphavantage', 'TDAmeritrade'.")
		
		elif hasattr(self, 'source'):
			data = self.data.copy()

		else:
			print("Neither source specified, nor previous dataframe with price history found. Please specify source or assign data attribute.")

		x = timeframe
		aroonUp = []
		aroonDown = []
		aroonDate = []

		while x < len(data):
			aroon_up = ((data.high[x-timeframe:x].to_list().index(max(data.high[x-timeframe:x]))) / timeframe) * 100
			aroon_down = ((data.low[x-timeframe:x].to_list().index(min(data.low[x-timeframe:x]))) / timeframe) * 100

			aroonUp.append(aroon_up)
			aroonDown.append(aroon_down)
			aroonDate.append(data.index[x])

			x += 1
		
		self.aroonUp = aroonUp
		self.aroonDown = aroonDown
		self.dates = aroonDate

		return data