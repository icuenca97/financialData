from ResultsClass import *

class Graph(Yields):

	def rendAcum(self):

		#plt.style.use('ggplot')
		fig, ax = plt.subplots(figsize=(15,7))

		ax.plot(self.strat_performance, lw=1, color='tab:red', label='Strategy')
		ax.plot(self.buyHold, lw=1, color='tab:blue', label='Buy & Hold')

		if hasattr(self, 'benchmark'):
			ax.plot(self.benchmark, lw=1, ls='--', label='Benchmark')
			ax.set_title(f'{self.strategy} performance vs Buy & Hold vs {self.benchmark} - {self.ticker} - Since {self.start}', size=16)
		
		else:
			ax.set_title(f'{self.strategy} performance vs Buy & Hold - {self.ticker} - Since {self.start}', size=16)
		
		ax.grid(alpha = .4)
		ax.legend(loc= 'upper left', fontsize=12)
		ax.set_ylabel("Performance in %")
		fig.tight_layout()

		plt.show()

		self.rendAcum = fig

		return fig

	def rendAnual(self):
		
		plt.style.use('ggplot')
		fig, ax = plt.subplots(figsize=(15,7))

		width = 0.4
		years = list(np.unique(self.strat_performance.index.to_series().apply(lambda x: x.year)))
		x_index = np.arange(len(years))
		
		yearly_strategy =  list(
			((self.result.strategy / 100 + 1).groupby(self.result.strategy.index.to_series().apply(lambda x: x.year)).prod() - 1) * 100)
		yearly_buyHold = list(((self.data.close).groupby(self.data.index.to_series().apply(lambda x: x.year)).last() / 
			(self.data.close).groupby(self.data.index.to_series().apply(lambda x: x.year)).first() - 1) * 100)
		
		if hasattr(self, 'benchmark'):
			width = 0.3
			yearly_benchmark = list(((self.benchmark / 100 + 1).groupby(self.benchmark.index.to_series().apply(lambda x: x.year)).prod() - 1) * 100)
			ax.bar(x_index - width, yearly_strategy, width = width, label='Strategy')
			ax.bar(x_index, yearly_buyHold, width = width, label='Buy & Hold')
			ax.bar(x_index + width, yearly_benchmark, width = width, label='Benchmark')
		
		else:
			ax.bar(x_index - width/2, yearly_strategy, width = width, label='Strategy')
			ax.bar(x_index + width/2, yearly_buyHold, width = width, label='Buy & Hold')
	
		ax.legend()
		ax.set_xticks(x_index)
		ax.set_xticklabels(years)
		plt.show()

		self.rendAnual = fig

		return fig


	def compareAssets(lista, strategy, start):

		dic = {}

		plt.style.use('ggplot')

		if len(lista) <= 10:
			fig, ax = plt.subplots(figsize=(20,5*len(lista)), nrows=math.ceil(len(lista)/2), ncols=2)

			for i in range(len(lista)):
				print(f'Analizando... Ticker {i+1} de {len(lista)}', end='\r')
				dic[lista[i]] = Graph(f'{lista[i]}', start='2015-01-01')
				dic[lista[i]].yfinance()
				getattr(dic[lista[i]], strategy)()
				dic[lista[i]].eventDriven()

				fila = math.floor(i/2)
				col = i%2
				ax[fila][col].plot(dic[lista[i]].strat_performance, lw=1, label='Strategy')
				ax[fila][col].plot(dic[lista[i]].buyHold, lw=1, label='Buy & Hold')
				ax[fila][col].set_title(dic[lista[i]].ticker, y=0.70, fontweight='bold', alpha=0.3, fontsize=32, c='gray')
				ax[fila][col].set_ylabel("Performance in %")
				ax[fila][col].legend(loc= 'upper left', fontsize=12)

			fig.suptitle(f'{strategy} performance vs Buy & Hold - Since {start}', fontsize=25, y=0.95)
			plt.show()
		
		else:
			print('Lista no válida. Cantidad máxima de tickers a graficar: 10')

		return fig