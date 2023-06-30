import configparser
import argparse
import datetime
import os
import sys
import webbrowser
import time
from datetime import date
from datetime import timedelta

stackCnt = 0

def parse_args():
    parser = argparse.ArgumentParser()
    #parser.add_argument('-d', '--date', required=True)
    parser.add_argument('-d', '--date')
    parser.add_argument('-f', '--file')
    parser.add_argument('-s', '--stock')
    parser.add_argument('-b', '--begindate')
    args = parser.parse_args()
    return args

def readConfigDefault():
    ### Read Config File
    inifile = './stocks.ini'
    config = configparser.ConfigParser()
    config.read(inifile)
    return config['DEFAULT']

def audit(event, args):
    global stackCnt
    if event == 'webbrowser.open':
        stackCnt += 1

if __name__ == '__main__':
    sys.addaudithook(audit)
    
    ### Read Config File Default Section
    dfltsect = readConfigDefault()
    stocksRoot = dfltsect['HistoricalDataRoot']

    stocksRoot = dfltsect['HistoricalDataRoot']
    downloadDir = dfltsect['DownloadDirectory']
    stocksList = dfltsect['stocksList']

    args = parse_args()
    ### If no date provided, calculate date of beginning of current week.
    pDate = args.date
    #if pDate and pDate.lower() == 'today':
    if str(pDate).lower() == 'today':
        today = date.today()
        pDate = today.strftime('%Y%m%d')
    elif not pDate:
        today = date.today()
        daysSinceSunday = (today.weekday() + 1) % 7
        sunday = today - timedelta(days = daysSinceSunday)
        pDate = sunday.strftime('%Y%m%d')
    
    ### Calculate dates and times
    startdate = datetime.date(1970, 1, 1)
    enddate = datetime.date(int(pDate[:4]), int(pDate[4:6]), int(pDate[6:8]))
    lastyear = datetime.date(enddate.year - 1, enddate.month, enddate.day)
    if args.begindate:
        lastyear = datetime.date(int(args.begindate[0:4]), int(args.begindate[4:6]), int(args.begindate[6:8]))
    print(enddate, lastyear)
    t = enddate - startdate
    endtime = t.days * 24 * 3600
    t = lastyear - startdate
    lastyeartime = t.days * 24 * 3600

    ### Create data directory for historical data
    wdate = "{}{:02d}{:02d}".format(enddate.year, enddate.month, enddate.day)
    stocksDir = "{}/{}".format(stocksRoot, wdate)
    if not os.path.exists(stocksDir):
        os.makedirs(stocksDir)
        print ("Created Directory {}".format(stocksDir))

    stocks = None
    ### Read list of stocks
    if args.file:
        with open(args.file, 'r') as f:
            stocks = [line.strip() for line in f]
    elif args.stock:
        stocks = [args.stock]

    ### Download historical data
    # getting browser path
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    # register the new browser
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    urlformat = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&includeAdjustedClose=true"
    
    cnt = prevcnt = 0
    numberOfStocks = len(stocks)
    batchsize = 10
    pos = 0
    while True:
        stackCnt = 0
        for i in range(pos, min(pos + batchsize, numberOfStocks)):
            destfile = "{}/{}.csv".format(stocksDir, stocks[i])
            if not os.path.exists(destfile):
                # Download files
                print(destfile)
                url = urlformat.format(stocks[i], lastyeartime, endtime)
                #webbrowser.get('chrome').open(url)
                webbrowser.get().open(url)
                cnt += 1
                if not cnt % 20:
                    print("{} files downloaded...".format(cnt))
        if cnt > prevcnt:
            ### Wait for files to download
            while stackCnt < cnt - prevcnt:
                time.sleep(1)
                print('Waiting... {}'.format(str(stackCnt)))
            time.sleep(2)
        
            ### Move files
            for i in range(pos, min(pos + batchsize, numberOfStocks)):
                sourcefile = "{}/{}.csv".format(downloadDir, stocks[i])
                if os.path.exists(sourcefile):
                    destfile = "{}/{}.csv".format(stocksDir, stocks[i])
                    os.rename(sourcefile, destfile)
            #time.sleep(1)

        prevcnt = cnt
        if pos > numberOfStocks:
            break
        pos += batchsize
    print ("{} new files downloaded!".format(cnt))
        
# "/Users/Jonathan Peyser/AppData/Local/Programs/Python/Python38/python.exe" "\Users\Jonathan Peyser\stocks_wd\StocksDownload.py" -d 20230205
