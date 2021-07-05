from StrategiesClass import *

class Yields(Strategies):

	def eventDriven(self, strategy=None, source=None, fast=5, slow=20, ema_fast=4, ema_medium=9, ema_slow=18,
					ma='rma', period=14, tend_fuerte=25):

		params = {'strategy':strategy, 'source': source, 'fast': fast, 'slow': slow, 'ema_fast': ema_fast, 
		'ema_medium': ema_medium, 'ema_slow': ema_slow, 'ma': ma, 'period': period, 'tend_fuerte': tend_fuerte}
		
		if source:
			if strategy:
				try:
					data = getattr(self, strategy)(**params).copy()
				except Exception as e:
					print('Ocurrió el siguiente error: ', e)
					print("Invalid source or strategy.")
			else:
				print('Please introduce a strategy. Try: "smaCrossover", "emaTripleCrossover", "ADXDMIStrat", "ADXsmaCrossover"')
		
		elif hasattr(self, 'source'):
			params['source'] = self.source
			if strategy:
				try:
					data = getattr(self, strategy)(**params).copy()
				except Exception as e:
					print('Ocurrió el siguiente error: ', e)
					print('Invalid strategy. Try: "smaCrossover", "emaTripleCrossover", "ADXDMIStrat", "ADXsmaCrossover"')
			elif hasattr(self, 'strategy'):
				data = getattr(self, f'data_{self.strategy}')#(**params).copy()
			else:
				print('Please introduce a strategy. Try: "smaCrossover", "emaTripleCrossover", "ADXDMIStrat", "ADXsmaCrossover"')
		else:
			print("Please introduce a source. Try: 'yfinance', 'alphavantage', 'TDAmeritrade.")
			
		try:
			señal = self.signal
			pct_changes = self.pctChange
			self.estado_actual = 'Afuera' #Por default, interpreto que la señal actual del mercado es 'Afuera'
			
			total = len(señal)
			i = 1
			results = [0]

			while i < total:

				if señal[i-1] == 'Compra':

					j = i
					while  j < total:
						results.append(pct_changes[j])            
						j +=1

						if señal[j-1]=='Venta':
							i = j
							break
						if j == total:
							i = j
							self.estado_actual = 'Comprado' #Si la ult fecha la señal es compra, el estado de la strat es 'Comprado'
							break
				else:
					results.append(0)
					i +=1

			result = pd.concat([data,pd.Series(data=results, index=data.index)], axis=1)
			result.columns.values[-1] = "strategy"
			result['strategy_acum'] = ((result['strategy'] / 100 + 1).cumprod() - 1) * 100
			strat_performance = result['strategy_acum']
			buyHold = result['buyHold']

			self.result = result
			self.strat_performance = strat_performance
			self.buyHold = buyHold

		except Exception as e:
			print('Ocurrió el siguiente error: ', e)
			result = pd.DataFrame()

		return result


	def getTrades(self):
		
		data = getattr(self, f'data_{self.strategy}')
		actions = data.loc[data.signal != 'Sin señal'].copy()
		actions['signal'] = np.where(actions.signal != actions.signal.shift(), actions.signal, 'Sin señal')
		actions = actions.loc[actions.signal != 'Sin señal'].copy()


		# Si la 1º operación es venta, la elimino (es strat long). Si ult operación es compra, la elimino(así no quedan compras abiertas)
		if len(actions) >= 2: 
			if actions.iloc[0].loc['signal'] == 'Venta':
				actions = actions.iloc[1:]
			if actions.iloc[-1].loc['signal'] == 'Compra':
				actions = actions.iloc[:-1]
		else:
			actions = None

		try:
			pares = actions.iloc[::2].loc[:,['close']].reset_index()
			impares = actions.iloc[1::2].loc[:,['close']].reset_index()
			trades = pd.concat([pares, impares], axis=1)

			trades.columns = ['fecha_compra','px_compra','fecha_venta','px_venta']
			trades['rendimiento'] = (trades.px_venta / trades.px_compra - 1) * 100
			trades['days'] = (trades.fecha_venta - trades.fecha_compra).dt.days

			if len(trades):
				trades['resultado'] = np.where(trades['rendimiento'] > 0 , 'Ganador' , 'Perdedor')
				trades['rendAcum'] = (((trades['rendimiento'] / 100 + 1).cumprod()) - 1) * 100

		except Exception as e:
			print('Ocurrió el siguiente error: ', e)
			trades = []

		buyHold = actions.loc[trades['fecha_venta']]['buyHold'].reset_index(drop=True)
		trades['buyHold'] = buyHold

		self.trades = trades

		return trades


	def resumen(self):

		trades = self.trades
		
		if len(trades):
			resultado = float(trades.iloc[-1:]['rendAcum']) #rendAcum en .iloc[-1] --> rendAcum luego del ult trade --> rend definitivo
			agg_cantidades = trades.groupby('resultado').size() #Cantidad de trades ganadores y perdedores
			agg_rendimientos = trades.groupby('resultado').mean()['rendimiento'] #Rend promedio de trades ganadores y perdedores
			agg_tiempos = trades.groupby('resultado').sum()['days'] #Días totales comprado en trades ganadores y perdedores
			agg_tiempos_medio = trades.groupby('resultado').mean()['days'] #Duración promedio de trades ganadores y perdedores

			r = pd.concat([agg_cantidades,agg_rendimientos, agg_tiempos, agg_tiempos_medio ], axis=1)
			r.columns = ['Cantidad', 'Rend x Trade', 'Dias Total', 'Dias x Trade']
			resumen = r.T

			try:
			    t_win = r['Dias Total']['Ganador'] 
			except:
			    t_win = 0
			    
			try:
			    t_loss = r['Dias Total']['Perdedor']
			except:
			    t_loss = 0

			t = t_win + t_loss
			tea = ((resultado/100+1)**(365/t)-1) * 100 if (t>0 and resultado > 0) else 0

			metricas = {'rendimiento':round(resultado,2), 'dias_in':round(t,4), 'TEA':round(tea,2)}
		
		else:
			resumen = pd.DataFrame()
			metricas = {'rendimiento':0, 'dias_in':0, 'TEA':0}

		self.resumen = resumen
		self.metricas = metricas

		return resumen, '\n\n', metricas