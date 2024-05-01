
import sys, os
import signal
import multiprocessing as mpr
from typing import List
import queue

# Set the starting point to the directory containing the script
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)


# Move up two directories to reach the parent directory (AOSS)
parent_directory = os.path.abspath(os.path.join(script_directory, '..'))
sys.path.append(parent_directory)

MAIN_TERMINATION_SIGNAL = "-end"
CONSOLE_LOG = False



from config_paths import *

from AOSS.processes.IPC import GUI_TERMINATION_SIGNAL
from AOSS.processes.DPMP import start as dpmp_start
from AOSS.processes.DSPP import start as dspp_start
from AOSS.processes.GUIP import start as gui_start

main_to_all = mpr.Queue(maxsize=5)
gui_to_main = mpr.Queue(maxsize=5)
hub_to_scraper = mpr.Queue(maxsize=5)
scraper_to_hub = mpr.Queue(maxsize=5)
hub_to_qui = mpr.Queue(maxsize=5)
gui_to_hub = mpr.Queue(maxsize=5)
product_file_lock = mpr.Lock()


processes: List[mpr.Process] = []

def terminate(signal):
    signal.value = 1

    for process in processes:
        process.join()

    processes.clear()
    exit(0)



def signal_handler(signum, frame):


    if signum == 2:
        print("Ctrl + C received. Terminating subprocesses.")
        terminate()



def check_gui(signal, timeout: float = 1.5):

    try:
        if gui_to_main.get(block=False, timeout=timeout) == GUI_TERMINATION_SIGNAL:
        
            terminate(signal=signal)
        
    except queue.Empty:
        pass

def launch_subprocesses():

    manager = mpr.Manager()
    shared_termination_signal = manager.Value('i', 0)
    
    
    market_hub = mpr.Process(target=dpmp_start, args=(shared_termination_signal, hub_to_scraper, scraper_to_hub, hub_to_qui,
                                                     gui_to_hub, product_file_lock, CONSOLE_LOG))
    
    market_hub.start()
    processes.append(market_hub)

    scraper = mpr.Process(target=dspp_start, args=(shared_termination_signal, scraper_to_hub, hub_to_scraper,
                                                   CONSOLE_LOG))
    scraper.start()
    processes.append(scraper)
    

    gui = mpr.Process(target=gui_start, args=(shared_termination_signal, gui_to_main, hub_to_qui, gui_to_hub,
                                              product_file_lock, CONSOLE_LOG))
    gui.start()
    processes.append(gui)

    while True:
        check_gui(signal=shared_termination_signal)




if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal_handler)
    launch_subprocesses()

    