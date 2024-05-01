
__AUTHOR__ = "Evenining Programmer"
__VERSION__ = "0.0.1"

from typing import List, Literal
from dataclasses import dataclass, field

from AOSS.structure.shopping import MarketPlace, RegisteredProduct, ProductCategory, ProductWeightUnit
from AOSS.components.search import ProductMatcher

# class MarketExplorer:

#     """
#         This class explores list of registered markets and attempts to recommend the best one according to a criterium (mostly price).
#         Each market gets allocated a buffer containing products that represent market's offer for the provided product list.

        
#     """

#     def __init__(self, markets: List[Market], matcher: ProductMatcher = None) -> None:
#         self.__markets = markets
#         self.__matcher = matcher
#         self.__product_lists: Dict[Market, List[Product]] = {}

#         for market in self.__markets:
#             self.__product_lists[market] = []

#         if self.__matcher is None:
#             self.__matcher = ProductMatcher(markets=self.__markets, adjust_at=500)
    
#     def product_lists(self):
#         return self.__product_lists



#     def explore(self, products: List[Product], min_match: float = 0.5):
#         if not 0<=min_match<=1:
#             raise ValueError("Minimal match must be float between 0 and 1.")
        
#         for value in self.__product_lists.values():
#             value.clear()


#         best_matches = []
#         processed_markets: List[int] = []

#         for product in products:

#             matches = self.__matcher.match(text=product.name, category=product.category, limit=5, for_each=True)
#             matches.sort(key=lambda pair: (pair[0].market_ID, -pair[1], pair[0].price))

#             for match in matches:
#                 if match[0].market_ID not in processed_markets:
#                     processed_markets.append(match[0].market_ID)
#                     best_matches.append(match)

#             processed_markets.clear()

#             for match in best_matches:
                
#                 for market, product_list in self.__product_lists.items():
#                     if market.ID() == match[0].market_ID:
#                         product_list.append(match[0])
#                         break
            
#             best_matches.clear()
        
#         for product_list in self.__product_lists.values():
#             assert(len(product_list) <= len(products))
    
#     def best_market(self) -> Dict[Market, List[Product]]:
#         min_sum = -1
#         results: Dict[Market, List[Product]] = {}

#         for market, product_list in self.__product_lists.items():
            
#             cur_sum = 0

#             for product in product_list:
#                 cur_sum += product.price


#             if cur_sum < min_sum:
#                 results.clear()
#                 results[market] = product_list
#                 min_sum = cur_sum
#             elif cur_sum == min_sum:
#                 results[market] = product_list
#             elif min_sum == -1:
#                 results[market] = product_list
#                 min_sum = cur_sum

            
#         return results


from typing import Dict


class MarketExplorer:

    @dataclass
    class ExplorationParams:
        """
            a) int - ID of the target product to which products in markets are sought,
                            explorations belonging to the same product will share this

            b) str - a specific name of the product for which the exploration will be carried out

            c) ProductCategory - this restricts exploration range to a specific category, if none
                                then no filter is applied

            d) int - required quantity of the product
        """

        target_id: int
        product_name: str
        product_category: ProductCategory = None
        categorization: Literal['Manual Mapping', 'TM-based Mapping'] = 'Manual Mapping'
        required_quantity: int = 0
        weight_unit: ProductWeightUnit = ProductWeightUnit.NONE
        weight: float = -1
            
    
    @dataclass
    class Exploration:
        """
            Exploration instance is a data class object which contains exploration results of
             a market and its products for the provided product list.

            Attributes
            ----------

            a) market_ID - ID of an explored market
            
            b) products - a list of found products in which each maps the best match results to
                            an element in product list

            c) total_expected_quantity - the expected amount of products that should be explored in the
                               market

            d) total_remaining_quantity

            e) total_price - total prices which is calculated as a sum of prices of all explored products


            Invariants
            ----------

            a) len(products) <= len(product_list)
            b) each product in products list should map a single product in product_list
            c) each product in products list has to contain unique target ID
        """

        market_ID: int

        # setting this only as [] would create a static variable, because of mutable list
        product_data: List[tuple[int, RegisteredProduct, float, int]] = field(default_factory=list)
        total_remaining_quantity: int = 0
        total_expected_quantity: int = 0
        total_price: float = 0


        def __post_init__(self):
            for product in self.product_data:
                expected_quantity = product[3]
                quantity_left = product[1].quantity_left
                self.total_remaining_quantity += (quantity_left if quantity_left <= expected_quantity else expected_quantity)
                self.total_price += product[1].price
                self.total_expected_quantity += product[3]
            
            if self.total_expected_quantity > 0:
                self.availability_rate = (self.total_remaining_quantity/self.total_expected_quantity) * 100
            else:
                self.availability_rate = 0
            
            try:
                self.general_metric = self.availability_rate / self.total_price
            except ZeroDivisionError:
                self.general_metric = 0
        
    
            

        def insert_product(self, target_ID: int, product: RegisteredProduct,
                           match_ratio: float, quantity):
            """
                Inserts a new product match to the exploration manually. Statistical attributes
                are automatically updated.
            """
            for existing_product in self.product_data:

                if existing_product[0] == target_ID:
                    raise ValueError("""Exploration instance cannot contain several products
                                     with the same target ID!""")
            
            self.product_data.append((target_ID, product, match_ratio, quantity))
            
            self.total_price += product.price
            self.total_expected_quantity += quantity
            self.total_remaining_quantity += (product.quantity_left if product.quantity_left <= quantity else quantity)
            self.availability_rate = (self.total_remaining_quantity/self.total_expected_quantity) * 100
            self.general_metric = self.availability_rate / self.total_price
      

        def replace_product(self, replacement: tuple[int, RegisteredProduct, float, int]):
            for index, data in enumerate(self.product_data):
                if data[0] == replacement[0]:
                    self.total_expected_quantity -= data[3]
                    self.total_price -= data[1].price
                    self.total_remaining_quantity -= data[3] if data[3] < data[1].quantity_left else data[1].quantity_left

                    self.total_expected_quantity += replacement[3]
                    self.total_price += replacement[1].price
                    self.total_remaining_quantity += replacement[3] if replacement[3] < replacement[1].quantity_left else replacement[1].quantity_left
                    
                    self.availability_rate = (self.total_remaining_quantity/self.total_expected_quantity) * 100
                    self.general_metric = self.availability_rate / self.total_price
                    self.product_data[index] = replacement
                    break
            else:
                raise ValueError("Invalid target ID!")
            

    """
         This class explores list of registered markets and attempts to recommend the best one according to a criterium (mostly price).
         Each market gets allocated a buffer containing products that represent market's offer for the provided product list.
    """

    
    def __init__(self, market_hub: MarketPlace, alternatives: int = 1) -> None:
        self.__market_hub = market_hub
        self.__matcher = ProductMatcher(market_hub=self.__market_hub)
     
        self.__markets = self.__market_hub.markets()
        self.__explorations: List[List[MarketExplorer.Exploration]] = []
        self.__alternatives = alternatives

        for index, market in enumerate(self.__markets):
            self.__explorations.append([])

            for _ in range(self.__alternatives):
                self.__explorations[index].append(MarketExplorer.Exploration(market_ID=market.ID(),
                                                                      total_price=0,
                                                                      product_data=[]))

    def get_limit(self):
        return self.__alternatives

    def set_limit(self, value: int):
        if self.__explorations:
            raise ValueError("Explorer contains some explorations! Remove them first.")

        self.__alternatives = value



    
    def clear_buffer(self):
        self.__explorations.clear()



    def expected_size(self, size: int):

        for i in range(len(self.__markets)):

            for g in range(self.__alternatives):
                expl = self.__explorations[i][g]
                expl.total_expected_quantity = size
                expl.availability_rate = expl.total_expected_quantity/len(expl.product_data)



    def remove_target(self, ID: int):

        for i in range(len(self.__markets)):

            for g in range(self.__alternatives):
                expl = self.__explorations[i][g]

                for product in expl.product_data:
                    if product[0] == ID:
                            expl.product_data.remove(product)
                            expl.total_expected_quantity -= product[3]
                            expl.total_price -= product[1].price
                            quatity_left = product[3] if product[3] <= product[1].quantity_left else product[1].quantity_left
                            expl.total_remaining_quantity -= quatity_left
                            break
                else:
                    raise ValueError("Provided ID not found!")     



    def get_explorations(self, metric: Literal['price', 'success_rate'] = 'price'):
        if metric == 'price' and len(self.__explorations) == len(self.__markets):
            self.__explorations.sort(key=lambda exploration : exploration[0].total_price)


        return self.__explorations

    def swap_expl_products(self, market_ID: int, expl_1_index: int, expl_2_name: str, product_index: int):
        exploration_list = None

        for expl in self.__explorations:
            if expl[0].market_ID == market_ID:
                exploration_list = expl
                break
        else:
            raise ValueError("Invalid market ID!")

        expl_1 = exploration_list[expl_1_index]
        expl_2  = None

        for expl in exploration_list:
            if expl.product_data[product_index][1].name == expl_2_name:
                expl_2 = expl
                break
        else:
            raise ValueError("Product name not found!")
        

        expl_1_product_data = expl_1.product_data[product_index]
        expl_2_product_data = expl_2.product_data[product_index]

        expl_1.replace_product(replacement=expl_2_product_data)
        expl_2.replace_product(replacement=expl_1_product_data)






    def explore(self, product_list: List[ExplorationParams]): # tuple[int, str, ProductCategory, int]]):
        """
            Parameters
            ---------
            
            1) product list - includes all explored products. Each product is represented via a tuple:

                    a) int - ID of the target product to which products in markets are sought,
                            explorations belonging to the same product will share this

                    b) str - a specific name of the product for which the exploration will be carried out

                    c) ProductCategory - this restricts exploration range to the specific category, if none
                                        then no filter is applied

                    d) int - required quantity of the product
            
            2) limit - specifies how many additional explorations will be executed
        """

        for index, market in enumerate(self.__markets):

            for params in product_list:

                match_record = self.__matcher.match(text=params.product_name,
                                                    markets=(market.ID(),),
                                                    category=params.product_category,
                                                    limit=self.__alternatives,
                                                    sort_words=True,
                                                    weight_unit=params.weight_unit,
                                                    weight=params.weight)

                alternative_count = self.__alternatives if len(match_record) > self.__alternatives else len(match_record)

                for i in range(alternative_count):

                    expl = self.__explorations[index][i]
                    product=market.get_product(identifier=match_record[i].product_ID)
                    expl.insert_product(target_ID=params.target_id,
                                        product=product,
                                        match_ratio=match_record[i].ratio,
                                        quantity=params.required_quantity)
            
    # def explore(self, product_list: List[ tuple[int, str, ProductCategory, int]]):
    #     """
    #         Parameters
    #         ---------
            
    #         1) product list - includes all explored products. Each product is represented via a tuple:

    #                 a) int - ID of the target product to which products in markets are sought,
    #                         explorations belonging to the same product will share this

    #                 b) str - a specific name of the product for which the exploration will be carried out

    #                 c) ProductCategory - this restricts exploration range to the specific category, if none
    #                                     then no filter is applied
    #                 d) int - required amount of the product
            
    #         2) limit - specifies how many additional explorations will be executed


    #     """
    #     #explorations: List[MarketExplorer.Exploration] = []
        
    
    #     #ha = self.Exploration()
        

    #     #explorations: List[tuple[int, List[RegisteredProduct], float]] = []

    #     #product_lists: Dict[int, List[RegisteredProduct]] = {}

    #     #for market in self.__markets:
    #        # product_lists.append( (market.ID(), [], 0) )


    #     for index, market in enumerate(self.__markets):
    #         products: List[List[tuple[RegisteredProduct, float]]] = []
    #         total_price: List[int] = []

    #         for i in range(self.__limit):
    #             products.append([])
    #             total_price.append(0)

    #         for target_ID, explored_product, category, amount in product_list:
                

    #             match_record = self.__matcher.match(text=explored_product,
    #                                                 markets=(market.ID(),),
    #                                                 category=None,
    #                                                 limit=self.__limit,
    #                                                 sort_words=True)

    #             for i in range(self.__limit):

    #                 #product = market.get_product(ID=match_record[0][0])
    #                 product = market.get_product(identifier=match_record[i].product_ID)
    #                 products[i].append((target_ID, product, match_record[i].ratio))
    #                 total_price[i] += product.price
                
    #         for i in range(index * self.__limit, index * self.__limit + self.__limit):
                
    #            # start = index * self.__limit

    #            # for g in range(start, index * self.limit)
    #             self.__explorations[i].total_price += total_price[i%5]
    #             self.__explorations[i].products.append((target_ID, products[i], total_price[i%5]))

    #             #self.__explorations.append(self.Exploration(market_ID=market.ID(),
    #             #                                            products=products[i],
    #             #                                            total_price=total_price[i]))
            


    #         #explorations.append( (market.ID(), products, total_price))

    #             # for market_ID, products, total_price in product_lists:
                    
    #             #     if market_ID == market.ID():
    #             #         _product = market.get_product(ID=match_record[0].product_ID)

    #             #         products.append(_product)
    #             #         total_price += _product.price
    #             #         break


    #     # for product, category in product_list:

    #     #     for market in self.__markets:
        
    #     #         match_record = self.__matcher.match(text=product, markets=(market.ID(),), category=category, limit=1 )
                
    #     #         #product = market.get_product(ID=match_record[0][0])

    #     #         for market_ID, products, total_price in product_lists:
                    
    #     #             if market_ID == market.ID():
    #     #                 _product = market.get_product(ID=match_record[0].product_ID)

    #     #                 products.append(_product)
    #     #                 total_price += _product.price
    #     #                 break
    #             #product_lists[market.ID()].append(market.get_product(ID=match_record[0].product_ID))
        
        
        






        