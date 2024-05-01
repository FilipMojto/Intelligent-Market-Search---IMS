import json
import os, sys

# script_directory = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(script_directory)

# os.chdir(script_directory)

def get_config_path():
    if getattr(sys, 'frozen', False):
        # If the script is run as an executable (e.g., PyInstaller bundle)
        return os.path.join(os.path.dirname(sys.executable), "..\\config.json")
    else:
        # If the script is run as a Python script
        script_directory = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_directory, ".config.json")

# ------ Project Config Globals ------ #

CONFIG_FILE_PATH = get_config_path()

with open(file=CONFIG_FILE_PATH, mode='r') as config_file:
    PATHS = json.load(config_file)

RESOURCES = PATHS["resources"]
DATA = PATHS["resources"]["data"]



# ----- File Paths Constants ----- #

MARKET_FILE = DATA["markets"]
PRODUCT_FILE = DATA["products"]
CATEGORY_FILE = DATA["categories"]
CATEGORY_MAP_FILE = DATA["category_mappings"]
MARKET_CENTER_FILE = DATA["market_hubs"]
SEARCHED_PRODUCTS_FILE = DATA["searched_products"]



# ----- GUI Config Constants ----- #

GUI = PATHS["resources"]["gui"]

NEW_ITEM_ICON = GUI["new_item_icon"]
SHOPPING_CART_ICON = GUI["shopping_cart_icon"]
SHOPPING_CART_ICON_2 = GUI['shopping_cart_icon_2']
TRASH_BIN_ICON = GUI['trash_bin']
ACCEPT_ICON = GUI['accept_icon']
DECLINE_ICON = GUI['decline_icon']
SEARCH_ICON = GUI['search_icon']
GEAR_ICON = GUI['gear_icon']
EXIT_ICON = GUI['exit_icon']
MAGNIFIER_ICON = GUI['magnifier_icon']
ERASER_ICON = GUI['eraser_icon']
PLUS_ICON = GUI['plus_icon']
MINUS_ICON = GUI['minus_icon']