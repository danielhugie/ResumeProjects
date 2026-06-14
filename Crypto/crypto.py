import csv
import json
import os
import time
from datetime import datetime, timezone
import requests


class CryptoTradingProject:
    """
    For my final project for I chose cryptocurrency trading.
    Here is what this program does:
    1. First, it downloads daily crypto data from the CoinGecko JSON API.
    2. Then it saves each cryptocurrency into its own CSV file.
    3. Appends only new rows so old data is not overwritten.
    4. Runs two trading strategies: Simple Moving Average crossover and Mean Reversion
    5. Saves the latest analysis in a results.json file.
    6. Prints a buy/sell/hold message for the most recent day.
    """

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.results_path = os.path.join(self.base_dir, "results.json")
        self.api_key = os.getenv("COINGECKO_API_KEY", "")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.vs_currency = "usd"
        self.days = 365

        # The 6 coins that I chose
        self.coins = {
            "bitcoin": "Bitcoin",
            "ethereum": "Ethereum",
            "litecoin": "Litecoin",
            "ripple": "Ripple",
            "bitcoin-cash": "Bitcoin Cash",
            "eos": "EOS",
        }

    def get_headers(self):
        headers = {"accept": "application/json"}

        # Header for demo keys
        if self.api_key != "":
            headers["x-cg-demo-api-key"] = self.api_key
        return headers

    def fetch_coin_data(self, coin_id):
        """Get 365 days of daily data for one coin."""
        url = self.base_url + "/coins/" + coin_id + "/market_chart"
        parameters = {
            "vs_currency": self.vs_currency,
            "days": self.days,
            "interval": "daily",
        }
        
        response = requests.get(url, headers=self.get_headers(), params=parameters, timeout=30)
        response.raise_for_status()
        data = response.json()
        rows = []
        prices = data.get("prices", [])
        market_caps = data.get("market_caps", [])
        total_volumes = data.get("total_volumes", [])
        length = min(len(prices), len(market_caps), len(total_volumes))

        for i in range(length):
            timestamp = prices[i][0]
            price = prices[i][1]
            market_cap = market_caps[i][1]
            total_volume = total_volumes[i][1]

            #I was having issues with my date time so I had ChatGPT create this date_string variable
            date_string = datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime("%Y-%m-%d")

            rows.append(
                {
                    "date": date_string,
                    "price": round(float(price), 2),
                    "market_cap": round(float(market_cap), 2),
                    "total_volume": round(float(total_volume), 2),
                }
            )
        return rows

    def get_csv_path(self, coin_id):
        return os.path.join(self.base_dir, coin_id + ".csv")

    def read_existing_dates(self, csv_path):
        existing_dates = set()
        if os.path.exists(csv_path):
            with open(csv_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    existing_dates.add(row["date"])
        return existing_dates

    def append_to_csv(self, coin_id, rows):
        """Append only new rows. Do not overwrite old rows."""
        csv_path = self.get_csv_path(coin_id)
        file_exists = os.path.exists(csv_path)
        existing_dates = self.read_existing_dates(csv_path)
        new_rows = []
        for i in rows:
            if i["date"] not in existing_dates:
                new_rows.append(i)

        with open(csv_path, "a", newline="", encoding="utf-8") as file:
            fieldnames = ["date", "price", "market_cap", "total_volume"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            for i in new_rows:
                writer.writerow(i)
        return len(new_rows)

    def load_prices_from_csv(self, coin_id):
        csv_path = self.get_csv_path(coin_id)
        rows = []
        with open(csv_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for i in reader:
                rows.append(
                    {
                        "date": i["date"],
                        "price": float(i["price"]),
                        "market_cap": float(i["market_cap"]),
                        "total_volume": float(i["total_volume"]),
                    }
                )

        def get_row_date(item):
            return item["date"]
        rows.sort(key=get_row_date)
        return rows

    def moving_average(self, prices, end_index, window):
        if end_index - window + 1 < 0:
            return None

        total = 0
        start_index = end_index - window + 1

        for i in range(start_index, end_index + 1):
            total = total + prices[i]
        return total / window

    def run_sma_strategy(self, rows, short_window=5, long_window=20):
        prices = []
        dates = []

        for i in rows:
            prices.append(i["price"])
            dates.append(i["date"])

        holding = False
        buy_price = 0
        first_buy = None
        total_profit = 0
        trades = []
        last_signal = "HODL"

        for i in range(long_window, len(prices)):
            short_ma_today = self.moving_average(prices, i, short_window)
            long_ma_today = self.moving_average(prices, i, long_window)
            short_ma_yesterday = self.moving_average(prices, i - 1, short_window)
            long_ma_yesterday = self.moving_average(prices, i - 1, long_window)

            if (short_ma_today is None or long_ma_today is None or short_ma_yesterday is None or long_ma_yesterday is None):
                continue

            buy_signal = short_ma_yesterday <= long_ma_yesterday and short_ma_today > long_ma_today
            sell_signal = short_ma_yesterday >= long_ma_yesterday and short_ma_today < long_ma_today

            if buy_signal and not holding:
                buy_price = prices[i]
                holding = True

                if first_buy is None:
                    first_buy = buy_price

                trades.append(
                    {
                        "action": "BUY",
                        "date": dates[i],
                        "price": buy_price,
                    }
                )

                if i == len(prices) - 1:
                    last_signal = "BUY"

            elif sell_signal and holding:
                sell_price = prices[i]
                profit = sell_price - buy_price
                total_profit = total_profit + profit
                holding = False

                trades.append(
                    {
                        "action": "SELL",
                        "date": dates[i],
                        "price": sell_price,
                        "profit": round(profit, 2),
                    }
                )

                if i == len(prices) - 1:
                    last_signal = "SELL"

            else:
                if i == len(prices) - 1:
                    last_signal = "HODL"

        percent_return = 0
        if first_buy is not None and first_buy != 0:
            percent_return = (total_profit / first_buy) * 100

        return {
            "strategy_name": "Simple Moving Average",
            "total_profit": round(total_profit, 2),
            "first_buy": round(first_buy, 2) if first_buy is not None else None,
            "percent_return": round(percent_return, 2),
            "completed_trades": self.count_completed_trades(trades),
            "last_signal": last_signal,
            "currently_holding": holding,
            "latest_price": round(prices[-1], 2),
            "latest_date": dates[-1],
        }

    def run_mean_reversion_strategy(self, rows, window=20, buy_threshold=0.95):
        prices = []
        dates = []

        for i in rows:
            prices.append(i["price"])
            dates.append(i["date"])

        holding = False
        buy_price = 0
        first_buy = None
        total_profit = 0
        trades = []
        last_signal = "HODL"

        for i in range(window, len(prices)):
            average_price = self.moving_average(prices, i, window)
            if average_price is None:
                continue

            buy_signal = prices[i] < average_price * buy_threshold
            sell_signal = prices[i] > average_price

            if buy_signal and not holding:
                buy_price = prices[i]
                holding = True

                if first_buy is None:
                    first_buy = buy_price

                trades.append(
                    {
                        "action": "BUY",
                        "date": dates[i],
                        "price": buy_price,
                    }
                )

                if i == len(prices) - 1:
                    last_signal = "BUY"

            elif sell_signal and holding:
                sell_price = prices[i]
                profit = sell_price - buy_price
                total_profit = total_profit + profit
                holding = False

                trades.append(
                    {
                        "action": "SELL",
                        "date": dates[i],
                        "price": sell_price,
                        "profit": round(profit, 2),
                    }
                )

                if i == len(prices) - 1:
                    last_signal = "SELL"

            else:
                if i == len(prices) - 1:
                    last_signal = "HODL"

        percent_return = 0
        if first_buy is not None and first_buy != 0:
            percent_return = (total_profit / first_buy) * 100

        return {
            "strategy_name": "Mean Reversion",
            "total_profit": round(total_profit, 2),
            "first_buy": round(first_buy, 2) if first_buy is not None else None,
            "percent_return": round(percent_return, 2),
            "completed_trades": self.count_completed_trades(trades),
            "last_signal": last_signal,
            "currently_holding": holding,
            "latest_price": round(prices[-1], 2),
            "latest_date": dates[-1],
        }

    def count_completed_trades(self, trades):
        buy_count = 0
        sell_count = 0

        for i in trades:
            if i["action"] == "BUY":
                buy_count = buy_count + 1
            elif i["action"] == "SELL":
                sell_count = sell_count + 1

        if buy_count < sell_count:
            return buy_count
        return sell_count

    def save_results(self, results):
        with open(self.results_path, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4)

    def build_signal_message(self, coin_name, strategy_result):
        signal = strategy_result["last_signal"]
        strategy_name = strategy_result["strategy_name"]

        if signal == "BUY":
            return "You should BUY " + coin_name + " today based on the " + strategy_name + " strategy."
        elif signal == "SELL":
            return "You should SELL " + coin_name + " today based on the " + strategy_name + " strategy."
        else:
            return "No buy or sell signal today for " + coin_name + " using the " + strategy_name + " strategy."

    def run(self):
        print("updating cryptocurrency CSV files")
        print()
        all_results = []
        best_result = None

        for coin_id in self.coins:
            coin_name = self.coins[coin_id]
            print("Getting data for", coin_name)

            try:
                rows = self.fetch_coin_data(coin_id)
                added_count = self.append_to_csv(coin_id, rows)
                csv_rows = self.load_prices_from_csv(coin_id)
                moving_average_result = self.run_sma_strategy(csv_rows)
                mean_reversion_result = self.run_mean_reversion_strategy(csv_rows)

                coin_result = {
                    "coin_id": coin_id,
                    "coin_name": coin_name,
                    "rows_in_csv": len(csv_rows),
                    "new_rows_added": added_count,
                    "latest_date": csv_rows[-1]["date"],
                    "latest_price": round(csv_rows[-1]["price"], 2),
                    "simple_moving_average": moving_average_result,
                    "mean_reversion": mean_reversion_result,
                    "messages": [
                        self.build_signal_message(coin_name, moving_average_result),
                        self.build_signal_message(coin_name, mean_reversion_result),
                    ],
                }

                all_results.append(coin_result)

                for i in [moving_average_result, mean_reversion_result]:
                    if best_result is None:
                        best_result = {
                            "coin_name": coin_name,
                            "strategy_name": i["strategy_name"],
                            "total_profit": i["total_profit"],
                            "percent_return": i["percent_return"],
                        }
                    elif i["total_profit"] > best_result["total_profit"]:
                        best_result = {
                            "coin_name": coin_name,
                            "strategy_name": i["strategy_name"],
                            "total_profit": i["total_profit"],
                            "percent_return": i["percent_return"],
                        }

                print("Rows in CSV:", len(csv_rows))
                print("New rows added:", added_count)
                print("Latest price:", round(csv_rows[-1]["price"], 2))
                print("SMA profit:", moving_average_result["total_profit"])
                print("Mean Reversion profit:", mean_reversion_result["total_profit"])
                print(moving_average_result["strategy_name"] + " signal:", moving_average_result["last_signal"])
                print(mean_reversion_result["strategy_name"] + " signal:", mean_reversion_result["last_signal"])
                for i in coin_result["messages"]:
                    print(i)
                print()

                # I added a small pause so that the API is not hit too quickly.
                time.sleep(12)

            except Exception as error:
                print("Error for", coin_name + ":", error)
                print()

        final_results = {
            #I had ChatGPT assist me with this run_time_utc key and value since I was having issues with it.    
            "run_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            
            "api_source": "CoinGecko API",
            "vs_currency": self.vs_currency,
            "days_requested": self.days,
            "best_overall_result": best_result,
            "coins": all_results,
        }

        self.save_results(final_results)

        print("results.json has been updated.")
        print()

        if best_result is not None:
            print("Most profitable result:")
            print(best_result["coin_name"], "-", best_result["strategy_name"])
            print("Total profit:", best_result["total_profit"])
            print("Percent return:", str(best_result["percent_return"]) + "%")


if __name__ == "__main__":
    project = CryptoTradingProject()
    project.run()
