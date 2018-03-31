import pickle
import os
from br.bridge import Bridge
from pathlib import Path

'''
    Kline return value:

    1499040000000,  # Open time
    "0.01634790",  # Open
    "0.80000000",  # High
    "0.01575800",  # Low
    "0.01577100",  # Close
    "148976.11427815",  # Volume
    1499644799999,  # Close time
    "2434.19055334",  # Quote asset volume
    308,  # Number of trades
    "1756.87402397",  # Taker buy base asset volume
    "28.46694368",  # Taker buy quote asset volume
    "17928899.62484339"  # Can be ignored

    Open, high, low and close are price values.
    Volume and number of trades are trade signatures.

    The network does not take open time as a part of the input.
    We need everything except for the open time, close time and the can be ignored.
'''


def prune_and_save(bridge, overwrite=False):
    for symbol_pair in bridge.get_btc_symbols():
        filename = bridge.get_file_name(symbol_pair)[:-4] + " pruned.pkl"
        print(filename)

        if os.path.isfile(filename) and overwrite == False:
            print('pruned file already exists, no overwrite')
        else:

            with open(bridge.get_file_name(symbol_pair),'rb') as pickle_file:
                print("starting pruning "+symbol_pair)
                klines_list=pickle.load(pickle_file)
                pruned_klines_list=[]

                for kline in klines_list[symbol_pair]:
                    kline.pop(0)
                    kline.pop(5)
                    kline.pop(-1)
                    pruned_klines_list.append(kline)

                with open(filename,'wb') as pickle_save:
                    pickle.dump(pruned_klines_list,pickle_save)


def get_length_for_all_pairs(save=True):
    '''
    128 tickers form up one unit of operation.
    shuffled and fed into the network by batches

    The dataset has many pairs of trades. To sample unbiasedly, we need to find out the
    length of each pair of trade and produce the starting point of the 128-slice.

    Can such slice be produced at runtime?
    Maybe, why not?
    :return:
    '''

    file_path=Path("pairs_and_lengths.pkl")
    if file_path.exists():
        with file_path.open('rb') as pickle_file:
            return pickle.load(pickle_file)
    else:
        paired_lengths = {}
        data_dir_path=Path("../data")
        pruned_list=list(data_dir_path.glob("*pruned.pkl"))
        for pruned in pruned_list:
            with pruned.open("rb") as pickle_file:
                klines=pickle.load(pickle_file)
                number_of_ticks=len(klines)
                if number_of_ticks<129:
                    print('the length of '+str(pruned)+" is too small.")
                else:
                    see=str(pruned).split()
                    paired_lengths[see[1]]=(number_of_ticks,pruned)
        with file_path.open('wb') as pickle_file:
            pickle.dump(paired_lengths,pickle_file)
    return paired_lengths

def get_ticker_marker():
    pairs_lengths_path=Path("pairs_and_lengths.pkl")
    with pairs_lengths_path.open('rb') as lengths_file:
        paired_lengths=pickle.load(lengths_file)

    # first we sample a pair, by weights decided by lengths
    # then we sample a starting position, evenly

bridge=Bridge()
#
# prune_and_save(bridge)
# print("done")

get_length_for_all_pairs()
