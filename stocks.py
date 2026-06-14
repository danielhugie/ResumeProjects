import os
import json

def read_prices(file_path):
    prices = []

    #This opens the file and reads all of the lines.
    file = open(file_path, "r", encoding="utf-8-sig")
    lines = file.readlines()

    #This turns each line into a float and rounds it to 2 decimals.
    for line in lines:
        value = float(line.strip())
        value = round(value, 2)
        prices.append(value)

    file.close()
    return prices

def moving_average(price_list, final_index):
    total = 0

    #This adds the previous 5 prices together.
    for i in range(final_index - 5, final_index):
        total += price_list[i]

    #Divide by 5 in order to get the moving average.
    average = total / 5
    return average

def meanReversionStrategy(prices):
    buy_price = 0.0
    first_buy = 0.0
    total_profit = 0.0
    stock = False

    #It needs starts at index 5 so that there are 5 earlier prices for the average.
    for i in range(5, len(prices)):
        current_price = prices[i]
        average_price = moving_average(prices, i)

        #Buy when the price goes below 98% of the 5 day average.
        if current_price < average_price * 0.98 and stock == False:
            buy_price = current_price
            stock = True

            if first_buy == 0.0:
                first_buy = buy_price

            print("buying at:      " + "{:.2f}".format(buy_price))

        #Sell when the price goes above 102% of the 5 day average.
        elif current_price > average_price * 1.02 and stock == True:
            sell_price = current_price
            trade_profit = sell_price - buy_price
            trade_profit = round(trade_profit, 2)
            total_profit += trade_profit
            total_profit = round(total_profit, 2)
            stock = False
            print("selling at:     " + "{:.2f}".format(sell_price))
            print("trade profit:   " + "{:.2f}".format(trade_profit))
            print()

        else:
            pass

    print("-----------------------")
    print("Total profit:   " + "{:.2f}".format(total_profit))
    print("First buy:      " + "{:.2f}".format(first_buy))

    if first_buy != 0:
        #This will calculate the final percent return.
        final_profit_percentage = (total_profit / first_buy) * 100
        final_profit_percentage = round(final_profit_percentage, 2)
        print("Percent return: " + "{:.2f}".format(final_profit_percentage) + "%")
    else:
        final_profit_percentage = 0.0
        print("Percent return: 0.00%")

    return round(total_profit, 2), round(final_profit_percentage, 2)

def simpleMovingAverageStrategy(prices):
    buy_price = 0.0
    first_buy = 0.0
    total_profit = 0.0
    stock = False

    #It needs starts at index 5 so that there are 5 earlier prices for the average.
    for i in range(5, len(prices)):
        current_price = prices[i]
        average_price = moving_average(prices, i)

        #Buy when the current price goes above the moving average.
        if current_price > average_price and stock == False:
            buy_price = current_price
            stock = True

            if first_buy == 0.0:
                first_buy = buy_price

            print("buying at:      " + "{:.2f}".format(buy_price))

        #Sell when the current price goes below the moving average.
        elif current_price < average_price and stock == True:
            sell_price = current_price
            trade_profit = sell_price - buy_price
            trade_profit = round(trade_profit, 2)
            total_profit += trade_profit
            total_profit = round(total_profit, 2)
            stock = False
            print("selling at:     " + "{:.2f}".format(sell_price))
            print("trade profit:   " + "{:.2f}".format(trade_profit))
            print()

        else:
            pass

    print("-----------------------")
    print("Total profit:   " + "{:.2f}".format(total_profit))
    print("First buy:      " + "{:.2f}".format(first_buy))

    #This will calculate the final percent return.
    if first_buy != 0:
        final_profit_percentage = (total_profit / first_buy) * 100
        final_profit_percentage = round(final_profit_percentage, 2)
        print("Percent return: " + "{:.2f}".format(final_profit_percentage) + "%")
    else:
        final_profit_percentage = 0.0
        print("Percent return: 0.00%")

    return round(total_profit, 2), round(final_profit_percentage, 2)

def saveResults(results):
    #Save the dictionary into a json file called results.json
    file = open("results.json", "w")
    json.dump(results, file, indent=4)
    file.close()

def main():
    #My 10 stock tickers that I have text files for.
    tickers = ["AAPL", "GOOG", "ADBE", "TSLA", "BA", "CMCSA", "CSCO", "CVX", "JPM", "V"]

    #A dictionary stores prices, profits, and return percentages.
    results = {}

    for ticker in tickers:
        file_path = os.path.join(os.path.dirname(__file__), ticker + ".txt")

        if os.path.exists(file_path) == False:
            print(ticker + ".txt was not found.")
            print()
        else:
            prices = read_prices(file_path)

            #Store the stock prices in the results dictionary.
            results[ticker + "_prices"] = prices
            print(ticker + " Simple Moving Average Strategy Output:")
            sma_profit, sma_returns = simpleMovingAverageStrategy(prices)
            print()
            print(ticker + " Mean Reversion Strategy Output:")
            mr_profit, mr_returns = meanReversionStrategy(prices)
            print()

            #Store the results from both strategies in the dictionary.
            results[ticker + "_sma_profit"] = round(sma_profit, 2)
            results[ticker + "_sma_returns"] = round(sma_returns, 2)
            results[ticker + "_mr_profit"] = round(mr_profit, 2)
            results[ticker + "_mr_returns"] = round(mr_returns, 2)
    saveResults(results)

main()
