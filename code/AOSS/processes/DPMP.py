import sys, os, time
from typing import List
import multiprocessing as mpr, multiprocessing.connection as mpr_conn
import signal
import math
from queue import Empty
import threading
from datetime import datetime

#Set the starting point to the directory containing the script
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)

parent_directory = os.path.abspath(os.path.join(script_directory, '..', '..'))
sys.path.append(parent_directory)


from config_paths import *
from AOSS.structure.shopping import MarketPlace, Market, ProductCategory
from AOSS.components.categorization import ProductCategorizer
from AOSS.components.categorization import process_product
from AOSS.other.exceptions import IllegalProductState

from AOSS.processes.IPC import ProgressReportPoints as PRP, ScrapeRequest
from AOSS.processes.IPC import UPDATE_INTERVAL_SIGNAL, PROGRESS_BAR_SIGNAL, UPDATE_PRODUCTS_SIGNAL
from AOSS.processes.IPC import ScrapeRequestGenerator


requests: List[ScrapeRequest] = []
request_ID = 1
product_df = None



UPDATE_LIMIT = 0.75
MAX_UPDATE_DELAY = 10


market_hub_lock = threading.Lock()

                                





def start(main_to_all: mpr.Queue, hub_to_scraper: mpr.Queue, scraper_to_hub: mpr.Queue, hub_to_gui: mpr.Queue,
          gui_to_hub: mpr.Queue, product_file_lock: mpr.Lock, console_log: bool = True):
    
    update_interval = 0
    request_generator = ScrapeRequestGenerator()


    def terminate():
        nonlocal hub
        hub.save_markets()
        hub.update()
        exit(0)
        

    def signal_handler(signum):

        if signum == 2:
            # Since process might be in the middle of update or something like that, 
            # some exceptions might be uncaught
            try:
                print("Terminating marketing process...")
                terminate()
            except Exception:
                pass
                

    def check_main(main_to_all: mpr.Queue, timeout: int = 1):
        """
            Checks for some predefined signals which might be sent by the main process, like termination signal.

            If termination signal was received, process terminates by executing termination function.
        """

        
        if main_to_all.value:
            terminate()
        
        time.sleep(timeout)
   
    def request_missing_categories(market: Market, console_log: bool = True):
        nonlocal request_generator

        """
            Analyzes provided market by searching registered products for each category. If category contains
            no such products it inserts it into the SrapeRequest's empty categories buffer.

            Global product dataframe is used to filter our analyzed market and its categories.

            New ScrapeRequest instance is only added to the global request buffer should at least one empty category
            was found.
        """

        categories = market.categories()
        empty_categories = []

        for ID, name in categories.items():
            if len( product_df.filter( (product_df['market_ID'] == market.ID() ) &
                                    (product_df['query_string_ID'] == ID) )) == 0:
                
                if console_log:
                    print(f"Detected no products for market {market.name()}. Category: {name}")
                empty_categories.append(ID)
            
        # now we create a request if needed
        if empty_categories:
            requests.append(ScrapeRequest(ID=request_generator.get_request_ID(), market_ID=market.ID(), categories=empty_categories))



    



    def send_or_wait(main_to_all: mpr_conn.PipeConnection, hub_to_scraper: mpr.Queue, request: ScrapeRequest,
                     console_log: bool = True):
        """
            Attempts to send a ScrapeRequest instance via hub-to-scraper Queue. If the request was not sent
            because the queue is full it waits some time before trying again. Basically this function loops
            until the message is sent successfully or it receives termination signal from the main process.
        """

        while True:
            if not hub_to_scraper.full():
                hub_to_scraper.put(obj=request, block=False)
                break
            else:
                if console_log:
                    print("Unable to send scraping request!. Retrying...")
                check_main(main_to_all=main_to_all)
                time.sleep(1)


    def perform_full_refresh(main_to_all: mpr.Queue, hub_to_scraper: mpr.Queue, scraper_to_hub: mpr.Queue,
                              market_hub: MarketPlace):

        markets = market_hub.markets()

        for market in markets:
            scrape_request = ScrapeRequest(ID=request_generator.get_request_ID(),
                                           market_ID=market.ID(),
                                           categories=None)
            requests.append(scrape_request)
        
        for request in requests:
            market = market_hub.market(identifier=request.market_ID)
            send_or_wait(main_to_all=main_to_all, hub_to_scraper=hub_to_scraper, request=request)

            while True:
                while scraper_to_hub.empty():

                    check_main(main_to_all=main_to_all, timeout=0.001)

                response = scraper_to_hub.get(block=False)

                if(isinstance(response, list)):
                    
                    for product, _ in response:
                        process_product(product=product)

                        if product.name == "BILLA Špagetiny 500G":
                            pass
                        # try:
                        if not market.is_registered(product_name=product.name):

                            market.register_product(product=product)
                            if console_log:
                                print(f"Registered successfully: {{{product.name}}}")
                        else:
                            try:
                                if console_log:
                                    print(f"Product {{{product.name}}} already registered!")
                                market.update_product(product=product)
                            except IllegalProductState:
                                pass
                elif(isinstance(response, int)):
                    market.save_products(remove_if_outdated=True)
                    break




    def send_progress_signal(hub_to_gui: mpr.Queue, main_to_all: mpr.Queue, progress: int, console_log: bool = True):
        assert(0<=progress<=100)

        while hub_to_gui.full():
            print("Gui process queue full! Retrying...")
            check_main(main_to_all=main_to_all)
        
        hub_to_gui.put(obj=(PROGRESS_BAR_SIGNAL, progress), block=False)
    



    def check_update_interval_signals(gui_to_hub: mpr.Queue, interval: int, timeout: int = 1):

        try:
            signal = gui_to_hub.get(timeout=timeout)

            if signal[0] == UPDATE_INTERVAL_SIGNAL:
                return int(signal[1])
            
        except Empty:
            pass

        return interval


    
    os.chdir(parent_directory)
    signal.signal(signal.SIGINT, signal_handler)
    #start_market_hub(main_to_all=main_to_all, hub_to_scraper=hub_to_scraper, scraper_to_hub=scraper_to_hub, hub_to_gui=hub_to_qui)

    # loads all registered markets within the main market hub
    hub = MarketPlace(src_file=MARKET_CENTER_FILE['path'], console_log=console_log)   
    hub.load_markets()

    # loads all product data within the market hub but only when the lock is acquired, this is
    # because other processes
    with product_file_lock:
        hub.load_products()

    
    hub.update()
    markets = hub.markets()
    
    for market in markets:
        market.buffer(size=10000)

    global product_df
    product_df = hub.product_df() # pl.read_csv(hub.product_file())

    check_main(main_to_all=main_to_all)

    # analyzing training market
    send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=PRP.TRAINING_MARKET_ANALYSIS,
                         console_log=console_log)

    training_market = hub.training_market()
    request_missing_categories(market=training_market, console_log=console_log)
    
    send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=PRP.MARKETS_ANALYSIS,
                         console_log=console_log)


    for market in markets:
        if market.ID() == training_market.ID(): continue
        request_missing_categories(market=market)

    send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=PRP.SCRAPING_MISSING_DATA,
                         console_log=console_log)

    
    if requests:
        progress = PRP.SCRAPING_MISSING_DATA
        progress_rate = math.floor((PRP.UPDATING_DATA - PRP.SCRAPING_MISSING_DATA)
                                   /len(requests))

    # here we start sending  scraping requets
    while requests:
        processed_request = requests.pop(0)
        send_or_wait(main_to_all=main_to_all, hub_to_scraper=hub_to_scraper, request=processed_request)

        # in this loop, we wait until the request was finished successfully
        while True:
            if not scraper_to_hub.empty():

                try:
                    scraped_data = scraper_to_hub.get(block=False)
                except Exception:
                    pass

                if isinstance(scraped_data, list):
                    print("Received scraped data! Processing...")
                    
          
                    for product_data in scraped_data:
                        check_main(main_to_all=main_to_all, timeout=0.001)

                        product, market_ID = product_data
                        market = hub.market(identifier=market_ID)

                        process_product(product=product)
                        category = ProductCategory.NEURČENÁ
                        if market_ID == training_market.ID():
                            category = ProductCategorizer.categorize_by_mapping(product=product, mappings_file=CATEGORY_MAP_FILE['path'])
                        
                        try:
                            market.register_product(product=product, norm_category=category)
                            print(f"Registered successfully: {{{product.name}}}")
                        except IllegalProductState:
                            print(f"Product {{{product.name}}} already registered!")
                            
              

                elif isinstance(scraped_data, int):

                    if processed_request.ID == scraped_data:
                        print(f"Request {processed_request.ID} fulfilled!")

                        with product_file_lock:
                            hub.market(identifier=processed_request.market_ID).save_products()
                        
                        hub.update()

                        with product_file_lock:
                            hub.load_products()
                        send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=progress + progress_rate)
                        progress += progress_rate
                        break
                else:
                    if console_log:
                        print("Unsupported response type!")
            
            time.sleep(1.5)


    # send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=PRP.UPDATING_DATA)

    hub.load_products()
    
    product_df = hub.product_df()

    sorted_df = product_df.sort('updated_at')

    # firsly we check whether certain fraction of products are out-of-date
    update_limit_row = sorted_df.row(int((len(product_df)/100) * UPDATE_LIMIT))
    
    # we convert the string into a timestamp    
    timestamp = datetime.strptime(update_limit_row[PRODUCT_FILE['columns']['updated_at']['index']], "%Y-%m-%d %H:%M:%S")
    current_date = datetime.now()

    # now we get the update delay
    update_delay = current_date - timestamp
    categorizer = ProductCategorizer(market_hub=hub)

    # if the update delay has reached MAX_UPDATE_DALAY, request for exhaustive data update is sent
    # to GUI process
    if (update_delay.total_seconds())/60 > MAX_UPDATE_DELAY:
        if console_log:
            print("Detected a lot of out-of-date data! Sending request...")
        send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=PRP.UPDATING_DATA)
        
        # process waits until response is received
        while gui_to_hub.empty():
            check_main(main_to_all=main_to_all)

        response = gui_to_hub.get(block=False)

        # here user accepts Full Refresh
        if(isinstance(response, tuple) and response[1] == 1):
            
            perform_full_refresh(main_to_all=main_to_all, hub_to_scraper=hub_to_scraper,
                                 scraper_to_hub=scraper_to_hub, market_hub=hub)
            # hub.remove_local_products()
            # return start(main_to_all, hub_to_scraper, scraper_to_hub, hub_to_gui,
            #     gui_to_hub, product_file_lock)
        
        
        # send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=PRP.UPDATING_DATA)

        

        
    
    send_progress_signal(hub_to_gui=hub_to_gui, main_to_all=main_to_all, progress=PRP.FINISHING_POINT)
    hub.update()

    if console_log:
        print("Starting update process...")
    processed_categories: List[str] = []
    

    while True:
        # we update product_df to get latest version of dataframe
        product_df = hub.product_df()

        # sorting the product dataframe by the updated_at attribute
        # we find the earliest updated record in dataframe
    
        if console_log:
            print(f"The difference between {current_date} and {timestamp} is: {update_delay.total_seconds()/60}")


        earliest_updated = sorted_df.filter(sorted_df['query_string_ID'].is_in(processed_categories).not_()).head(1)
        
        market = earliest_updated['market_ID']
        processed_categories.append(earliest_updated['query_string_ID'][0])
        
        # here we store products belonging to the same category as the earliest updated product
        # products which will remain here after update process is finished are removed from the
        # market
        category_products = product_df.filter(product_df['query_string_ID'] == earliest_updated['query_string_ID'])['name'].to_list()
        
        if console_log:
            print(f"Updating category {earliest_updated['query_string_ID'][0]} of market {earliest_updated['market_ID'][0]}.")
    

        # now we create a ScrapeRequest isntance and send it to the scraper process
        processed_request = ScrapeRequest(ID=request_generator.get_request_ID(), market_ID=earliest_updated['market_ID'][0], categories=[earliest_updated['query_string_ID'][0]])
        
        with product_file_lock:
            hub.market(identifier=processed_request.market_ID).load_products()
        
        send_or_wait(main_to_all=main_to_all, hub_to_scraper=hub_to_scraper, request=processed_request)


        # here we wait until the request is fulfilled
        while True:
            # here we wait until we receive and answer
            while scraper_to_hub.empty():
                check_main(main_to_all=main_to_all)

            response = scraper_to_hub.get(block=False)

            # case in which we should receive updated product data
            if isinstance(response, list):
                if console_log:
                    print("Received scraped data! Processing...")
                
                for product, market_ID in response:
                    check_main(main_to_all=main_to_all, timeout=0.001)
                    update_interval = check_update_interval_signals(gui_to_hub=gui_to_hub,
                                                                    interval=update_interval,
                                                                    timeout=0.001)
                    
                    while update_interval == -1:
        
                        check_main(main_to_all=main_to_all)
                        update_interval = check_update_interval_signals(gui_to_hub=gui_to_hub, interval=update_interval)

                    process_product(product=product)

                    if market_ID == processed_request.market_ID:
                        market = hub.market(identifier=market_ID)
                        try:
                            market.update_product(product=product)

                            if console_log:
                                print(f"Updated successfully: {product.name}")
                            try:
                                # we remove this product as it has been updated and is still at disposal
                                category_products.remove(product.name)
                            except ValueError:
                                pass


                        # we received a new data which are not yet registered
                        except IllegalProductState:
                            
                            if market.ID() == training_market.ID():
                                category = categorizer.categorize_by_mapping(product=product, mappings_file=CATEGORY_MAP_FILE['path'])
                            else:
                                category = categorizer.categorize(product=product)

                            process_product(product=product)
                            try:
                                
                                market.register_product(product=product, norm_category=category)
                                if console_log:
                                    print(f"Registered successfully: {{{product.name}}}")
                            except IllegalProductState:
                                if console_log:
                                    print(f"Product {{{product.name}}} already registered!")

                    else:
                        if console_log:
                            print("Received response contains invalid market ID!")
            
            
            # case in which we should receive the ScrapeProcessTerminationSignal
            elif isinstance(response, int):
                
                # here all updated data have to be saved to the product file and market hub
                # has to be refreshed
                if processed_request.ID == response:
                    market = hub.market(identifier=processed_request.market_ID)

                    if category_products:
                        market.remove_products(identifiers=category_products)
                    
                    if console_log:
                        print(f"Request {processed_request.ID} fulfilled!")

                    while hub_to_gui.full():
                        if console_log:
                            print("GUI's queue is full! Retrying...")
                        check_main(main_to_all=main_to_all)
                    
                    hub_to_gui.put(obj=(UPDATE_PRODUCTS_SIGNAL,), block=False)

                    while gui_to_hub.empty() or gui_to_hub.get(block=False)[0] != UPDATE_PRODUCTS_SIGNAL:
                        check_main(main_to_all=main_to_all, timeout=0.0001)
                        
                        


                    with product_file_lock:
                        market.save_products()
                        hub.update()
                        hub.load_products()
                    break
                else:
                    if console_log:
                        print("Received invalid Scrape Process Termination Signal!")
            else:
                if console_log:
                    print("Unsupported response type!")
            
            check_main(main_to_all=main_to_all)


        time.sleep(update_interval)


if __name__ == "__main__":

    print("Start this script as a subprocess by running start() function.")
    
 