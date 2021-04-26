import logging as log
import yfinance as yf
import pickle as pkl
import pandas as pd
import numpy as np

from math import sqrt
from math_functions import get_line_equation_parameters
from os import path

CURRENT_FILE_DIR = path.dirname(path.realpath(__file__))
log.basicConfig(format='%(levelname)s| %(message)s', level=log.INFO)


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
        self.time_horizon_in_days = 1
        self.time_horizon_as_a_years_part = self.time_horizon_in_days / 365
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
        wallet_info += '\n' + f'You will currently calculate the portfolio for stocks\' means and variances from results from the last {self.time_horizon_in_days} days.'
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

        wallet_data = pd.read_csv(self.file_name, header=0, sep=";")
        column_contains_only_numeric_data = wallet_data.apply(lambda s: pd.to_numeric(s, errors='coerce').notnull().all()).tolist()
        if not all(numeric_column is True for numeric_column in column_contains_only_numeric_data):
            log.error('Columns, apart from header, must contain only numeric values!')
            exit(1)

        for stock_name in wallet_data.columns:
            self.wallet.stocks.append(Stock(stock_name, wallet_data[stock_name]))

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
        while(True):
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
        self.wallet.k_risk_factor = float(input('Enter your risk factor k: '))
        log.info('Risk factor updated successfully.')

    def update_risk_free_asset(self):
        while True:
            self.wallet.risk_free_asset_expected_return = float(input('Enter your risk free asset expected return in percents: ')) / 100
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
                self.wallet.time_horizon_as_a_years_part = self.wallet.time_horizon_in_days / 365
                break
            else:
                log.error('You entered wrong number, try again.')

    def update_budget(self):
        while True:
            self.wallet.budget = int(input('Enter your budget: '))
            if self.wallet.budget > 0:
                log.info('Budget updated successfully.')
                break
            else:
                log.error('You entered wrong number, try again.')

    def apply_stock_splits(self, adj_close, stock_splits):
        if stock_splits != 0:
            return adj_close * (1 / (1 * stock_splits))
        else:
            return adj_close

    def get_stocks_daily_returns(self):
        for stock in self.wallet.stocks:
            if self.file_mode_on:
                stock_info = stock.pricing_info
            else:
                stock_info = yf.Ticker(stock.info['symbol']).history(period=f"{self.wallet.time_horizon_in_days}d")[['Close', 'Dividends', 'Stock Splits']]
            stock_info['Adj Close'] = stock_info['Close'] - stock_info['Dividends']
            stock_info['Adj Close'] = stock_info.apply(lambda x: self.apply_stock_splits(x['Adj Close'], x['Stock Splits']), axis=1)
            self.wallet.stocks_returns[stock.info['symbol']] = stock_info['Adj Close'].pct_change().apply(lambda x: np.log(1 + x))

    def calculate_z_matrix(self):
        # jestesmy nie w procentach ale w realnych liczbach, wszedzie!
        #czy tu mnożyć przez time horizon
        avg_returns_matrix = (self.wallet.stocks_returns.mean() - (self.wallet.risk_free_asset_expected_return * self.wallet.time_horizon_as_a_years_part)).to_numpy()[np.newaxis].T
        # zwrocic uwage jakie tu jednostki wychodza w cov matrix (kwadraty procentow)
        # self.wallet.cov_matrix = np.array([[0.36,0.2,0],[0.2,1,-0.6],[0,-0.6,2.25]])
        self.wallet.cov_matrix = (self.wallet.stocks_returns.cov()).to_numpy()
        z_matrix = np.dot(np.linalg.inv(self.wallet.cov_matrix), avg_returns_matrix)
        return z_matrix

    def calculate_tangent_portfolio_weights(self):
        self.get_stocks_daily_returns()
        log.info('Daily returns calculated, now calculating tangent portfolio weights..')
        list_of_z = [item for sublist in self.calculate_z_matrix().tolist() for item in sublist]
        self.wallet.risk_assets_weights = [z / sum(list_of_z) for z in list_of_z]
        log.info('Tangent portfolio weights calculated, now calculating optimal portfolio weights..')

    # def calculate_tangent_portfolio_std_dev(self):
    #     tangent_portfolio_variation = 0
    #     for i, risk_assets_weight_i in enumerate(self.wallet.risk_assets_weights):
    #         for j, risk_assets_weight_j in enumerate(self.wallet.risk_assets_weights):
    #             tangent_portfolio_variation += risk_assets_weight_i * risk_assets_weight_j * self.wallet.cov_matrix[i][j]

    #     return sqrt(tangent_portfolio_variation)

    # def get_efficient_porfolios_line_equation_parameters(self):
    #     risk_free_point = (0, self.wallet.risk_free_asset_expected_return * self.wallet.time_horizon_as_a_years_part)
    #     #czy tu mnożyć przez time horizon
    #     avg_returns_list = (self.wallet.stocks_returns.mean()).tolist()
    #     self.wallet.tangent_portfolio_mean = sum([y * mu for y, mu in zip(self.wallet.risk_assets_weights, avg_returns_list)])
    #     self.wallet.tangent_portfolio_std_dev = self.calculate_tangent_portfolio_std_dev()
    #     self.wallet.efficient_porfolios_line_equation_a, self.wallet.efficient_porfolios_line_equation_b = \
    #         get_line_equation_parameters(risk_free_point, (self.wallet.tangent_portfolio_std_dev, self.wallet.tangent_portfolio_mean))
        # y = self.efficient_porfolios_line_equation_a*x + self.efficient_porfolios_line_equation_b

    def calculate_optimal_portfolio_weights(self):
        #zamiast tego
        #policz A, mi zero i sigma zero i k masz i podstaw do wzoru na mi i sigma i bedzie te optymalne
        self.get_optimal_porfolios_parameters()
        # self.get_efficient_porfolios_line_equation_parameters()
        # self.wallet.optimal_portfolio_std_dev = (self.wallet.efficient_porfolios_line_equation_a) / (self.wallet.k_risk_factor * 2)
        # self.wallet.optimal_portfolio_mean = (self.wallet.efficient_porfolios_line_equation_a * self.wallet.optimal_portfolio_std_dev) \
        #     + self.wallet.efficient_porfolios_line_equation_b
        # self.wallet.risk_free_asset_weight = (self.wallet.optimal_portfolio_mean - self.wallet.tangent_portfolio_mean) / \
        #     ((self.wallet.risk_free_asset_expected_return * self.wallet.time_horizon_as_a_years_part) - self.wallet.tangent_portfolio_mean)
        self.wallet.optimal_portfolio_risk_assets_weight = 1 - self.wallet.risk_free_asset_weight

    def show_budget_calculations(self):
        log.info('That means, that you should invest your money this way:')
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
        self.calculate_tangent_portfolio_weights()
        self.calculate_optimal_portfolio_weights()
        self.show_risk_assets_weights()
        self.show_covariation_matrix()
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
        wallet_menu['5'] = 'Update amount of days to calculations'
        wallet_menu['6'] = 'Update budget'
        wallet_menu['7'] = 'Show optimal portfolio weights'
        wallet_menu['8'] = 'Save wallet to file'
        wallet_menu['9'] = 'Exit'

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
                self.update_amount_of_days_to_calculations()
            elif selection == '6':
                self.update_budget()
            elif selection == '7':
                self.show_optimal_portfolio_weights()
            elif selection == '8':
                self.save_wallet_to_file()
            elif selection == '9':
                self.main_menu()
            else:
                log.error('Unknown Option Selected!')

    def wallet_menu_file_mode(self):
        wallet_menu = {}
        wallet_menu['0'] = 'Show wallet'
        wallet_menu['1'] = 'Update risk-free asset'
        wallet_menu['2'] = 'Update risk factor'
        wallet_menu['3'] = 'Update amount of days to calculations'
        wallet_menu['4'] = 'Update budget'
        wallet_menu['5'] = 'Show optimal portfolio weights'
        wallet_menu['6'] = 'Save wallet to file'
        wallet_menu['7'] = 'Exit'

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
                self.update_amount_of_days_to_calculations()
            elif selection == '4':
                self.update_budget()
            elif selection == '5':
                self.show_optimal_portfolio_weights()
            elif selection == '6':
                self.save_wallet_to_file()
            elif selection == '7':
                exit(0)
            else:
                log.error('Unknown Option Selected!')
