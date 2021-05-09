def given_data_is_long_enough(time_horizon, stocks, file_mode_on):
    if not file_mode_on:
        return True
    for stock in stocks:
        if len(stock.pricing_info) >= time_horizon:
            return True
        else:
            return False
    return False

def apply_stock_splits(adj_close, stock_splits):
    if stock_splits != 0:
        return adj_close * (1 / (1 * stock_splits))
    else:
        return adj_close