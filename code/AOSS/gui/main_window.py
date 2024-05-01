from tkinter import *

import multiprocessing as mpr
import os, sys
from typing import List, Literal

# Set the starting point to the directory containing the script
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)

# Move up two directories to reach the parent directory (AOSS)
parent_directory = os.path.abspath(os.path.join(script_directory, '..', '..'))
sys.path.append(parent_directory)

import config_paths as cfg

from AOSS.gui.shopping_list import ShoppingListFrame

from AOSS.gui.product_specification import ProductSpecificationMenu

from AOSS.gui.market_explorer import MarketExplorerFrame
from AOSS.gui.settings import SettingsFrame

from AOSS.structure.shopping import MarketPlace
from AOSS.other.exceptions import InvalidApplicationState



class MainWindow(Frame):

    SECTION_TITLES_EN = ('Specify Product', 'Explore Markets', 'Shopping List', 'Adjust Settings')
    SECTION_TITLES_SK = ('Špecifikuj produkt', 'Hľadaj obchody', 'Nákupný zoznam', 'Zmeniť nastavenia')

    def on_key_press(self, event, main_view):

        key_pressed = event.keysym

        if key_pressed == "Delete":
            main_view.market_explorer_window.delete_product()
    
    def change_language(self, language: Literal['EN', 'SK']):
        self.language = language
    


    def __init__(self, *args, root: Tk, market_hub, gui_to_hub: mpr.Queue,
                 app_name: str, app_version: str, is_beta: bool = False, main_menu_items: List[str],
                 language: Literal['EN', 'SK'] = 'EN', **kw):
        super(MainWindow, self).__init__(*args, **kw)
        
        self.language = language
        self.cur_section_titles = self.SECTION_TITLES_EN if self.language == 'EN' else self.SECTION_TITLES_SK



        self.root = root
        self.market_hub = market_hub

        self.main_menu_panel = MainMenu(self, app_name=app_name, app_version=app_version, is_beta=is_beta,
                                         items=main_menu_items, parent=self, bg='skyblue')
        self.main_menu_panel.pack(side='left', fill='y', expand=False)

        self.main_window = Frame(self, bg='lightblue', width=50)

        self.main_window.pack(side='left', fill='both', expand=True)


        self.list_frame = Frame(self.main_window, bg='skyblue')
        self.list_frame.pack(side='left', fill='both', expand=True)

        self.market_explorer_window = None

        self.shopping_list_window = ShoppingListFrame(self.list_frame,
                                                      text=self.cur_section_titles[0],
                                                      font=('Arial', 17, 'bold'),
                                                      bg='skyblue',
                                                      language=self.language,
                                                      on_delete=lambda item: self.market_explorer_window.delete_product(item))
        self.shopping_list_window.pack(side='right', fill='y', expand=False, pady=6, padx=(3, 5))
        
        market_hub = MarketPlace(src_file=cfg.MARKET_CENTER_FILE['path'])
        market_hub.load_markets()
        market_hub.load_products()



        self.market_explorer_window = MarketExplorerFrame(self.list_frame,
                                                          bg='skyblue',
                                                    root=self.list_frame,
                                                    market_hub=self.market_hub,
                                                    shopping_list_frame=self.shopping_list_window,
                                                    text=self.cur_section_titles[1],
                                                    font=("Arial", 17, 'bold'),
                                                    language=self.language)
        



        self.specification_window = ProductSpecificationMenu(self.list_frame,
                                                text=self.cur_section_titles[2],
                                                font=('Arial', 17, 'bold'),
                                                root=self.root,
                                                shopping_list_frame=self.shopping_list_window,
                                                market_explorer_frame=self.market_explorer_window,
                                                bg='skyblue',
                                                language=self.language)
        self.specification_window.pack(side='right', fill='both', expand=True, pady=6, padx=(0, 3))


        # self.explorer_frame = Frame(self.main_window)

       
        self.settings_frame = SettingsFrame(self.main_window, gui_to_hub=gui_to_hub, section_title=self.cur_section_titles[3],
                                            on_language_change=self.change_language)

        #market_explorer_window 
    
    def exit(self):
        self.quit()
        self.root.quit()


class MainMenu(Frame):

    ITEM_COUNT = 4
    BUTTON_Y_PAD = 2


    def __init__(self, *args, parent: MainWindow, app_name: str, app_version: str, is_beta: bool = False,
                 items: List[str], **kw):
        super(MainMenu, self).__init__(*args, **kw)
        
        self.parent = parent

        if self.ITEM_COUNT > len(items):
            raise InvalidApplicationState(message=f"Invalid amount of provided main menu items! At least {self.ITEM_COUNT} required!")
        
        self.items = items

            
        


  
        # ----- Layout Configuration ------ #
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        app_title = app_name + " v" + app_version

        self.app_name_text_wrapper = Frame(self, bg='deepskyblue')
        self.app_name_text_wrapper.pack(side='top', fill='x', expand=False, pady=(51, 30))

        self.app_name_text = Text(self.app_name_text_wrapper, width=5, height=1, font=('Arial', 17, 'bold'), bg='deepskyblue')
        self.app_name_text.insert("end", "      ")

        if not is_beta:
            self.app_name_text.insert("end", "      ")

        self.app_name_text.tag_config("black", foreground='black')
        self.app_name_text.tag_config("red", foreground='red')
        self.app_name_text.insert("end", app_title, "black")

        if is_beta:
            self.app_name_text.insert("end", ' BETA', 'red')
        
        self.app_name_text.config(state='disabled')

        # self.app_name_label = Label(self, text=app_title, font=('Arial', 17, 'bold'),  bg='deepskyblue')
        self.app_name_text.pack(side='top', fill='x', expand=False, pady=10)
        
        
        ##self.shopping_list_option = Frame(self, bg='aqua')
       # self.shopping_list_option.pack(side='top', fill='x', expand=False, pady=(6, self.BUTTON_Y_PAD))

        
        
        # ----- Specification Option Configuration ----- #
        self.shopping_list_icon = PhotoImage(file=cfg.SHOPPING_CART_ICON).subsample(13, 13)
        self.shopping_list_option = Button(self, pady=10, padx=9, bg='aqua', text=self.items[0], font=('Arial', 15, 'bold'),
                                           image=self.shopping_list_icon,
                                           compound='right',
                                           anchor='e',
                                           state='disabled',
                                           command=self.to_shopping_list)
        self.shopping_list_option.pack(side='top', fill='x', expand=False, pady=(0,2))
        

        # ----- Explorer Option Configuration ----- #
        self.magnifier_icon = PhotoImage(file=cfg.MAGNIFIER_ICON).subsample(19, 19)
        self.explorer_option = Button(self,  pady=12, padx=12, bg='aqua', text=self.items[1] + " ", font=('Arial', 15, 'bold'),
                                      image=self.magnifier_icon,
                                      compound='right',
                                      anchor='e',
                                      command=self.to_market_explorer)
        self.explorer_option.pack(side='top', fill='x', expand=False, pady=self.BUTTON_Y_PAD)


        

        # ----- Settings Option Configuration ----- #
        self.gear_icon = PhotoImage(file=cfg.GEAR_ICON).subsample(19, 19)
        self.settings_option = Button(self, pady=12, padx=12, bg='aqua', text=self.items[2] + " ", font=('Arial', 15, 'bold'),
                                      image=self.gear_icon,
                                      compound='right',
                                      anchor='e',
                                      command=self.to_settings_panel)
        self.settings_option.pack(side='top', fill='x', expand=False, pady=self.BUTTON_Y_PAD)



        # ----- Exit Option Configuration ----- #

        self.exit_icon = PhotoImage(file=cfg.EXIT_ICON).subsample(19, 19)
        self.exit_option = Button(self, pady=12, padx=12, bg='aqua', text=self.items[3] + " ", font=('Arial', 15, 'bold'),
                                  image=self.exit_icon,
                                  compound='right',
                                  anchor='e',
                                  command=self.exit)
        self.exit_option.pack(side='top', fill='x', expand=False, pady=self.BUTTON_Y_PAD)

        self.selected_option = self.shopping_list_option

    
    def exit(self):
        self.quit()
        self.parent.exit()


    def to_market_explorer(self):

        for child in self.parent.main_window.winfo_children():
            child.pack_forget()

        self.parent.specification_window.modal_window.withdraw()
        self.parent.specification_window.pack_forget()
        self.parent.market_explorer_window.pack(side='right', fill='both', expand=True, pady=6, padx=(0, 3))
        self.parent.list_frame.pack(side='left', fill='both', expand=True)

        self.selected_option.config(state='normal')
        self.explorer_option.config(state='disabled')
        self.selected_option = self.explorer_option

    

    def to_shopping_list(self):
        for child in self.parent.main_window.winfo_children():
            child.pack_forget()

        self.parent.market_explorer_window.pack_forget()
        self.parent.specification_window.pack(side='right', fill='both', expand=True, pady=6, padx=(0, 3))
        self.parent.list_frame.pack(side='left', fill='both', expand=True)

        self.selected_option.config(state='normal')
        self.shopping_list_option.config(state='disabled')
        self.selected_option = self.shopping_list_option


    
    def to_settings_panel(self):
        for child in self.parent.main_window.winfo_children():
            child.pack_forget()
        
        self.parent.settings_frame.pack(side='left', fill='both', expand=True, padx=(0, 5), pady=6)

        self.selected_option.config(state='normal')
        self.settings_option.config(state='disabled')
        self.selected_option = self.settings_option

        self.parent.main_window.config(bg='skyblue')

