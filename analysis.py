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
    parser.add_argument('-f', '--force', action='store_true')
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
    isodate = "{}-{}-{}".format(args.date[:4], args.date[4:6], args.date[6:8])
    pDate = date.fromisoformat(isodate)
    ### Default is from start of month
    if not args.window:
        args.window = 30
    startDate = pDate - timedelta(days = int(args.window))
    startdate = startDate.strftime('%Y%m%d')

    if args.symbol:
        dir_list = ["{}.csv".format(args.symbol)]
    else:
        ### Check if plot directory exists
        createDirFlag = False
        plotsDir = "{}/{}/{}".format(stocksRoot, dirdate, 'Plots')
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
        # p = np.array(rsis)
        # peaks, props = find_peaks(p, height=0)
        
        # rsi_peaks = []
        # prev = -1
        # asc = False
        # for i in range(len(rsis)):
        #     if i in peaks:
        #         if prev == -1:
        #             prev = i
        #         elif rsis[i] >= rsis[prev]:
        #             prev = i
        #             asc = True
        #         else:
        #             if asc == True:
        #                 #rsi_peaks.append((prev, rsis[prev], 'P'))
        #                 rsi_peaks.append((prev, rsis[prev], 'P', dates[prev]))
        #             prev = i
        #             asc = False
        
        v = np.array(rsis) * -1
        valleys, props = find_peaks(v, height=(None, 0))
        props_valleys = props['peak_heights'] * -1
        #if args.debug:
        #    print(props_valleys, len(props_valleys))
        
        if props_valleys.size == 0:
            continue
        all_valleys = []
        for i in valleys:
            all_valleys.append((i, rsis[i], 'V', dates[i]))

        if args.debug:
            for r in all_valleys:
                print("{} {} {}".format(r[3], prices[r[0]], r[1]))

        AscFlag = False
        plotFlag = False
        flag = False
        hline = 30
        coords = [0, 0]
        for i in range(len(all_valleys) - 1):
            if (all_valleys[i][1] <= 30.0 and
                all_valleys[i + 1][1] > 30.0
                ):
                flag = True
            elif flag == True:
                if (all_valleys[i][1] < all_valleys[i + 1][1] and
                    prices[all_valleys[i][0]] >  prices[all_valleys[i + 1][0]]
                    ):
                    j = savej = i + 1
                    j += 1
                    while(j < len(all_valleys)):
                        if (all_valleys[i + 1][1] < all_valleys[j][1] and
                            prices[all_valleys[i + 1][0]] >  prices[all_valleys[j][0]]):
                            savej = j
                            j += 1
                        else:
                            break
                    ddate = re.sub('-', '', all_valleys[i][3])
                    if ddate > startdate:
                        output.append("Symbol:           {}".format(symbol))
                        output.append("Dates:            {} -> {}".format(dates[all_valleys[i][0]], dates[all_valleys[savej][0]]))
                        output.append("Ascending RSI:    {} -> {}".format(round(rsis[all_valleys[i][0]], 6), round(rsis[all_valleys[savej][0]], 6)))
                        output.append("Descending Price: {} -> {}".format(prices[all_valleys[i][0]], prices[all_valleys[savej][0]]))
                        output.append('---')
                        for j in range(len(output) - 5, len(output)):
                            print(output[j])
                        plotFlag = True
                        coords = [all_valleys[i][0], all_valleys[savej][0]]
                flag = False
        if plotFlag:
            AscFlag = True

        ### Look for ascending price and descending RSI
        for i in range(len(all_valleys) - 1):
            if (all_valleys[i][1] >= 70.0 and
                all_valleys[i + 1][1] < 70.0
                ):
                flag = True
            elif flag == True:
                if (all_valleys[i][1] > all_valleys[i + 1][1] and
                    prices[all_valleys[i][0]] < prices[all_valleys[i + 1][0]]
                    ):
                    j = savej = i + 1
                    j += 1
                    while(j < len(all_valleys)):
                        if (all_valleys[i + 1][1] > all_valleys[j][1] and
                            prices[all_valleys[i + 1][0]] < prices[all_valleys[j][0]]):
                            savej = j
                            j += 1
                        else:
                            break
                    ddate = re.sub('-', '', all_valleys[i][3])
                    if ddate > startdate:
                        output.append("Symbol:           {}".format(symbol))
                        output.append("Dates:            {} -> {}".format(dates[all_valleys[i][0]], dates[all_valleys[savej][0]]))
                        output.append("Descending RSI:    {} -> {}".format(round(rsis[all_valleys[i][0]], 6), round(rsis[all_valleys[savej][0]], 6)))
                        output.append("Ascending Price: {} -> {}".format(prices[all_valleys[i][0]], prices[all_valleys[savej][0]]))
                        output.append('---')
                        for j in range(len(output) - 5, len(output)):
                            print(output[j])
                        plotFlag = True
                        hline = 70
                        coords = [all_valleys[i][0], all_valleys[savej][0]]
                flag = False

        
        ### Plot/Save the graph
        if args.symbol and (plotFlag or args.force):
            plt.plot(dates, prices, rsis)
            p1, p2 = coords
            if p1 and p2:
                plt.plot((p1, p2), (rsis[p1], rsis[p2]), 'b-')
                plt.plot((p1, p2), (prices[p1], prices[p2]), 'r-')
            plt.axhline(y=hline, color="red", linestyle="--")
            plt.show()
        elif plotFlag and not args.test:
            if createDirFlag:
                os.makedirs(plotsDir)
                createDirFlag = False
            plt.plot(dates, prices, rsis)
            p1, p2 = coords
            plt.plot((p1, p2), (rsis[p1], rsis[p2]), 'b-')
            plt.plot((p1, p2), (prices[p1], prices[p2]), 'r-')
            plt.axhline(y=hline, color="red", linestyle="--")
            filename = "{}/{}.pdf".format(plotsDir, symbol)
            plt.savefig(filename)
            plt.close()

    if not args.symbol:
        outfile = "{}/StockWinners_{}.txt".format(stocksRoot, dirdate)
        with open(outfile, 'w') as f:
            for line in output:
                f.write("{}\n".format(line))

# # "/Users/Jonathan Peyser/AppData/Local/Programs/Python/Python38/python.exe" -u "\Users\Jonathan Peyser\stocks_wd\analysis.py" -d 20230205

