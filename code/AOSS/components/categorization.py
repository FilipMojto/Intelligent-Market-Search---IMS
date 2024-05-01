from typing import List

import csv
import time
from datetime import datetime

from config_paths import *
from AOSS.structure.shopping import Product, ProductCategory, MarketPlace
from AOSS.components.search import ProductMatcher
from AOSS.other.exceptions import InvalidFileFormatError
from AOSS.other.utils import TextEditor


PRICE_APPROXIMATION_SIGN = '~'
CURRENCY_SIGN='€'


def process_scraped_products(products: (list[tuple[Product, int]] | tuple[Product, int]),
                              substition: (list[tuple[str, str]] | tuple[str, str]) = (',', '.')):

    if isinstance(products, list):
        results: List[Product] = []

        for name, price, category, _ in products:
            
            if isinstance(substition, list):

                for subst in substition:
                    name = name.replace(subst[0], subst[1])
                    price = price.replace(subst[0], subst[1])
            elif isinstance(substition, tuple):
                name = name.replace(substition[0], substition[1])
                price = price.replace(substition[0], substition[1])

            approximation = 0

            if price is None or not price:
                continue

            # Here we check whether theprice is just an approximate value
            if(price[0] == PRICE_APPROXIMATION_SIGN):
                price = price[1:]
                approximation = 1

            # We remove the potential price approximation sign from the price text
            price = price.split(CURRENCY_SIGN)[0].strip()

            results.append(Product(
                name=name,
                price=float(price),
                approximation=approximation,
                category_ID=category,
                created_at=datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                updated_at=datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            )
        
        return results
    elif isinstance(products, tuple):
        name, price, category, market_ID = products

        if isinstance(substition, list):

            for subst in substition:
                name = name.replace(subst[0], subst[1])
                price = price.replace(subst[0], subst[1])
        elif isinstance(substition, tuple):
            name = name.replace(substition[0], substition[1])
            price = price.replace(substition[0], substition[1])

        approximation = 0

        # Here we check whether the price is just an approximate value
        if(price[0] == PRICE_APPROXIMATION_SIGN):
            price = price[1:]
            approximation = 1

        # We remove the potential price approximation sign from the price text
        price = price.split(CURRENCY_SIGN)[0].strip()

        return Product(name=name, price=float(price), approximation=approximation, category_ID=products[2],
                       created_at=datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                       updated_at=datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    else:
        raise TypeError("Unsupported type of products variable!") 

def process_product(product: Product):
    product.name = product.name.replace(',', '.')
    product.normalized_name = product.normalized_name.replace(',', '.')


import pandas as pd

class ProductCategorizer:

    @staticmethod
    def category_details(category: str):
       
        with open(CATEGORY_FILE['path'], 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            
            # Assuming the first row contains headers

            if CATEGORY_FILE['header']:
                next(csv_reader)
            
            # Reading the rest of the rows
            for row in csv_reader:
                # Accessing columns by index
                if row[CATEGORY_FILE['columns']['name']['index']] == category:
                    return row[CATEGORY_FILE['columns']['details']['index']]
            
        return None

    @staticmethod
    def categorize_by_mapping(product: Product, mappings_file: str):
        """
            This function categorizes a product manually based on category mapping in a file. This is especially useful for
            categorizing training market's products.

            It searches the provide custom-mapping file and if it contains a mapping for the product's category it attempts to
            find a normalized category. 
        """

        category_ID = -1

        with open(file=mappings_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            
            for row in reader:
                if int(row['ID']) == product.category_ID:

                    category_ID = int(row['category_ID'])
                    break
            else:
                raise ValueError("There is no mapping for the specified category!")
            

        with open(file=CATEGORY_FILE['path'], mode='r', encoding='utf-8') as file:
            
            line = file.readline()

            if len(line.split(CATEGORY_FILE['delimiter'])) != len(CATEGORY_FILE['columns']):
                raise InvalidFileFormatError("File contains invalid amount of columns!")

            if line is not None and CATEGORY_FILE['header']:
                line = file.readline()

            while line:
                
                attributes = line.split(CATEGORY_FILE['delimiter'])

                if int(attributes[CATEGORY_FILE['columns']['ID']['index']]) == category_ID:
                    return ProductCategory(value=category_ID)

                line = file.readline()
            else:
                raise ValueError("Target category is not found!")


    def __init__(self, market_hub: MarketPlace) -> None:
        if not market_hub.can_categorize():
            raise ValueError("""Cannot categorize product because training market is unspecified or contains no data for one of
                         its categories!""")
        
        self.__market_hub = market_hub
        self.__training_market = self.__market_hub.training_market()
        self.__matcher = ProductMatcher(market_place=self.__market_hub)
        self.__matcher.set_subset(market_ID=self.__training_market.ID())


    def recategorize(self):

        # Step 1: Load the CSV file into a Pandas DataFrame
        csv_file_path = self.__market_hub.product_file()
        df = pd.read_csv(csv_file_path)
        training_market = self.__market_hub.training_market().ID()

        # Step 2: Iterate and Modify Rows
        column_to_modify = 'category'
        for _, row in df.iterrows():
            # Your modification logic here, for example:
            if row['market_ID'] != training_market:
                start = time.time()
                row[column_to_modify] = self.categorize(product=row['normalized_name']).name
                end = time.time()

                print(f"Time: {end - start}")
            # row[column_to_modify] = modify_function(row[column_to_modify])
            #pass

        # Step 3: Save the Modified DataFrame
        #modified_csv_file_path = 'modified_file.csv'
        df.to_csv("../resources/data/temp.csv", index=False)




    def categorize(self, product: Product | str):
        """
            This function categorizes a product based on the training market's product categories in the provided market hub.
            It uses a ProductMatcher object to find the best match for the product in the training market product dataset.

            To be able to categorize a product successfully, following must be met:

                a) Provided market must contain a training market

                b) Training market must provide at least one product for each of its categories
            
            Otherwise ValueError exception is thrown.
        """


        match = None
        
        if isinstance(product, Product):
            match = self.__matcher.match(text=product.normalized_name, use_subset=True, limit=1, min_match=0)

           # match = self.__matcher.match(text=product.normalized_name, markets=(self.__training_market.ID(),), limit=1, min_match=0)
        elif isinstance(product, str):
            match = self.__matcher.match(text=TextEditor.standardize_str(text=product),
                                          use_subset=True, limit=1, min_match=0)
            
    

        product_match = self.__training_market.get_product(identifier=match[0].product_ID)
        return product_match.normalized_category
    















