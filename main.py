import functions as func
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='the-wallet - Markowitz Portfolio Tool to calculate ' \
                                                 'your optimal portfolio of investment.')

    parser.add_argument('-f', '--file', type=str, help='Turn on if you want to run the-wallet in file ' \
                                                       'mode, more information (about file preparation ' \
                                                       'etc.) can be found in README.md')

    args = parser.parse_args()

    func.Interface(args)
