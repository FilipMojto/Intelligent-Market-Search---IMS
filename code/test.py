from AOSS.structure.shopping import MarketPlace
from AOSS.components.marexp import MarketExplorer


from config_paths import *

with MarketPlace(src_file=MARKET_CENTER_FILE['path'], console_log=True) as hub:
    explorer = MarketExplorer(market_hub=hub)
    explorer.explore(product_list=[MarketExplorer.ExplorationParams()])

