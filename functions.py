import logging as log
import yfinance as yf
import pickle as pkl

from os import path

CURRENT_FILE_DIR = path.dirname(path.realpath(__file__))
log.basicConfig(format='%(levelname)s| %(message)s', level=log.DEBUG)

class Wallet():
    def __init__(self):
        self.stocks = []
        self.k_risk_factor = 0
        self.risk_free_asset_expected_return = 0
        self.risk_assets_weights = []
        self.risk_free_asset_weight = 0
        self.time_horizon_in_days = 0
        self.budget = 100

    def __str__(self):
        wallet_info = 'Stocks in your wallet:'
        if not self.stocks:
            wallet_info += ' currently no stocks in your wallet :('
        for stock in self.stocks:
            wallet_info += '\n' + stock.info['symbol'] + ' - ' + stock.info['shortName']
        wallet_info += '\n' + '-----------------------'
        wallet_info += '\n' + f'Risk free asset expected return: {self.risk_free_asset_expected_return*100}%'
        wallet_info += '\n' + f'Investor\'s risk function is: U = \u03BC - ({self.k_risk_factor}*\u03C3)'
        wallet_info += '\n' + f'You will currently calculate the portfolio for means and variances from results from the last {self.time_horizon_in_days} days.'
        return wallet_info

class Interface():
    """Markowitz Portfolio"""
    def __init__(self):
        self.main_menu()
        self.wallet_menu()

    def open_existing_wallet(self):
        while(True):
            wallet_path = input('Write path to file:')
            if path.exists(wallet_path):
                try:
                    with open(wallet_path, 'rb') as wallet_pickle:
                        self.wallet = pkl.load(wallet_pickle)
                        log.info('Wallet loaded successfully.')
                        break
                except Exception as e:
                    log.error(f'Cannot load wallet file! Reason: {e}')
            else:
                log.error('Path does not exist!')

    def save_wallet_to_file(self):
        while(True):
            wallet_path = input('Write path to file where you want to save your wallet:')
            if path.exists(wallet_path):
                choice = input('This file already exist. Do you want to overwrite your wallet? [y/n]')
                if str.upper(choice) == 'Y':
                    pass
                elif str.upper(choice) == 'N':
                    continue
            try:
                with open(wallet_path, 'wb') as wallet_pickle:
                    pkl.dump(self.wallet, wallet_pickle)
                log.info(f'Walled successfully saved to {wallet_path}')
                break
            except Exception as e:
                log.error(f'Cannot save wallet file! Reason: {e}')

    def add_stock_to_wallet(self):
        stock_to_add = input('Write symbol of stock you want to add: ')
        try:
            #threshold to pass
            log.info('Checking if stock exist/is valid...')
            yf.Ticker(stock_to_add).info
            self.wallet.stocks.append(yf.Ticker(stock_to_add))
            log.info(f'{stock_to_add} added successfully')
        except Exception as e:
            log.error(f'Cannot add stock named {stock_to_add}! Probably it does not exist in Yahoo Finance API.')

    def remove_stock_from_wallet(self):
        stock_to_remove = input('Write symbol of stock you want to remove: ')
        stocks_names = [stock.info['symbol'] for stock in self.wallet.stocks]
        if not stock_to_remove in stocks_names:
            log.error('This stock does not exist in this wallet!')
        try:
            self.wallet.stocks = [stock for stock in self.wallet.stocks if stock.info['symbol'] != stock_to_remove]
            log.info('Stocks updated successfully')
        except Exception as e:
            log.error(f'Cannot remove stock named {stock_to_remove}! Reason: {e}')

    def update_risk_factor(self):
        self.wallet.k_risk_factor = int(input('Enter your risk factor k: '))
        log.info('Risk factor updated successfully.')

    def update_risk_free_asset(self):
        while True:
            self.wallet.risk_free_asset_expected_return = int(input('Enter your risk free asset expected return in percents: '))
            if (self.wallet.risk_free_asset_expected_return >= 0) and (self.wallet.risk_free_asset_expected_return < 100):
                log.info('Risk free asset updated successfully.')
                break
            else:
                log.error('You entered wrong number, try again.')

    def update_amount_of_days_to_calculations(self):
        while True:
            self.wallet.time_horizon_in_days = int(input('Enter amount of days to calculations: '))
            if self.wallet.time_horizon_in_days > 0:
                log.info('Time horizon updated successfully.')
                break
            else:
                log.error('You entered wrong number, try again.')

    def update_budget():
        while True:
            self.wallet.budget = int(input('Enter your budget: '))
            if self.wallet.budget > 0:
                log.info('Budget updated successfully.')
                break
            else:
                log.error('You entered wrong number, try again.')

    def apply_stock_splits(self, adj_close, stock_splits):
        if stock_splits != 0:
            return adj_close * (1/(1*stock_splits)) 
        else:
            return adj_close

    def calculate_stock_average_return(self, stock):
        stock_info = yf.Ticker(stock.info['symbol']).history(period=f"{self.wallet.time_horizon_in_days}d")[['Close','Dividends','Stock Splits']]
        stock_info['Adj Close'] = stock_info['Close'] - stock_info['Dividends']
        stock_info['Adj Close'] = stock_info.apply(lambda x: self.apply_stock_splits(x['Adj Close'], x['Stock Splits']), axis=1)
        avg_return = (((stock_info['Adj Close']/stock_info['Adj Close'].shift(1)) - 1).mean())*self.wallet.time_horizon_in_days
        print(f"{avg_return*100}%")

    def calculate_optimal_portfolio_weights(self):
        for stock in self.wallet.stocks:
            self.calculate_stock_average_return(stock)

    def show_optimal_portfolio_weights(self):
        self.calculate_optimal_portfolio_weights()

    def main_menu(self):
        log.info('Welcome to the-wallet - Markowitz Portfolio tool')

        main_menu = {}
        main_menu['1']='Open existing wallet'
        main_menu['2']='Start with new wallet'
        main_menu['3']='Exit'

        while(True): 
            options=main_menu.keys()
            for entry in options:
                print(f'{entry}. {main_menu[entry]}')

            selection = input('Please Select: ') 
            if selection == '1': 
                self.open_existing_wallet()
                break
            elif selection == '2': 
                self.wallet = Wallet()
                log.info('New wallet created.')
                break
            elif selection == '3':
                log.info('Goodbye!') 
                exit(0)
            else:
                log.error('Unknown Option Selected!')

    def wallet_menu(self):
        main_menu = {}
        main_menu['0']='Show wallet'
        main_menu['1']='Add stocks'
        main_menu['2']='Remove stocks'
        main_menu['3']='Update risk-free asset'
        main_menu['4']='Update risk factor'
        main_menu['5']='Update amount of days to calculations'
        main_menu['6']='Update budget'
        main_menu['7']='Show optimal portfolio weights'
        main_menu['8']='Plot portfolio'
        main_menu['9']='Save wallet to file'
        main_menu['10']='Exit'

        while(True): 
            print()
            options=main_menu.keys()
            for entry in options:
                print(f'{entry}. {main_menu[entry]}')

            selection = input('Please Select: ') 
            if selection == '0':
                print(self.wallet)
            elif selection == '1': 
                self.add_stock_to_wallet()
            elif selection == '2': 
                self.remove_stock_from_wallet()
            elif selection == '3':
                self.update_risk_free_asset()
            elif selection == '4': 
                self.update_risk_factor()
            elif selection == '5': 
                self.update_amount_of_days_to_calculations()
            elif selection == '6':
                self.update_budget()
            elif selection == '7':
                self.show_optimal_portfolio_weights()
            elif selection == '8':
                self.plot_portfolio()
            elif selection == '9': 
                self.save_wallet_to_file()
            elif selection == '10':
                self.main_menu()
            else:
                log.error('Unknown Option Selected!')


'''
mozna sprobowac tez z wpisywanymi z palucha

il aktywow ryzykownych
stopy zwrotu po np miesiacu
macierz kowariancji na wejściu 
markowitz pdf - 410 - 
stopa wolna od ryzyka jest tylko jedna - 399
dostaje z-ty i z nich x czyli wagi i dostaje portfel stycznosci
funcja uzytecznosci awersji do ryzyka - 400

ile aktywow na portfel stycznosci
a ile na stope wolna od ryzyka
to jest clue
i ro
pierwsze 2 rozdzialy do konca przyszlego weekendu

proba prosta
'''
