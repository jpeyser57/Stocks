import configparser
import argparse
import re
import os
from datetime import datetime
from datetime import date
from datetime import timedelta
#import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--date')
    parser.add_argument('-s', '--symbol')
    parser.add_argument('-w', '--window', help='Range of last n days in which indicators are found')
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-g', '--debug', action='store_true')
    args = parser.parse_args()
    return args

def readConfigDefault():
    ### Read Config File
    #inifile = "c:/Users/Jonathan Peyser/stocks_wd/stocks.ini"
    inifile = "{}/stocks.ini".format(os.curdir)
    print(inifile)
    config = configparser.ConfigParser()
    config.read(inifile)
    return config['DEFAULT']

def plotGraph(plt, dates, prices, rsis):
    plt.plot(dates, prices, rsis)
    plt.axhline(y=30, color="red", linestyle="--")
    plt.show()

    
if __name__ == '__main__':
    lbdays = 14

    ### Read Config File Default Section
    dfltsect = readConfigDefault()
    stocksRoot = dfltsect['HistoricalDataRoot']
    stocksRoot = dfltsect['HistoricalDataRoot']
    downloadDir = dfltsect['DownloadDirectory']
    stocksList = dfltsect['stocksList']
    
    ### Parse command line arguments
    args = parse_args()
    if not args.date:
        today = date.today()
        args.date = today.strftime('%Y%m%d')
    dirdate = args.date

    ### Format startdate as string
    # isodate = "{}-{}-{}".format(args.date[:4], args.date[4:6], args.date[6:8])
    # pDate = date.fromisoformat(isodate)
    ### Default is from start of month
    # if not args.window:
    #     args.window = int(pDate.strftime('%d'))
    # startDate = pDate - timedelta(days = int(args.window))
    # startdate = startDate.strftime('%Y%m%d')
    
    if args.symbol:
        dir_list = ["{}.csv".format(args.symbol)]
    else:
        ### Check if plot directory exists
        createDirFlag = False
        plotsDir = "{}/{}/{}".format(stocksRoot, dirdate, 'Plots_B')
        if not os.path.exists(plotsDir):
            createDirFlag = True

        ### Read Directory
        dir_list = []
        with os.scandir("{}/{}".format(stocksRoot, dirdate)) as it:
            for entry in it:
                if entry.is_file():
                    dir_list.append(entry.name)

    nmbr = 0
    output = []
    for fname in dir_list:
        rows = []
        dates = []
        prices = []
        rsis = []
        cntr = 0
        prevprice = 1
        lavgpos = []
        lavgneg = []
        avgpos = avgneg = 0
        rsi = 0
        skip = False
        symbol = fname[:-4]
        nmbr += 1
        if nmbr % 20 == 0:
            print("Processed {} files...".format(str(nmbr)))
        
        try:
            filename = "{}/{}/{}".format(stocksRoot, dirdate, fname)
            f = open(filename, "r")
            ### Read lines from file
            for line in f:
                if not re.match('Date', line):
                    rows.append(line)
            f.close()
        except IOError:
            print('WARNING: Error opening file {}.'.format(filename))
            continue
        
        ### Sort rows according to date
        rows.sort(key=lambda date: datetime.strptime(date.split(",")[0], "%Y-%m-%d"))

        ### Calculate RSI
        for line in rows:
            fields = line.split(',')
            if 'null' in fields:
                skip = True
                continue
            price = float(fields[1].replace("$", ""))
            diff = (price - prevprice) / prevprice
            if cntr > 0 and cntr <= lbdays:
                if diff > 0:
                    lavgpos.append(diff / 100)
                elif diff < 0:
                    lavgneg.append(diff * -1 / 100)
                    
                if cntr == lbdays:
                    # Calculate initial averages.
                    avgpos = sum(lavgpos) / lbdays
                    avgneg = sum(lavgneg) / lbdays
                    # Calculate RSI
                    rsi = 100 if avgneg == 0 else 100 - (100 / (1 + (avgpos / avgneg)))
                    #print("{},{},{}".format(fields[0], price, rsi))
                    dates.append(fields[0])
                    prices.append(price)
                    rsis.append(rsi)
            elif cntr > lbdays:
                avgpos = ((avgpos * (lbdays - 1)) + (diff if diff > 0 else 0)) / lbdays
                avgneg = ((avgneg * (lbdays - 1)) + (diff * -1 if diff < 0 else 0)) / lbdays
                rsi = 100 if avgneg == 0 else 100 - (100 / (1 + (avgpos / avgneg)))
                #print("{},{},{}".format(fields[0], price, rsi))
                dates.append(fields[0])
                prices.append(price)
                rsis.append(rsi)

            prevprice = price
            cntr += 1

        if skip:
            continue
        
        ### scipy
        ### Find Peaks
        p = np.array(rsis)
        peaks, props = find_peaks(p, height=0)
        props_peaks = props['peak_heights']
        
        if props_peaks.size == 0:
            continue
        all_peaks = []
        j = 0
        for i in range(len(rsis)):
            if rsis[i] == props_peaks[j]:
                all_peaks.append((i, rsis[i], 'P', dates[i]))
                j += 1
                if j == len(props_peaks):
                    break

        ### Find Valleys
        v = np.array(rsis) * -1
        valleys, props = find_peaks(v, height=(None, 0))
        props_valleys = props['peak_heights'] * -1

        if props_valleys.size == 0:
            continue
        all_valleys = []
        j = 0
        for i in range(len(rsis)):
            if rsis[i] == props_valleys[j]:
                all_valleys.append((i, rsis[i], 'V', dates[i]))
                j += 1
                if j == len(props_valleys):
                    break

        # if args.debug:
        #     for r in all_valleys:
        #         print("{} {} {}".format(r[3], prices[r[0]], r[1]))

        all_props = sorted(all_peaks +  all_valleys, key=lambda p: p[0])
        if args.debug:
            for p in all_props:
                print(p)

        ### Number of days before current date to search for breakout
        diffdays = int(args.window) if args.window else 28
        today = date.today()
        dfdate = today - timedelta(days = diffdays)
        dfDate = dfdate.strftime('%Y%m%d')

        stage = 0
        starti = 0
        plotFlag = False
        prev_rsi = 29
        saverow = None
        for i in range(len(all_valleys)):
            ### RSI is below 30
            if all_valleys[i][1] < 30.0:
                prev_rsi = all_valleys[i][1]
                stage = 1
                starti = i
                saverow = all_valleys[i]
            elif stage == 1:
                ### RSI has risen above 30
                if all_valleys[i][1] > 30:
                    prev_rsi = all_valleys[i][1]
                    stage = 2
            elif stage == 2:
                ### Is RSI still rising?
                if all_valleys[i][1] < prev_rsi:
                    if all_valleys[i][1] < 30:
                        stage = 1
                        starti = i
                else:
                    stage = 3
                    j = i
                prev_rsi = all_valleys[i][1]
            elif stage == 3:
                ### RSI is falling again
                if all_valleys[i][1] < prev_rsi:
                    if all_valleys[i][1] < 30:
                        stage = 1
                        starti = i
                else:
                    stage = 4
                prev_rsi = all_valleys[i][1]
            elif stage > 3:
                ### RSI is breaking out
                if all_valleys[i][1] > prev_rsi:
                    rsiDate = "{}{}{}".format(all_valleys[j][3][:4], all_valleys[j][3][5:7], all_valleys[j][3][8:10])
                    if dfDate <= rsiDate:
                        plotFlag = True
                        print(dfDate, rsiDate)
                stage = 0
            if stage == 6:
                #starti = all_valleys[starti - 1][0] if starti else all_valleys[0][0]
                endi = all_valleys[i][0]
                #print(all_valleys[starti])
                #print(all_valleys[i])
                #plotGraph(plt, dates[starti:endi], prices[starti:endi], rsis[starti:endi])
                if re.match(r'2023-05', all_valleys[j][3]):
                    plotFlag = True
                stage = 0


        ### Plot/Save the graph
        if args.symbol and plotFlag:
            plt.plot(dates, prices, rsis)
            plt.axhline(y=30, color="red", linestyle="--")
            plt.show()
        elif plotFlag and not args.test:
            if createDirFlag:
                os.makedirs(plotsDir)
                createDirFlag = False
            plt.plot(dates, prices, rsis)
            plt.axhline(y=30, color="red", linestyle="--")
            filename = "{}/{}.pdf".format(plotsDir, symbol)
            plt.savefig(filename)
            plt.close()

    if not args.symbol:
        outfile = "{}/StockWinners_{}.txt".format(stocksRoot, dirdate)
        with open(outfile, 'w') as f:
            for line in output:
                f.write("{}\n".format(line))

# # "/Users/Jonathan Peyser/AppData/Local/Programs/Python/Python38/python.exe" -u "\Users\Jonathan Peyser\stocks_wd\analysis.py" -d 20230205

