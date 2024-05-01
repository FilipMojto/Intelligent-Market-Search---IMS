import csv
import time

from config_paths import *

from AOSS.structure.shopping import MarketPlace
from AOSS.components.categorization import ProductCategorizer


with MarketPlace(src_file=MARKET_CENTER_FILE['path']) as hub:
    with open(file=PRODUCT_FILE['path'], mode='r', encoding='utf-8') as file:
        products = list(csv.reader(file)) # Convert the iterator to a list

    
    categorizer = ProductCategorizer(market_hub=hub)
    limit = 0

    for i in range(1, len(products)):
        if products[i][8] != "2":
            break

        limit += 1

    print(limit)

    start = time.time()

    for product in products:
        if product[8] == "2":
            continue
        
        product[6] = categorizer.categorize(product=product[2]).name
        print(f"Categorized product: {product[2]}")
    
    with open(file=PRODUCT_FILE['path'], mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(products)
    
    end = time.time()

    print(f"Time: {end - start}")

         
    
    
