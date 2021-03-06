import pickle
import os
from br.bridge import Bridge
from pathlib import Path
import random
from parameters import *

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

class Pruner():

    def __init__(self):
        self.bridge=Bridge()

    def reprepare(self):
        '''
        rewrites all data
        :return:
        '''
        self.prune_and_save(overwrite=True)
        self.get_length_for_all_pairs(load=False,save=True)


    def prune_and_save(self, overwrite=False):

        '''
            Pruned value:

            "0.01634790",  # Open
            "0.80000000",  # High
            "0.01575800",  # Low
            "0.01577100",  # Close
            "148976.11427815",  # Volume
            "2434.19055334",  # Quote asset volume
            308,  # Number of trades
            "1756.87402397",  # Taker buy base asset volume
            "28.46694368",  # Taker buy quote asset volume
        '''
        for symbol_pair in self.bridge.get_btc_symbols():
            filename = self.bridge.get_file_name(symbol_pair)[:-4] + " pruned.pkl"
            print(filename)

            if os.path.isfile(filename) and overwrite == False:
                print('pruned file already exists, no overwrite')
            else:
                with open(self.bridge.get_file_name(symbol_pair),'rb') as pickle_file:
                    print("starting pruning "+symbol_pair)
                    klines_list=pickle.load(pickle_file)
                    pruned_klines_list=[]

                    for kline in klines_list[symbol_pair]:
                        kline.pop(0)
                        kline.pop(5)
                        kline.pop(-1)
                        kline=list(map(float,kline))
                        pruned_klines_list.append(kline)

                    with open(filename,'wb') as pickle_save:
                        pickle.dump(pruned_klines_list,pickle_save)


    def get_length_for_all_pairs(self, load=True, save=False):
        '''
        128 tickers form up one unit of operation.
        shuffled and fed into the network by batches

        The dataset has many pairs of trades. To sample unbiasedly, we need to find out the
        length of each pair of trade and produce the starting point of the 128-slice.

        Can such slice be produced at runtime?
        Maybe, why not?
        :return:
        '''

        if "pr" in str(Path.cwd()):
            file_path=Path("pairs_and_lengths.pkl")
        else:
            file_path=Path("pr/pairs_and_lengths.pkl")
        if file_path.exists() and load:
            with file_path.open('rb') as pickle_file:
                return pickle.load(pickle_file)
        else:
            # keys are the symbol pairs, values is (number_of_ticks, path) tuple
            paired_lengths = {}
            if "pr" in str(Path.cwd()):
                data_dir_path=Path("../data")
            else:
                data_dir_path=Path("data")
            pruned_list=list(data_dir_path.glob("*pruned.pkl"))
            for pruned in pruned_list:
                with pruned.open("rb") as pickle_file:
                    klines=pickle.load(pickle_file)
                    number_of_ticks=len(klines)
                    if number_of_ticks<time_length+1:
                        print('the length of '+str(pruned)+" is too small.")
                    else:
                        filename_splitted=str(pruned).split()
                        if "pr" in str(Path.cwd()):
                            # if "pr" is in the path, then pruned will look like "../data/abc.data"
                            # this line makes it so that the path looks like "data/abc.data"
                            paired_lengths[filename_splitted[1]] = (number_of_ticks, Path(*pruned.parts[2:]))
                        else:
                            paired_lengths[filename_splitted[1]] = (number_of_ticks, pruned)
            if save:
                with file_path.open('wb') as pickle_file:
                    pickle.dump(paired_lengths,pickle_file)
        return paired_lengths

    def get_ticker_marker(self,time_length,batch_size):
        '''
        return batch_size number of tuple (ticker starting position, file_path)

        :param time_length:
        :param batch_size:
        :return:
        '''
        if "pr" in str(Path.cwd()):
            pairs_lengths_path=Path("../pr/pairs_and_lengths.pkl")
        else:
            pairs_lengths_path=Path("pr/pairs_and_lengths.pkl")
        with pairs_lengths_path.open('rb') as lengths_file:
            paired_lengths=pickle.load(lengths_file)

        # first we sample a pair, by weights decided by lengths
        # then we sample a starting position, evenly

        number_of_tickers=[value[0] for value in paired_lengths.values()]
        count_path_tuples=list(paired_lengths.values())

        sampled_count_path_tuples = random.choices(population=count_path_tuples,weights=number_of_tickers, k=batch_size)
        double_sampled_count_path_tuples=[]

        for count_path_tuple in sampled_count_path_tuples:
            start_mark=random.randint(0,count_path_tuple[0]-time_length-1)
            double_sampled_count_path_tuples.append((start_mark,count_path_tuple[1]))

        return double_sampled_count_path_tuples

    def get_batch(self,time_length,batch_size):
        '''
        Create a batch of x and y
        y is the close price at the next time step

        opening file costs time. Consider, if memory permits, caching the read/write

        :param time_length:
        :param batch_size:
        :return:
        '''
        ticker_marker=self.get_ticker_marker(time_length,batch_size)
        x=[]
        y=[]
        for marker, path in ticker_marker:
            with path.open("rb") as pickle_file:
                klines=pickle.load(pickle_file)
                x.append(klines[marker:marker+time_length])
                y.append([kline[3] for kline in klines[marker+1:marker+time_length+1]])

        return (x,y)

if __name__=="__main__":
    pruner=Pruner()
    pruner.reprepare()
    hello=pruner.get_batch(time_length,batch_size)
    print("done")