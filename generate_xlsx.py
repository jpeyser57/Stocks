import argparse
import webbrowser
import time
import re
import os
from datetime import date

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--date')
    parser.add_argument('-o', '--olddate')
    parser.add_argument('-s', '--symbol')
    parser.add_argument('-f', '--file')
    parser.add_argument('-b', '--breakout', action='store_true')
    parser.add_argument('-c', '--cross', action='store_true')
    parser.add_argument('-m', '--midcaps', action='store_true')
    args = parser.parse_args()
    return args, parser

def getPriceVolume(symbol, date):
    price = None
    file = "{}\{}\{}.csv".format(os.getcwd(), date, symbol)
    isodate = "{}-{}-{}".format(date[:4], date[4:6], date[6:8])
    with open(file, 'r') as f:
        prices = f.read()
        p = prices.split('\n')
        close = p[-1].split(',')[4]
        volume = p[-1].split(',')[6]
    return close, volume

if __name__ == '__main__':
    ### Parse command line arguments
    args, parser = parse_args()
    if not args.date:
        today = date.today()
        args.date = today.strftime('%Y%m%d')

    if args.breakout:
        plotsDir = 'Plots_B'
    elif args.cross:
        plotsDir = 'Plots_C'
    else:
        plotsDir = 'Plots'
        
    symbols = None
    if args.symbol:
        symbols = args.symbol.split(',')
    elif args.file:
        symbols = []
        with open(args.file) as f:
            symbols = f.read().split('\n')
    elif args.date:
        symbols = []
        dirdate = args.olddate if args.olddate else args.date
        for f in os.listdir('{}/{}'.format(dirdate, plotsDir)):
            s = re.sub('.pdf', '', f)
            symbols.append(s)
    else:
        parser.print_help()
        exit()
            
    print("Stock,Price,Volume,Yahoo Page,Graph")
    for s in symbols:
        if s:
            price, volume = getPriceVolume(s, args.date) if args.date else None
            yahoo = '"=HYPERLINK(""https://finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch"",""Yahoo Quote - {}"")"'.format(s, s, s)
            link = '"=HYPERLINK(""c:\\Users\\Jonathan Peyser\\stocks_wd\\{}\\{}\\{}.pdf"",""{}.pdf"")"'.format(args.date, plotsDir, s, s) if args.date else None
            #print("{},{},https://finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch,{}".format(s, price, s, s, link))
            print("{},{},{},{},{}".format(s, price, volume, yahoo, link))
        
            
