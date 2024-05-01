# ------- Module Description ------- #

"""
    This module defines fully implemented user interface when it comes to online shopping. It provides some general functions for working
    with markets and classes which define further structure and compatibility.

    Functions:
        market()
        markets()
        are_compatible()

    Classes:
        Product
        Market
        ProductCategory
"""

__ALL__ = ['market', 'markets', 'are_compatible', 'Product', 'Market', 'ProductCategory']
__AUTHOR__ = "Evening Programmer"
__VERSION__ = "1.0.0"

# ------- System Import -------- #

from typing import List, Dict, Literal
from enum import Enum
from dataclasses import dataclass, KW_ONLY
from abc import ABC, abstractmethod

import csv
import polars as pl

import threading
import time
from datetime import datetime

# ------- My Imports ------- #

from config_paths import *
from config import PF_FIELDNAMES
from AOSS.other.utils import PathManager, TextEditor
from AOSS.other.exceptions import IllegalProductState, InvalidMarketState

class ProductCategory(Enum):
    NEURČENÁ = 0
    OVOCIE_ZELENINA = 1
    PECIVO = 2
    MASO_MRAZENE_VYROBKY = 3
    UDENINY_NATIERKY_PASTETY = 4
    MLIECNE_VYROBKY = 5
    TRVANLIVE_POTRAVINY_VAJCIA = 6
    SLADKOSTI = 7
    SLANE_SNACKY_SEMIENKA = 8
    NEALKOHOLICKE_NAPOJE = 9
    TEPLE_NAPOJE = 10
    ALKOHOL = 11
    ZDRAVE_POTRAVINY = 12
    HOTOVE_INSTANTNE = 13

class ProductWeightUnit(Enum):
    NONE = 1
    GRAMS = 2
    LITRES = 3

@dataclass
class Product:
    """
        This class represents a single Product object. It is a data class which should provide a
        convenient way of storing information about products  during program runtime.
        
        Attributes:
            a) ID (unsigned int) - unique identifier within the market which possess the product

            b) name (string) - unique name identifier of a product

            c) price (float) - decimal number representing the price of a product 

            d) approximation (bool) - flag indicating whether price is just an approximation

            e) category (int) - one of the possible categories

            f) hash (string) - hashed name attribute using sha256 - Removed

            g) market_ID (unsigned int) - unique identifier of a market which possess the product, -1 if not possessed by any market
    """


    name: str
    _: KW_ONLY
    price: float = -1
    approximation: int = -1
    weight_unit: ProductWeightUnit = ProductWeightUnit.NONE
    weight: float = -1
    category_ID: int = -1
    quantity_left: int = -1
    created_at: str
    updated_at: str

    def __post_init__(self):
        self.normalized_name = TextEditor.standardize_str(self.name)



@dataclass
class RegisteredProduct(Product):

    ID: int
    market_ID: int
    _: KW_ONLY
    normalized_category: ProductCategory = ProductCategory.NEURČENÁ

    @staticmethod
    def to_obj(row: str):
        attributes = row.split(PRODUCT_FILE['delimiter'])

        if len(attributes) != PRODUCT_FILE['col_count']:
            raise ValueError("Provided row contains invalid amount of attributes!")

        return RegisteredProduct(
            ID=attributes[PRODUCT_FILE['columns']['ID']['index']],
            name=attributes[PRODUCT_FILE['columns']['name']['index']],
            price=float(attributes[ PRODUCT_FILE['columns']['price']['index']]),
            approximation=int(attributes[PRODUCT_FILE['columns']['approximation']['index']]),
            weight_unit=attributes[PRODUCT_FILE['columns']['weight_unit']['index']],
            weight=float(attributes[PRODUCT_FILE['columns']['weight']['index']]),
            category_ID=int(attributes[PRODUCT_FILE['columns']['query_string_ID']['index']]),
            normalized_category=ProductCategory[attributes[PRODUCT_FILE['columns']['category']['index']]],
            market_ID=attributes[PRODUCT_FILE['columns']['market_ID']['index']],
            quantity_left=int(attributes[PRODUCT_FILE['columns']['quantity_left']['index']]),
            created_at=attributes[PRODUCT_FILE['columns']['created_at']['index']],
            updated_at=attributes[PRODUCT_FILE['columns']['updated_at']['index']]
        )
    
    @staticmethod
    def to_obj_from_dict(row):
        

        return RegisteredProduct(
            ID=int(row['ID']),
            name=row['name'],
            price=float(row['price']),
            approximation=int(row['approximation']),
            weight_unit=row['weight_unit'],
            weight=float(row['weight']),
            quantity_left=int(row['quantity_left']),
            category_ID=row['query_string_ID'],
            normalized_category=ProductCategory[row['category']],
            market_ID=int(row['market_ID']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    


class ProductIdentification(ABC):
       
    @abstractmethod
    def assign_product_ID(self, market):
        pass
        

class MarketView:
    
    """
        This class is supposed to hold basic information about an online market stored locally and provide
        access to its products.

        Attributes:

            a) ID - unique identifier of a market, best if set by a market hub
            
            b) name - market company name

            c) store_name - unique name of a specific market store

            d) categories - a sublist of all category names as they are used online, they are basically query strings

    """

    def __init__(self, ID:int, name: str, store_name: str, product_file: str,  category_file: str):
        self.__ID = ID
        self.__name = name
        self.__store_name = store_name
        self.__categories: Dict[int, str] = {}
        self.__products: Dict[str, RegisteredProduct] = {}

        self.__product_file = product_file
        PathManager.check_if_exists(path=product_file, type='file')

        self.__category_file = category_file
        PathManager.check_if_exists(category_file, type='file')
        


        # we load categories from provided file
        with open(file=self.__category_file, mode='r', encoding='utf-8') as file:
            categories = csv.DictReader(file)

            for metadata in categories:

                if int(metadata['market_ID']) == self.__ID:
                    self.__categories[int(metadata['ID'])] = metadata['name'] 
            


    def __str__(self):
        return f"{{ID: {self.__ID}, name: {self.__name}, store_name: {self.__store_name}, categories: {self.__categories.keys()}}}" + '\n'



    def load_products(self):

        with open(file=self.__product_file, mode='r', encoding='utf-8') as product_f:
            products = csv.DictReader(product_f)

            for product in products:

                if int(product['market_ID']) == self.__ID:
                    _product = RegisteredProduct.to_obj_from_dict(row=product)
                    self.__products[_product.name] = _product
                



    def ID(self):
        return self.__ID

    def name(self, name: str = None):
        if name is not None:
            self.__name = name
        else:
            return self.__name
    
    def store_name(self, name: str = None):
        if name is not None:
            self.__store_name = name
        else:
            return self.__store_name
    
    def categories(self):
        return self.__categories
    

    def product_file(self):
        return self.__product_file
    
    def category_file(self):
        return self.__category_file

    def products(self):
        return self.__products
    
    def get_product(self, identifier: int | str):

        """
            This is one of the CRUD methods provided by class Market. It is suppossed to load the desired
            product metadata and return it as a new Product object.
            
            Parameters:

                ID - unique identifier of a retrieved product

            Please note, that this method only works within this Market object, so even if the provided ID
            is in dataset but it is not associated with this Market, it will be ignored.
        """
        
        if isinstance(identifier, int):
            for product in self.__products.values():
                if product.ID == identifier:
                    return product
        elif isinstance(identifier, str):
            return self.__products[identifier]
        else:
            raise TypeError("Unsupported type of identifier!")

 


    
# --- Market - Class Declaration&Definition --- #

class Market(MarketView):
    
    """
        Class Market extends MarketView by adding registration functionalities, which basically
        allows the market instance to register new Product objects.

        Newly registered products are firstly stored in a buffer during runtime but can also be
        appended to the provided Product File. User can specify limit of this buffer, so that it
        is automatically saved to the file and cleared when necessary.
    
    """
    
    

    def __init__(self, ID: int, name: str, store_name: str, market_hub: ProductIdentification,
                 product_file: str, category_file: str, buffer: int = 5000) -> None:
        super().__init__(ID=ID, name=name, store_name=store_name, product_file=product_file, category_file=category_file)

        # --- Market Attributes --- #
        self.__market_hub = market_hub
     

        # --- Market Product Registration Attributes --- #

        self.__registration_buffer: List[tuple[Product, ProductCategory]] = []
        self.__update_buffer: List[Product] = []
        self.__removal_buffer: List[int] = []
        self.__buffer_limit = buffer
        self.__buffer_lock = threading.Lock()

        
    def load_products(self):
        if self.__registration_buffer:
            raise InvalidMarketState("Cannot load products because there are products in registration buffer!")
        
        
        return super().load_products()


    def buffer(self, size: int):
        with self.__buffer_lock:
            self.__buffer_limit = size

    def is_registered(self, product_name: str):
        for _product in self.__registration_buffer:
            if (product_name == _product[0].name):
                return True
                
        return product_name in self.products()
            


    def register_product(self, product: Product, norm_category: ProductCategory = ProductCategory.NEURČENÁ):
        
        """
            This method is another of the CRUD method of Market class. It registers the provided product
            by storing it to a list during runtime.

            Parameters:

                a) product - a Product instance to be registered

                b) norm_category - an ProductCategory instance, if product's category is normalized

            In order to register successfully the product has to:

                a) have unique name from the registered or locally stored products

                b) have a category which is supported by the market object
            
            Please note, that in order to store newly added instances persistenly to a Product File
            method save_products() must be used. Products are saved in this manner automatically when
            the buffer limit is reached.

            IllegalProductState exception is thrown in case of the following events:

            a) Conflicting name with an unregistered product (stored in buffer)
            b) Conflicting name with a registered product (stored locally in the source file)
            c) The market doesn't provide such a category
        """


        with self.__buffer_lock:
            # Let's firstly check the unregistered products to prove product's uniqueness
            for _product in self.__registration_buffer:
                if (product.name == _product[0].name):
                    raise IllegalProductState("Conflicting name with an unregistered product!")
            
            # Now we check the registered products for the same purpose
            
            if product.name in self.products():
                raise IllegalProductState("Conflicting name with a registered product!")



            # here we verify the category of the product, whether the market provides it
            with open(self.category_file(), mode='r', encoding='utf-8') as categories_f:
                categories = csv.DictReader(categories_f)
                
                for metadata in categories:

                    if (product.category_ID == int(metadata['ID'])):
                        break

                else:
                    raise IllegalProductState("The market doesn't provide such a category.")

            # Finally, we can add the product for registration
            self.__registration_buffer.append((product, norm_category))
        
            if len(self.__registration_buffer) >= self.__buffer_limit:
                self.save_products()



    def update_product(self, product: Product):

        if product.name in self.products(): 
            self.__update_buffer.append(product)
        else:
            raise IllegalProductState("Provided product not registered!")
        

    
    def remove_products(self, identifiers: List[int]):
        _products = self.products()
        
      
        for id in identifiers:
            try:
                self.__removal_buffer.append(_products[id].ID)
            except KeyError:
                raise IllegalProductState(message="Provided product not found in the dataset!")




    def save_products(self, remove_if_outdated: bool = False):

        """
            This method stores all products stored in a buffer during runtime to the Product File.
            The buffer is cleared at the end of process.

            Parameters:

                a) remove_if_outdated - all products which have not been updated are automatically removed
        """

        if self.__update_buffer or self.__removal_buffer:
            local_products_tree = []


            with open(file=self.product_file(), mode='r', encoding='utf-8') as product_f:
                for row in csv.DictReader(product_f):
                    for el in local_products_tree:
                        if el[0][0]['market_ID'] == row['market_ID']:
                            el.append([row, False])
                            break
                    else:
                        local_products_tree.append([[row, False]])

            market_bound_LPT = None

            for el in local_products_tree:
                if int(el[0][0]['market_ID']) == self.ID():
                    market_bound_LPT = el
                    break


                # local_products = [[row, False] for row in csv.DictReader(product_f)]
                # local_products = list((csv.DictReader(product_f), False))

            # Update products based on the __update_buffer
            for upd_product in self.__update_buffer:
                for local_product in market_bound_LPT:
                    if upd_product.name == local_product[0]['name']:

                        local_product[0]['price'] = upd_product.price
                        local_product[0]['approximation'] = upd_product.approximation
                        local_product[0]['quantity_left'] = upd_product.quantity_left
                        local_product[0]['updated_at'] = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                        local_product[1] = True
                        break
      
                else:
                    raise TypeError("Not found!")

            # Save the updated products back to the CSV file
            with open(file=self.product_file(), mode='w', encoding='utf-8', newline='') as product_f:
                
                # fieldnames = ('ID','name','normalized_name','price','approximation','quantity_left',
                #               'category', 'query_string_ID','market_ID','created_at','updated_at')
                
                products_writer = csv.DictWriter(product_f, fieldnames=PF_FIELDNAMES)

                # Write the header
                products_writer.writeheader()
            

                # if there are products to remove we exlude their rows from the dataset
                if self.__removal_buffer:
                    market_bound_LPT = [row for row in market_bound_LPT if int(row[0]['ID']) not in self.__removal_buffer]
                
                if remove_if_outdated:
                    market_bound_LPT = [row for row in market_bound_LPT if row[1] == True]

        
                # Write the updated products
                # for el in local_products_tree:
                #     products_writer.writerows(el[0])
                for el in local_products_tree:
                    for product_data, _ in el:
                        products_writer.writerow(product_data)

            self.__removal_buffer.clear()
            self.__update_buffer.clear()

                        

        with open(self.product_file(), 'a', encoding='utf-8') as file:
            for element in self.__registration_buffer:

                if isinstance(element, tuple):
                    local_product, category = element
                    id = self.__market_hub.assign_product_ID(market=self)
                    file.write(str(id) + PRODUCT_FILE['delimiter'] +
                            local_product.name + PRODUCT_FILE['delimiter'] +
                            local_product.normalized_name + PRODUCT_FILE['delimiter'] +
                            str(local_product.price) + PRODUCT_FILE['delimiter'] +
                            str(int(local_product.approximation)) + PRODUCT_FILE['delimiter'] +
                            local_product.weight_unit.name + PRODUCT_FILE['delimiter'] +
                            str(local_product.weight) + PRODUCT_FILE['delimiter'] +
                            str(local_product.quantity_left) + PRODUCT_FILE['delimiter'] +
                            category.name + PRODUCT_FILE['delimiter'] +
                            str(local_product.category_ID) + PRODUCT_FILE['delimiter'] +
                            str(self.ID()) + PRODUCT_FILE['delimiter'] +
                            local_product.created_at + PRODUCT_FILE['delimiter'] +
                                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + '\n')
                # elif isinstance(element, RegisteredProduct):
                #     file.write(str(element.ID) + PRODUCT_FILE['delimiter'] +
                #             element.name + PRODUCT_FILE['delimiter'] +
                #             element.normalized_name + PRODUCT_FILE['delimiter'] +
                #             str(element.price) + PRODUCT_FILE['delimiter'] +
                #             str(int(element.approximation)) + PRODUCT_FILE['delimiter'] +
                #             element.weight_unit.name + PRODUCT_FILE['delimiter'] +
                #             str(element.weight) + PRODUCT_FILE['delimiter'] +
                #             str(element.quantity_left) + PRODUCT_FILE['delimiter'] +
                #             element.normalized_category + PRODUCT_FILE['delimiter'] +
                #             str(element.category) + PRODUCT_FILE['delimiter'] +
                #             str(self.__ID) + PRODUCT_FILE['delimiter'] +
                #             element.created_at + PRODUCT_FILE['delimiter'] +
                #                 element.updated_at)
                else:
                    raise TypeError("Uknown type for registered buffer element!")
            
        self.__registration_buffer.clear()






class MarketPlace(ProductIdentification):

    """
        MarketHub provides an effective system for market storage and management.
        The implementation is file-based, therefore all metadata are loaded
        directly from files, stored and manipulated efficiently during program
        runtime and then updated back to source files.

        Necessary metadata which must be provided in the source file:

            a) market_ID - next ID assigned to a newly registered market
            b) product_ID - next ID registered by any registered market
            c) market_file - a valid path to a file which stores registered markets


        Registered markets must follow some rules:

            a) They share the same files for their products and categories

            b) Their IDs, names and store names must be unique
        
        Aggregating markets in this manner allows for their categorization and search of registered
        products or even exploring and recommending their instances.
        
        See Also:
            :class:`ProductCategorizer`
            :class:`ProductMatcher`
            :class:`MarketExplorer`
    """

    # ------ MarketHub Constructor ------- #

    def __init__(self, src_file: str, console_log: bool = True) -> None:

        """
            Constructs a MarketHub object by loading its metadata from a provided source file.
            Source file must follow CSV format.
        """
        
        self.console_log = console_log

        # this ensures that the provided source file exists
        if PathManager.check_if_exists(path=src_file, type='file'):
            self.__src_file = src_file
    

        # loads the necessary metadata from the source file and verify their format
        with open(file=self.__src_file, mode='r') as src_file:
            reader = csv.DictReader(src_file)
            metadata = next(reader)


            self.__next_market_ID = int(metadata['market_ID'])
            self.__next_product_ID = int(metadata['product_ID'])

            if PathManager.check_if_exists(metadata['market_file']):
                self.__market_file = metadata['market_file']

            self.__training_market = int(metadata['training_market'])
            if PathManager.check_if_exists(metadata['category_file']):
                self.__standardized_category_file = metadata['category_file']


        self.__product_file: str = None
        self.__category_file: str = None


        
        # markets are stored as mappings of Market objects to their market ID
        # this is because when new markets are registered their IDs cannot be
        # modified directly in the class
        # when market stats are saved back to the file, their IDs are based on
        # this mapping
        self.__markets: List[tuple[Market, int]] = []
        self.__mappings: Dict[int, str] = {}

        


    def __enter__(self, console_log: bool = None):
        """
            Apart from constructing a MarketHub object this also automatically loads the 
        """

        if (console_log is not None and console_log) or self.console_log:
            print("Loading markets from a file...")
  
        self.load_markets()
        self.load_mappings()        
        self.load_products()
        
        if (console_log is not None and console_log) or self.console_log:
            print(f"Successfully loaded {len(self.__markets)} markets!")

        return self
    
    def __exit__(self, exc_type, exc_value, traceback, console_log: bool = None):
        if (console_log is not None and console_log) or self.console_log:
            print("Updating hub stats to file...")
        self.update(console_log=console_log)
        


    # ------ MarketHub - Public Interface ------- #

    def load_markets(self, console_log: bool = None):

        """
            Loads metadata about markets stored in the Market File and stores them as Market objects
            in the buffer. When loading metadata, their format is strictly checked. If certain line
            in the file contain invalid data, it might be skipped completely or logged.

            Parameters:

                console_log - if any errors with Market metadata are encountered, they are logged in
                                       theconsole  
        """

        with open(file=self.__market_file, mode='r', encoding='utf-8') as market_file:
            markets = csv.DictReader(market_file)

            # iterates line by line and loads market metadata storing as Market objects afterwards
            for index, metadata in enumerate(markets):
                ID = None

                try:
                    ID = int(metadata['ID'])
                except ValueError:

                    if (console_log is not None and console_log) or self.console_log:
                        print(f"Error at line {index}: Failed to load ID attribute.")
                
                name = metadata['name']
                store_name = metadata['store_name']

                if (name is None or not name or store_name is None or not store_name) and (
                    (console_log is not None and console_log) or self.console_log):
                    print(f"Error at line {index}: Failed to load name or store_name attribute.")


                # checks the existence of the loaded paths
                try:

                    product_file = metadata['product_file']
                    category_file = metadata['category_file']       

                    PathManager.check_if_exists(path=product_file)
                    PathManager.check_if_exists(path=category_file)

                except ValueError:
                    if (console_log is not None and console_log) or self.console_log:
                        print(f"Error at line {index}: Invalid Product File or Category File paths.")

                # checks the consistence of Product and Category File paths
                if self.__product_file is None and self.__category_file is None:
                    self.__product_file = product_file
                    self.__category_file = category_file
                elif ((self.__product_file != product_file or self.__category_file != category_file)
                    and ((console_log is not None and console_log) or self.console_log)):
                    print(f"Error at line {index}: Inconsistent Product File or Category File paths.")

                new_market = Market(ID=ID,
                                    name=name,
                                    store_name=store_name,
                                    market_hub=self,
                                    product_file=product_file,
                                    category_file=category_file
                            )


                if not self.can_register(market=new_market) and ((console_log is not None and console_log) or self.console_log):
                    print("Error at line {index}: Market cannot be aggregated by the market hub!")



                # aggregates new Market object
                self.__markets.append((new_market, new_market.ID()))
            
            # eventually sets the training market
            self.__training_market = self.market(identifier=self.__training_market)

    def get_standardized_category(self, category_ID: int):
        return self.__mappings[category_ID] if category_ID in self.__mappings else None
    

    def load_mappings(self):
        """
            Loads mappings of each market's local category to a standardized category.

            Markets' metadata must be loaded first in order to get the path of their 
            local categories. This can be done calling load_markets() method.
        """

        category_mappings = []
        normalized_categories = []

        with open(file=self.__category_file, mode='r', encoding='utf-8') as category_file:
            mapping_reader = csv.reader(category_file)
            next(mapping_reader)
            category_mappings = list(mapping_reader)
   

        with open(file=self.__standardized_category_file, mode='r', encoding='utf-8') as stnd_category_file:
            stnd_category_reader = csv.reader(stnd_category_file)
            next(stnd_category_reader)
            normalized_categories = list(stnd_category_reader)
        
        for CM_row in category_mappings:
            
            for NC_row in normalized_categories:

                if CM_row[CATEGORY_MAP_FILE['columns']['category_ID']['index']] == NC_row[CATEGORY_FILE['columns']['ID']['index']]:
                    self.__mappings[int(CM_row[CATEGORY_MAP_FILE['columns']['ID']['index']])] = NC_row[CATEGORY_FILE['columns']['name']['index']] 
                    break






    def load_dataset(self):
        """
            This function (re)loads current dataframe by reading it as a polars dataset. The csv format
            is requested.
        """

        if self.__product_file is not None:

            self.__product_df = pl.read_csv(self.__product_file)
        else:
            raise InvalidMarketState("At least one market must be loaded first!")



    def load_products(self):
        """
            Loads all product data necessary for market hub full functionality. For a market hub instance
            this includes loading all product data in the form of Polars dataset. For each registered market this
            includes loading all of its registered products in the form dictionaries.            
        """

        if self.__product_file is not None:

            self.__product_df = pl.read_csv(self.__product_file)
            #self.__product_df.apply
        else:
            raise InvalidMarketState("At least one market must be loaded first!")
        
        for market_data in self.__markets:
            market_data[0].load_products()


    def update(self, console_log: bool = None):
        """
            This method updates MarketHub metadata (product_ID and market_ID) by
            writing it back to the source file.

            This method is called automatically at the end when used along with
            the with statement.
        """

        metadata: List[str] = None

        with open(self.__src_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            metadata = next(reader)
            
            metadata['market_ID']= str(self.__next_market_ID)
            metadata['product_ID'] = str(self.__next_product_ID)


        with open(self.__src_file, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows([metadata])


        lines = []

        with open(self.__market_file, mode='r', encoding='utf-8') as market_file:
            reader = csv.DictReader(market_file)
            fieldnames = reader.fieldnames
            lines.append(MARKET_FILE['delimiter'].join(fieldnames) + '\n')
            

        for market, ID in self.__markets:
            lines.append(str(ID) + MARKET_FILE['delimiter'] + market.name() + MARKET_FILE['delimiter'] + market.store_name() + MARKET_FILE['delimiter'] + self.__product_file + MARKET_FILE['delimiter'] + self.__category_file + '\n')

        

        with open(self.__market_file, mode='w', newline='', encoding='utf-8') as file:
            file.writelines(lines)

        if (console_log is not None and console_log) or self.console_log:
            print("Data updated successfully!")

        

    def save_markets(self):
        """
            Saves all markets' products back to their product file.
        """
        for market in self.__markets:
            market[0].save_products()

    
    def product_file(self):
        return self.__product_file

    

    def __get_market_ID(self):
        old_val = self.__next_market_ID
        self.__next_market_ID += 1
        return old_val

 
    

    def product_df(self):
        return self.__product_df
    
    def training_market(self):
        return self.__training_market


    def can_register(self, market: MarketView) -> bool:
        """
            This method checks whether the provided market object meets all the necessary
            conditions so that it can be registered by this MarketHub object.

            The mentioned conditions are as follows:
                
                a) The consistency of Product and Category File with the MarketHub instance

                b) Uniqueness of name and store_name attributes
        """

        if (self.__product_file != market.product_file() or self.__category_file
                  != market.category_file()): #or self.__hash_file != market.hash_file()[0]):
            return False
        
        for __market, _ in self.__markets:

            if __market.name() == market.name() or __market.store_name() == market.store_name():
                return False

        return True
    
    def register(self, market: MarketView):
        if self.can_register(market=market):
            self.__markets.append((market, self.__get_market_ID()))
        else:
            raise InvalidMarketState("Cannot register provided market!")
            #raise ValueError("Cannot register provided market!")
    
    def can_categorize(self):
        """
            This methods checks whether categorization by a training market is possible.
            This means, that it cannot be None and it must contain at least one product
            for each of its categories.

            Returns:
                bool: True, if this hub can categorize products, False otherwise

        """

        if self.__training_market is None:
            return False
        else:
            categories = self.__training_market.categories()

            for ID in categories.keys():
                if len(self.__product_df.filter((self.__product_df['market_ID'] == self.__training_market.ID()) &
                                        (self.__product_df['query_string_ID'] == ID))) == 0:
                    return False
            
        return True


    def market(self, identifier: int, mode: Literal['ID', 'index'] = 'ID'):
        """
            This will return a registered market by its identifier. This can either be a ID or
            index.

            Parameters
            ----------

                a) identifier - unique positive integer which identifies a specific market

                b) mode - whether identifier is an ID or index

        """
        if mode == 'ID':
            for market, _ in self.__markets:
                if market.ID() == identifier:
                    return market
            else:
                return None
        elif mode == 'index':
            return self.__markets[identifier][0]


    def markets(self):
        """
            This will return a tuple of all aggregated markets.
        """

        return tuple(market for market, _ in self.__markets)
    
    def remove_local_products(self):
        header = ""

        if (PRODUCT_FILE['header']):
            with open(file=self.__product_file, mode='r', encoding='utf-8') as file:
                header = file.readline()
        

        

        with open(file=self.__product_file, mode='w', encoding='utf-8', newline='') as file:
            file.write(header)

    
    

    
    def assign_product_ID(self, market: Market):
        
        for market, _ in self.__markets:
            if market.ID() == market.ID():
                old_value = self.__next_product_ID
                self.__next_product_ID += 1
                return old_value
        else:
            raise InvalidMarketState("Provided market is not aggregated by this market hub! Register it first.")
            
    
                    


if __name__ == "__main__":

    product = Product(name="Hrusky zelene", price=1.23, approximation=0, category_ID="ovocie&zelenina")
    product.__str__()

