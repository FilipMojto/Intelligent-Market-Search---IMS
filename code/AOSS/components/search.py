import rapidfuzz.fuzz as fuzz
from typing import List, Literal
from dataclasses import dataclass
import polars.exceptions

import os, sys

cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cur_dir)

parent_dir = os.path.abspath(os.path.join(cur_dir, "..", '..'))
sys.path.append(parent_dir)



from AOSS.structure.shopping import MarketPlace, ProductCategory, ProductWeightUnit
from AOSS.other.utils import get_mapped_category
from config_paths import *




# class ProductMatcher:
    
#     """
#         This class serves for an efficient product search by providing match rates.

#         An instance of this class keeps a buffer containing mappings of registered products to the currently searched
#         product name. This buffer is cleared every time a new name is searched.

#         Attributes:
#             __market_hub - a market base containing markets from which the product is searched
#             __markets - the mentioned buffer
#             __buffer_limit - the limit at which the buffer is cleared using adjust_at() method

#         Methods:

#             a) match()

#             b) clear_at()

#             c) __clear_buffer()
#     """

#     def __init__(self, market_hub: MarketHub, buffer_limit: int = 1000) -> None:

#         """
#             Class Constructor which initializes everything necessary.
#         """

#         self.__market_hub = market_hub
#         self.__buffer_limit = buffer_limit
#         self.__matches: List[tuple[RegisteredProduct, float]] = []
    
#     def clear_at(self, matches: int = None):
        
#         """
#             This method serves both as a getter or a setter for reading or modifying the buffer limit.
#         """

#         if matches is not None:
#             self.__buffer_limit = matches
        
#         return self.clear_at


#     def match(self, text: str, category: ProductCategory = None, min_match: float = 0, limit: int = 5, for_each: bool = False,
#               markets: tuple = None):
        
#         # Firstly we check whether the provided parameters fulfill several constraints 
#         if not 0<=min_match<=1:
#             raise ValueError("Minimal match must be a float in interval <0, 1>.")
        
#         if limit >= self.__buffer_limit:
#             raise ValueError("Provided limit value higher than buffer limit!")
        
#         # Now we process the name string to contain only unicode lowercase characters and clear the buffer
#         processed_text = unidecode(text.lower())
#         self.__matches.clear()
        
        
#         # At this point we can start comparing 
#         with open(file=PRODUCT_FILE['path'], mode='r', encoding='utf-8') as file:    
#             line = file.readline()

#             if line is not None and PRODUCT_FILE['header']:
#                 line = file.readline()
        
#             while(line):
#                 product = Product.to_obj(row=line)

#                 match = fuzz.token_sort_ratio(unidecode(product.name.lower()), processed_text)

#                 if match >= min_match:
#                     self.__matches.append( (product, match) )
                
#                 #if len(self.__matches) > self.__buffer_limit:
#                     #self.__clear_buffer(category=category.name.lower(), limit=limit, for_each=for_each)

                    
#                 line = file.readline()
            
#         self.__clear_buffer(category=category, limit=limit, for_each=for_each)
#         return self.__matches


#     def __clear_buffer(self, limit: int, for_each: bool, category: str = None, markets: tuple = None) -> bool:
        
#         # First, we sort matches in desceding order of the match rate, then we will filter only the results of
#         # the required category
#         self.__matches.sort(key=lambda pair: pair[1], reverse=True)
        
#         if markets is not None:
#             self.__matches = [(product, ratio) for product, ratio in self.__matches if product.market_ID() in markets]

#         if category is not None:
#             self.__matches = [(product, ratio) for product, ratio in self.__matches if product.category == category]

#         # here we will attempt to restrict matches to the limit so that each market gets its top matches
#         # len(self.__matches) <= len(self.__market_hub.markets()) * limit
#         if for_each:
#             matches_count: Dict[int, int] = {}
#             matches = []

#             for market in self.__market_hub.markets():
#                 matches_count[market.ID()] = 0


#             for match in self.__matches:
#                 if matches_count[match[0].market_ID] < limit:
#                     matches_count[match[0].market_ID] += 1
#                     matches.append(match)

#                 if len(matches) == limit * len(self.__market_hub.markets()):
#                     break
            
#             self.__matches = matches
#             assert(len(self.__matches) <= len(self.__market_hub.markets()) * limit)
            

#         else:
#             # we restrict match buffer to the required limit
#             self.__matches = self.__matches[:limit]

    

class ProductMatcher:
    """
        
    """

    @dataclass
    class Match:

        product_ID: int
        ratio: float
        price: float
        market_ID: int

        def __str__(self):

            return {f"{{product_ID: {self.product_ID}, match: {self.ratio}, price: {self.price}, market_ID: {self.market_ID} }}"}




    def __init__(self, market_hub: MarketPlace) -> None:
        
        self.__market_hub = market_hub
        self.__markets = self.__market_hub.markets()
        
        if len(self.__markets) == 0:
            raise ValueError("Provided market hub contains no markets!")

        #market_hub.load_products()
        self.__product_df = market_hub.product_df()
        self.__subset = None

        for market in self.__markets:
            if not self.__product_df.filter(self.__product_df['market_ID'] == market.ID()).is_empty():
                break
        else:
            raise ValueError("Provided markets contain no data!")
        
        
    

    def __extract_cols(self, row, text, sort: bool = False):

        if not sort:
            return (row[PRODUCT_FILE['columns']['ID']['index']], fuzz.token_set_ratio(row[
                PRODUCT_FILE['columns']['normalized_name']['index']], text), row[PRODUCT_FILE['columns']['price']['index']],
            row[PRODUCT_FILE['columns']['market_ID']['index']])
        else:
            return (row[PRODUCT_FILE['columns']['ID']['index']], fuzz.token_sort_ratio(row[
                PRODUCT_FILE['columns']['normalized_name']['index']], text), row[PRODUCT_FILE['columns']['price']['index']],
            row[PRODUCT_FILE['columns']['market_ID']['index']])

 
    def set_subset(self, market_ID: int):
        self.__subset = self.__product_df.filter(self.__product_df['market_ID'] == market_ID)

    # Define a function to apply your mapping logic
    def filter_category(self, row, category: ProductCategory):
    
        mapped_category = get_mapped_category(query_string_ID=row,
                                            mappings_file=CATEGORY_MAP_FILE['path'],
                                            categories_file=CATEGORY_FILE['path'])
        return mapped_category == category.name

    def match(self, text: str, markets: tuple[int] = None, category: ProductCategory = None, categorization: Literal['ManualMapping', 'TM-based Mapping' ] = 'ManualMapping', limit: int = 10,
              min_match: float = 0, for_each: bool = False, sort_words: bool = False, use_subset: bool = False,
              weight_unit: ProductWeightUnit = ProductWeightUnit.NONE, weight: float = -1):
        
        
        """
            Match products based on the specified criteria.

            Parameters:
            - text (str): The text to match against.
            - markets (tuple[int], optional): A tuple of market IDs to restrict the search to.
            - category (ProductCategory, optional): The product category to filter by.
            - limit (int, optional): The maximum number of matches to return.
            - min_match (float, optional): The minimum match ratio required.
            - for_each (bool, optional): If True, apply the limit separately for each market.
            - sort_words (bool, optional): If True, it sorts words first and then finds match ratio
            - use_subset (bool, optional): If True, custom subset set by set_subset() method is used

            Returns:
            - List of matches based on the specified criteria.
        """
        

        if limit < 0:
            raise ValueError("Invalid limit value! Must be positive.")
        
        if not 0<=min_match<=100:
            raise ValueError("Invalid minimal match value! Must be a float within 0 to 100.")

        if markets is not None and markets:
            for market in markets:
                for hub_market in self.__markets:
                    if market == hub_market.ID():
                        break
                else:
                    raise ValueError("One of filtered market IDs not found in market hub!")


        df = None

        if use_subset and self.__subset is not None:
            df = self.__subset
        else:
            df = self.__product_df
        
        if df.is_empty():
            return []
        
        # filtering products belonging to a subset of markets
        if markets is not None and markets:
            df = df.filter(self.__product_df['market_ID'].is_in(markets))

        if df.is_empty():
            return []
        # weight_str = str(weight)

        if weight_unit != ProductWeightUnit.NONE and weight > 0:
            df = df.filter(
                (polars.col('weight_unit') == weight_unit.name) & (polars.col('weight') == weight)
            )

        if df.is_empty():
            return []

        # filtering products by their category
        if category is not None:
            if categorization == 'ManualMapping':
                df = df.filter(polars.col("query_string_ID").apply(lambda row: self.filter_category(row, category=category)))
                
                # df = df.filter(get_mapped_category(query_string_ID=df['query_string_ID'],
                #                                    mappings_file=CATEGORY_MAP_FILE['path'],
                #                                    categories_file=CATEGORY_FILE['path']) == category.name)
            elif categorization == 'TM-based Mapping':    
                df = df.filter(df['category'] == category.name)

        if df.is_empty():
            return []

        try:    
            df = df.apply(lambda row: self.__extract_cols(row, text, sort=sort_words))
        except polars.exceptions.ComputeError:
            return

        # [product_ID, match, price, market_ID]
        # here we convert necessary columns into python lists and then zip them into a list of tuples
        results: List[tuple[int, float, float, int]] = list(zip(df['column_0'].to_list(), df['column_1'].to_list(),
                        df['column_2'].to_list(), df['column_3'].to_list()))

        # Create a list of Match objects
        matches = [self.Match(*t) for t in results]

        if min_match > 0:
            matches = [_match for _match in matches if _match.ratio >= min_match]


      #  matches.sort(key=lambda _match: (-_match.match, _match.price))
        
        
        if not for_each:
           #la = sorted(matches, key=lambda _match: (-_match.match, _match.price))
            return sorted(matches, key=lambda _match: (-_match.ratio, _match.price))[:limit]

            #return matches[:limit]
        else:
            composed_matches: List[self.Match] = []
            _markets = []
            
            if markets is not None and markets:
                for market_i in markets:
                    _markets.append(self.__market_hub.market(identifier=market_i))
            else:
                _markets = self.__markets

            for market in _markets:
                composed_matches.extend(
                    [match for match in sorted(matches, key=lambda m: (-m.ratio, m.price)) if match.market_ID == market.ID()][:limit]
                )
                
                #composed_matches.extend([_match for _match in matches if _match.market_ID == market.ID()][:limit])

            return composed_matches          




                   
