from binance.client import Client
from flask import current_app

import time
import datetime
import heapq

CLOSE_RANGE = 20

api_key = current_app.config['API_KEY']
api_secret = current_app.config['API_SECRET']

client = Client(api_key, api_secret)


def sell(price, quantity):
    order = client.create_order(
        symbol='BTCUSDT',
        side=Client.SIDE_SELL,
        type=Client.ORDER_TYPE_LIMIT,
        price=price,
        quantity=quantity,
        timeInForce='GTC',
        recvWindow=2000)
    return order


def buy(price, quantity):
    order = client.create_order(
        symbol='BTCUSDT',
        side=Client.SIDE_BUY,
        type=Client.ORDER_TYPE_LIMIT,
        price=price,
        quantity=quantity,
        timeInForce='GTC',
        recvWindow=2000)
    return order


def get_price_range():
    # klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, )
    timestamp = round(datetime.datetime.now().timestamp() * 1000)
    klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, "20 min ago UTC")

    sum = 0
    high_list = []
    for i in range(len(klines)):
        kline = klines[i]
        high = float(kline[2])
        low = float(kline[3])
        sum += high - low

        high_list.append(high)
    avg = sum / len(klines)
    second_high = heapq.nlargest(2, high_list)[1]
    start_price = second_high
    end_price = second_high - avg

    if start_price - end_price < CLOSE_RANGE:
        start_price = end_price + CLOSE_RANGE

    return round(start_price, 2), round(end_price, 2)

# def get_price_range():
#     depth = client.get_order_book(symbol='BTCUSDT')
#     asks = depth['asks']
#     bids = depth['bids']
#
#     sum = 0
#     high_list = []
#     for i in range(len(klines)):
#         kline = klines[i]
#         high = float(kline[2])
#         low = float(kline[3])
#         sum += high - low
#
#         high_list.append(high)
#     avg = sum / len(klines)
#     second_high = heapq.nlargest(2, high_list)[1]
#     start_price = second_high
#     end_price = second_high - avg
#
#     return round(start_price, 2), round(end_price, 2)


def test():
    upper = 7401
    lower = 7400
    quantity = 0.003

    # start_price, end_price = get_price_range()

    range_buy_sell(upper, lower, quantity)

    tmp = 3


def range_buy_sell(upper, lower, quantity):
    # bought/sold
    # status = 'bought'
    # round_finished = False



    status = 'sold'
    round_finished = True

    unfinish_count = 0
    loop_count = 0

    urgent_close = False

    # get init range
    upper, lower = get_price_range()

    while (True):
        try:
            depth = client.get_order_book(symbol='BTCUSDT')
            bids = depth['bids']
            asks = depth['asks']
            one_bid = float(bids[0][0])
            one_ask = float(asks[0][0])

            if one_ask >= upper and status == 'bought':
                # sell
                order = sell(upper, quantity)
                round_finished = True
                status = 'sold'
                current_app.logger.info('Sold %s' % order)
                current_app.logger.info(
                    '******************************************************** Upper: %s, lower: %s, earned: %s' % (
                    str(upper), str(lower), str((upper - lower) * quantity)))
            elif one_bid <= lower and status == 'sold':
                # buy
                order = buy(lower, quantity)
                round_finished = False
                status = 'bought'
                urgent_close = False
                current_app.logger.info('Bought %s' % order)

            if status == 'bought':
                current_app.logger.info('selling %s, (bid %s, upper %s), loop count: %s, bid: %s, ask: %s --> upper: %s, lower: %s' % (
                    '(urgent close)' if urgent_close else '', one_bid, upper, loop_count, one_bid, one_ask, upper, lower))
            elif status == 'sold':
                current_app.logger.info('buying, (ask %s, lower %s), loop count: %s, bid: %s, ask: %s --> upper: %s, lower: %s' % (
                    one_ask, lower, loop_count, one_bid, one_ask, upper, lower))

            loop_count += 1
            unfinish_count += 1

            if loop_count % 30 == 0 and round_finished:
                upper, lower = get_price_range()
                unfinish_count = 1
                current_app.logger.info(
                    '------------------------------ price updated, upper %s, lower %s' % (upper, lower))

            if unfinish_count % 120 == 0:
                if upper - lower >= CLOSE_RANGE:
                    upper = lower + CLOSE_RANGE
                urgent_close = True
                current_app.logger.info('wait too long, change upper to upper %s, lower %s' % (upper, lower))

            time.sleep(5)
        except Exception as ex:
            current_app.logger.error('error happen: %s' % ex)

    # place a test market buy order, to place an actual order use the create_order function
    # order = client.create_test_order(
    #     symbol='BTCUSDT',
    #     side=Client.SIDE_SELL,
    #     type=Client.ORDER_TYPE_LIMIT,
    #     price=7030,
    #     quantity=0.003,
    #     timeInForce='GTC',
    #     recvWindow=3000
    #     )

    # order = buy(buy_price, buy_quantity)

    # print(order)

    # print(depth)
    # get all symbol prices
    # prices = client.get_all_tickers()

    # print(prices)


if __name__ == '__main__':
    print(round(22.123, 2))
    # test()


# withdraw 100 ETH
# check docs for assumptions around withdrawals
# from binance.exceptions import BinanceAPIException, BinanceWithdrawException
#
# try:
#     result = client.withdraw(
#         asset='ETH',
#         address='<eth_address>',
#         amount=100)
# except BinanceAPIException as e:
#     print(e)
# except BinanceWithdrawException as e:
#     print(e)
# else:
#     print("Success")
#
# # fetch list of withdrawals
# withdraws = client.get_withdraw_history()
#
# # fetch list of ETH withdrawals
# eth_withdraws = client.get_withdraw_history(asset='ETH')
#
# # get a deposit address for BTC
# address = client.get_deposit_address(asset='BTC')


# start aggregated trade websocket for BNBBTC
def process_message(msg):
    print("message type: {}".format(msg['e']))
    print(msg)
    # do something

# from binance.websockets import BinanceSocketManager
#
# bm = BinanceSocketManager(client)
# bm.start_aggtrade_socket('BNBBTC', process_message)
# bm.start()
#
# # get historical kline data from any date range
#
# # fetch 1 minute klines for the last day up until now
# klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
#
# # fetch 30 minute klines for the last month of 2017
# klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_30MINUTE, "1 Dec, 2017", "1 Jan, 2018")
#
# # fetch weekly klines since it listed
# klines = client.get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")
