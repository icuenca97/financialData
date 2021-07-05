from IndicatorsClass import *

class Strategies(Indicators):

	def smaCrossover(self, source = None, fast = 5, slow = 20, **kwargs):

		data = self.dobleSMA(source = source, fast = fast, slow = slow).copy()

		cruce = (data['sma_fast'] / data['sma_slow'] - 1) * 100
		compra = cruce > 0
		data['signal'] = np.where(compra, 'Compra', 'Venta')
		data['buyHold'] = ((data.close.pct_change() + 1).cumprod() - 1) * 100

		self.data_smaCrossover = data
		self.strategy = 'smaCrossover'
		self.signal = data['signal'].tolist()
		self.pctChange = data['pct_change'].to_list()

		return data


	def emaTripleCrossover(self, source = None, ema_fast = 4, ema_medium = 9, ema_slow = 18, **kwargs):

		data = self.tripleEMA(source = source, fast = ema_fast, medium = ema_medium, slow = ema_slow).copy()

		compra = (data['ema_fast'] > data['ema_medium']) & ((data['ema_fast'] > data['ema_slow']))
		venta = ~ compra
		#Signal: Si está la fast arriba, compra. Si no está, m fijo q ayer tpco -doy un día de handicap-. Si ayer no estuvo, venta
		data['signal'] = np.where(compra, 'Compra', np.where(venta & venta.shift(), 'Venta', 'Compra'))
		data['buyHold'] = ((data.close.pct_change() + 1).cumprod() - 1) * 100

		self.data_emaTripleCrossover = data
		self.strategy = 'emaTripleCrossover'
		self.signal = data['signal'].tolist()
		self.pctChange = data['pct_change'].to_list()

		return data


	def ADXDMIStrat(self, ma='rma', period=14, source=None, **kwargs):

		data = self.ADXDMI(ma=ma, period=period, source=source).copy()

		dif_DI = data['PDI'] - data['NDI']
		#Idea: Compra cuando +DI cruza parriba a -DI, y a la fecha siguiente +DI sigue al alza y -DI a la baja (la dif_DI se agranda)
		compra = (dif_DI.shift(2) < 0) & (dif_DI.shift() > 0)  & (dif_DI > dif_DI.shift())
		#Para la venta soy mas conserva: Vendo ni bien cruza +DI para abajo a -DI
		venta = (dif_DI < 0) & (dif_DI.shift() > 0)

		data['signal'] = np.where(compra, 'Compra', np.where(venta, 'Venta', 'Sin señal'))
		#Lo planteo asi pq si pongo np.nan en np.where, me devuelve un str 'nan', no NaN
		data['signal'].replace('Sin señal', np.nan, inplace=True) 
		#Le pongo el valor al 1º row a mano p que el ffill tenga punto d arranque antes de la 1º señal original
		data['signal'][0] = 'Compra' if (dif_DI[0] > 0) else 'Venta'
		data['signal'] = data['signal'].ffill()
		data['buyHold'] = ((data.close.pct_change() + 1).cumprod() - 1) * 100

		self.data_ADXDMIStrat = data
		self.strategy = 'ADXDMIStrat'
		self.signal = data['signal'].tolist()
		self.pctChange = data['pct_change'].to_list()

		return data


	def ADXsmaCrossover(self, period=14, ma='rma', source=None, fast=5, slow=20, tend_fuerte=25, **kwargs):

		data = self.ADXsma(period=period, ma=ma ,source=source, fast=fast, slow=slow).copy()

		cruce = (data['sma_fast'] / data['sma_slow'] - 1) * 100
		cruce_pos = cruce > 0
		tendencia = data['ADX'] >= tend_fuerte
		compra = (cruce_pos & tendencia)

		data['signal'] = np.where(((compra) &  (compra.shift() == False)), 'Compra', 
			np.where(((cruce < 0) & (cruce.shift() > 0)), 'Venta', 'Sin señal'))
		data['signal'].replace('Sin señal', np.nan, inplace=True) 
		data['signal'][0] = 'Compra' if (compra[0] > 0) else 'Venta'
		data['signal'] = data['signal'].ffill()
		data['buyHold'] = ((data.close.pct_change() + 1).cumprod() - 1) * 100

		self.data_ADXsmaCrossover = data
		self.strategy = 'ADXsmaCrossover'
		self.signal = data['signal'].tolist()
		self.pctChange = data['pct_change'].to_list()

		return data