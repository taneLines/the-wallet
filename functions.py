import logging as log
import yfinance as yf
import pickle as pkl
import pandas as pd
import numpy as np

from math import sqrt
from additional_functions import apply_stock_splits, given_data_is_long_enough
from os import path

CURRENT_FILE_DIR = path.dirname(path.realpath(__file__))
log.basicConfig(format='%(levelname)s| %(message)s', level=log.INFO)

N_DAYS_RETURNS_MAP = {'1d' : 1, '1wk' : 7, '1mo' : 30, '3mo' : 90}

class Stock():
    """Used only in file mode to emulate stock from API"""
    def __init__(self, symbol, close_prices):
        self.info = {'symbol': symbol, 'shortName': symbol}
        self.pricing_info = pd.DataFrame()
        self.pricing_info['Close'] = close_prices
        self.pricing_info['Dividends'] = 0
        self.pricing_info['Stock Splits'] = 0


class Wallet():
    """Markowitz Portfolio"""
    def __init__(self):
        self.stocks = []
        self.stocks_returns = pd.DataFrame()
        self.k_risk_factor = 0
        self.risk_free_asset_expected_return = 0
        self.risk_assets_weights = []
        self.risk_free_asset_weight = 0
        self.time_horizon_in_days = 500
        self.n_days_return_str = '1d'
        self.n_days_return = N_DAYS_RETURNS_MAP[self.n_days_return_str]
        self.n_days_return_as_a_years_part = self.n_days_return / 365
        self.budget = 100
        self.file_mode_on = False

    def __str__(self):
        wallet_info = 'Stocks in your wallet:'
        if not self.stocks:
            wallet_info += ' currently no stocks in your wallet :('
        for stock in self.stocks:
            wallet_info += '\n' + stock.info['symbol'] + ' - ' + stock.info['shortName']
        wallet_info += '\n' + '-----------------------'
        wallet_info += '\n' + f'Your bugdet is {self.budget} USD'
        wallet_info += '\n' + f'Risk free asset year\'s expected return: {self.risk_free_asset_expected_return*100}%'
        wallet_info += '\n' + f'Investor\'s risk function is: U = \u03BC - ({self.k_risk_factor}*\u03C3)'
        wallet_info += '\n' + f'You will currently calculate the portfolio for stocks\' means and variances ' \
                              f'from results from the last {self.time_horizon_in_days} days.'
        wallet_info += '\n' + f'You will currently calculate the portfolio for calculated {self.n_days_return}-day(s) returns.'
        return wallet_info


class Interface():
    def __init__(self, args):
        self.file_mode_on = False
        if args.file:
            self.file_mode_on = True
            self.file_name = args.file
        self.main_menu()
        if self.file_mode_on:
            self.wallet_menu_file_mode()
        else:
            self.wallet_menu_api()

    def load_stocks_info_from_file(self):
        self.wallet = Wallet()
        self.wallet.file_mode_on = True

        wallet_data = pd.read_csv(self.file_name, header=0, sep=';')
        column_contains_only_numeric_data = wallet_data.apply(\
            lambda s: pd.to_numeric(s, errors='coerce').notnull().all()).tolist()
        if not all(numeric_column is True for numeric_column in column_contains_only_numeric_data):
            log.error('Columns, apart from header, must contain only numeric values!')
            exit(1)

        for stock_name in wallet_data.columns:
            self.wallet.stocks.append(Stock(stock_name, wallet_data[stock_name]))
        self.wallet.time_horizon_in_days = len(self.wallet.stocks[0].pricing_info)

    def open_existing_wallet(self):
        while(True):
            wallet_path = input('Write path to file: ')
            if path.exists(wallet_path):
                try:
                    with open(wallet_path, 'rb') as wallet_pickle:
                        self.wallet = pkl.load(wallet_pickle)
                        if self.wallet.file_mode_on:
                            self.file_mode_on = True
                            log.info('Mode changed from API to file-mode')
                        log.info('Wallet loaded successfully.')
                        break
                except Exception as e:
                    log.error(f'Cannot load wallet file! Reason: {e}')
            else:
                log.error('Path does not exist!')

    def save_wallet_to_file(self):
        while True:
            wallet_path = input('Write path to file where you want to save your wallet: ')
            if path.exists(wallet_path):
                choice = input('This file already exist. Do you want to overwrite your wallet? [y/n] ')
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
            # threshold to pass
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
        while True:
            try:
                self.wallet.k_risk_factor = float(input('Enter your risk factor k: '))
                if self.wallet.k_risk_factor > 0:
                    log.info('Risk factor updated successfully.')
                    break
                else:
                    log.error('You entered wrong number (value must be greater than zero), try again.')
            except:
                log.error('You entered wrong number (value must be greater than zero), try again.')


    def update_risk_free_asset(self):
        while True:
            try:
                self.wallet.risk_free_asset_expected_return = float(input('Enter your risk free ' \
                    'asset years\' expected return in percents: ')) / 100
                if (self.wallet.risk_free_asset_expected_return >= 0) and (self.wallet.risk_free_asset_expected_return < 100):
                    log.info('Risk free asset updated successfully.')
                    break
                else:
                    log.error('You entered wrong number, try again.')
            except:
                log.error('You entered wrong number, try again.')

    def update_amount_of_days_to_take_data_from(self):
        while True:
            try:
                self.wallet.time_horizon_in_days = int(input('Enter amount of days to take data from: '))
                if self.wallet.time_horizon_in_days > 0 and \
                   given_data_is_long_enough(self.wallet.time_horizon_in_days, self.wallet.stocks, self.file_mode_on):
                    log.info('Time horizon updated successfully.')
                    break
                else:
                    log.error('Value is negative or too big for given data, try again.')
            except:
                log.error('Value is negative or too big for given data, try again.')

    def update_return_calculation(self):
        while True:
            try:
                self.wallet.n_days_return_str = str(input('You want to calculate portfolio for n-days return. '\
                                                          'Enter interval (possible choices: 1d, 1wk, 1mo, 3mo): '))
                if self.wallet.n_days_return_str in N_DAYS_RETURNS_MAP.keys() and \
                   given_data_is_long_enough(self.wallet.time_horizon_in_days, self.wallet.stocks, self.file_mode_on) and \
                   self.wallet.time_horizon_in_days >= N_DAYS_RETURNS_MAP[self.wallet.n_days_return_str]:
                    self.wallet.n_days_return = N_DAYS_RETURNS_MAP[self.wallet.n_days_return_str]
                    self.wallet.n_days_return_as_a_years_part = self.wallet.n_days_return / 365
                    log.info('Time horizon updated successfully.')
                    break
                else:
                    log.error('Value is not valid or too big for given data, try again.')
            except:
                log.error('Value is not valid or too big for given data, try again.')

    def update_budget(self):
        while True:
            try:
                self.wallet.budget = int(input('Enter your budget: '))
                if self.wallet.budget > 0:
                    log.info('Budget updated successfully.')
                    break
                else:
                    log.error('You entered wrong number, try again.')
            except:
                log.error('You entered wrong number, try again.')

    def get_stocks_returns(self):
        self.wallet.stocks_returns = pd.DataFrame()
        for stock in self.wallet.stocks:
            if self.file_mode_on:
                stock_info = stock.pricing_info
            else:
                stock_info = \
                    yf.Ticker(stock.info['symbol'])\
                    .history(period=f'{self.wallet.time_horizon_in_days}d', interval=self.wallet.n_days_return_str)\
                    [['Close', 'Dividends', 'Stock Splits']]
            stock_info['Adj Close'] = stock_info['Close'] - stock_info['Dividends']
            stock_info['Adj Close'] = \
                stock_info.apply(lambda x: apply_stock_splits(x['Adj Close'], x['Stock Splits']), axis=1)
            try:
                self.wallet.stocks_returns[stock.info['symbol']] = \
                    stock_info['Adj Close'].dropna().pct_change()*100
            except ValueError:
                self.wallet.stocks_returns[stock.info['symbol']] = \
                    (stock_info['Adj Close'].pct_change()*100).reindex(self.wallet.stocks_returns.index)

    def calculate_z_matrix(self):
        avg_returns_matrix = \
            (self.wallet.stocks_returns.mean() - \
             self.wallet.risk_free_asset_expected_return_in_given_time_horizon).\
             to_numpy()[np.newaxis].T
        self.wallet.cov_matrix = self.wallet.stocks_returns.cov().to_numpy()
        z_matrix = np.dot(np.linalg.inv(self.wallet.cov_matrix), avg_returns_matrix)
        return z_matrix

    def calculate_tangent_portfolio_weights(self):
        self.get_stocks_returns()
        log.info('Returns calculated, now calculating tangent portfolio weights..')
        list_of_z = [item for sublist in self.calculate_z_matrix().tolist() for item in sublist]
        self.wallet.risk_assets_weights = [z / sum(list_of_z) for z in list_of_z]
        log.info('Tangent portfolio weights calculated, now calculating optimal portfolio weights..')

    def calculate_tangent_portfolio_std_dev(self):
        tangent_portfolio_variation = 0
        for i, risk_assets_weight_i in enumerate(self.wallet.risk_assets_weights):
            for j, risk_assets_weight_j in enumerate(self.wallet.risk_assets_weights):
                tangent_portfolio_variation += risk_assets_weight_i * risk_assets_weight_j * self.wallet.cov_matrix[i][j]

        return sqrt(abs(tangent_portfolio_variation))

    def get_tangent_portfolio_parameters(self):
        self.wallet.tangent_portfolio_std_dev = self.calculate_tangent_portfolio_std_dev()
        avg_returns_list = self.wallet.stocks_returns.mean().tolist()
        self.wallet.tangent_portfolio_expected_return = sum([y * mu for y, mu in zip(self.wallet.risk_assets_weights, avg_returns_list)])

    def get_optimal_portfolio_parameters(self):
        self.wallet.optimal_portfolio_A = (self.wallet.tangent_portfolio_std_dev ** 2) / \
            ((self.wallet.risk_free_asset_expected_return_in_given_time_horizon - self.wallet.tangent_portfolio_expected_return) ** 2)
        self.wallet.optimal_portfolio_std_dev = sqrt(1 / (4 * (self.wallet.k_risk_factor ** 2) * self.wallet.optimal_portfolio_A))
        self.wallet.optimal_portfolio_expected_return = self.wallet.risk_free_asset_expected_return_in_given_time_horizon + \
            (1 / (2 * self.wallet.k_risk_factor * self.wallet.optimal_portfolio_A))

    def calculate_optimal_portfolio_weights(self):
        self.get_tangent_portfolio_parameters()
        self.get_optimal_portfolio_parameters()
        self.wallet.risk_free_asset_weight = \
            (self.wallet.optimal_portfolio_expected_return - self.wallet.tangent_portfolio_expected_return) / \
            (self.wallet.risk_free_asset_expected_return_in_given_time_horizon - self.wallet.tangent_portfolio_expected_return)
        self.wallet.optimal_portfolio_risk_assets_weight = 1 - self.wallet.risk_free_asset_weight

    def show_budget_calculations(self):
        log.info('That means, that you should invest your money this way in risk assets:')
        risk_assets_investments = [i * self.wallet.optimal_portfolio_risk_assets_weight * self.wallet.budget for i in self.wallet.risk_assets_weights]
        risk_free_asset_investment = self.wallet.risk_free_asset_weight * self.wallet.budget
        for risk_asset_investment, stock in zip(risk_assets_investments, self.wallet.stocks):
            stock_name = stock.info['shortName']
            log.info(f'{stock_name} - {risk_asset_investment:.2f} USD')
        log.info(f'In risk free asset, you shold invest {risk_free_asset_investment:.2f} USD')
        log.info('Remember, if any invesment retuns negative score - you should make it short position.')

    def show_risk_assets_weights(self):
        log.info('Risk assests weights:')
        for risk_asset_weight, stock in zip(self.wallet.risk_assets_weights, self.wallet.stocks):
            stock_name = stock.info['shortName']
            log.info(f'{stock_name} - {risk_asset_weight:.2f}')

    def show_covariation_matrix(self):
        log.info('Covariation matrix:')
        print(self.wallet.cov_matrix)

    def show_optimal_portfolio_weights(self):
        self.wallet.risk_free_asset_expected_return_in_given_time_horizon = \
            self.wallet.risk_free_asset_expected_return * self.wallet.n_days_return_as_a_years_part
        self.calculate_tangent_portfolio_weights()
        self.show_risk_assets_weights()
        self.show_covariation_matrix()
        self.calculate_optimal_portfolio_weights()
        log.debug(f'Risk assets exp ret: {self.wallet.tangent_portfolio_expected_return}')
        log.debug(f'Risk assets std dev: {self.wallet.tangent_portfolio_std_dev}')
        log.debug(f'Risk free assets exp ret: {self.wallet.risk_free_asset_expected_return_in_given_time_horizon}')
        log.info(f'Risk assets weight is {self.wallet.optimal_portfolio_risk_assets_weight:.2f}')
        log.info(f'Risk free asset weight is {self.wallet.risk_free_asset_weight:.2f}')
        self.show_budget_calculations()

    def main_menu(self):
        log.info('Welcome to the-wallet - Markowitz Portfolio tool')

        if self.file_mode_on:
            log.info(f'File mode turned on, loading data from {self.file_name}')
            self.load_stocks_info_from_file()
            return

        main_menu = {}
        main_menu['1'] = 'Open existing wallet'
        main_menu['2'] = 'Start with new wallet'
        main_menu['3'] = 'Exit'

        while(True):
            options = main_menu.keys()
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

    def wallet_menu_api(self):
        wallet_menu = {}
        wallet_menu['0'] = 'Show wallet'
        wallet_menu['1'] = 'Add stocks'
        wallet_menu['2'] = 'Remove stocks'
        wallet_menu['3'] = 'Update risk-free asset'
        wallet_menu['4'] = 'Update risk factor'
        wallet_menu['5'] = 'Update amount of days to take data from'
        wallet_menu['6'] = 'Update days return'
        wallet_menu['7'] = 'Update budget'
        wallet_menu['8'] = 'Show optimal portfolio weights'
        wallet_menu['9'] = 'Save wallet to file'
        wallet_menu['10'] = 'Exit'

        while(True):
            print()
            options = wallet_menu.keys()
            for entry in options:
                print(f'{entry}. {wallet_menu[entry]}')

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
                self.update_amount_of_days_to_take_data_from()
            elif selection == '6':
                self.update_return_calculation()
            elif selection == '7':
                self.update_budget()
            elif selection == '8':
                self.show_optimal_portfolio_weights()
            elif selection == '9':
                self.save_wallet_to_file()
            elif selection == '10':
                self.main_menu()
            else:
                log.error('Unknown Option Selected!')

    def wallet_menu_file_mode(self):
        wallet_menu = {}
        wallet_menu['0'] = 'Show wallet'
        wallet_menu['1'] = 'Update risk-free asset'
        wallet_menu['2'] = 'Update risk factor'
        wallet_menu['3'] = 'Update amount of days to take data from'
        wallet_menu['4'] = 'Update days return'
        wallet_menu['5'] = 'Update budget'
        wallet_menu['6'] = 'Show optimal portfolio weights'
        wallet_menu['7'] = 'Save wallet to file'
        wallet_menu['8'] = 'Exit'

        while(True):
            print()
            options = wallet_menu.keys()
            for entry in options:
                print(f'{entry}. {wallet_menu[entry]}')

            selection = input('Please Select: ')
            if selection == '0':
                print(self.wallet)
            elif selection == '1':
                self.update_risk_free_asset()
            elif selection == '2':
                self.update_risk_factor()
            elif selection == '3':
                self.update_amount_of_days_to_take_data_from()
            elif selection == '4':
                self.update_return_calculation()
            elif selection == '5':
                self.update_budget()
            elif selection == '6':
                self.show_optimal_portfolio_weights()
            elif selection == '7':
                self.save_wallet_to_file()
            elif selection == '8':
                exit(0)
            else:
                log.error('Unknown Option Selected!')
