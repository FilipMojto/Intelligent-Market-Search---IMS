from tkinter import *
from tkinter import ttk
from tkinter import messagebox

import threading
from typing import List, Dict, Literal

#import math

import config_paths as cfg

from AOSS.gui.shopping_list import ShoppingListFrame, ShoppingListItem
from AOSS.gui.utils import CircularProgress
from AOSS.structure.shopping import MarketPlace, ProductCategory
from AOSS.components.marexp import MarketExplorer
from AOSS.other.utils import TextEditor

BACKGROUND = 'lightblue'

def bind_widgets_recursive(widget, event, handler):
    widget.bind(event, handler)
    for child in widget.winfo_children():
        bind_widgets_recursive(child, event, handler)




class Table(Frame):
    def __init__(self, *args, rows: int, columns: int, **kw):
        super(Table, self).__init__(*args, **kw)

        self.rows = rows
        self.columns = columns
        self.cells: List[List[Label]] = []

        self.config(bg='lightgrey')

        for i in range(columns):
            self.columnconfigure(i, weight=1)


        for i in range(rows):
            self.cells.append([])
            self.rowconfigure(i, weight=1)

            for g in range(columns):
                self.cells[i].append(Label(self, text="", font=("Arial", 13)))
                self.cells[i][g].grid(row=i, column=g, sticky="NSEW", padx=3, pady=3)
    
    def col_proportion(self, values: tuple[int, ...]):

        if len(values) != self.columns:
            raise ValueError("Invalid amount of columns!")
        
        for i in range(self.columns):
            self.columnconfigure(index=i, weight=values[i])
        
        

    
    def insert_value(self, row: int, column: int, value: str | int | float | PhotoImage | Widget):

        if isinstance(value, PhotoImage):
            self.cells[row][column].config(text="", image=value, compound='center')
        elif isinstance(value, str):
            self.cells[row][column].config(text=value)
        elif isinstance(value, int) or isinstance(value, float):
            self.cells[row][column].config(text=str(value))            
        elif isinstance(value, Widget):
            self.cells[row][column].destroy()
            self.cells[row][column] = value
            self.cells[row][column].grid(row=row, column=column, sticky="NSEW")

            #print(self.cells[row][column].grid_info())
        else:
            raise TypeError("Unkown type of value!")
        
        




class ExplorationTable(Frame):

    ROW_COUNT = 4
    COLUMN_NAMES_EN = ('Total Price', 'Total Availability (%)', 'Recommended')
    COLUMN_NAMES_SK = ('Celková cena', 'Celková dostupnosť (%)', 'Odporúčanie')

    def __init__(self, *args, market_hub: MarketPlace, language: Literal['EN', 'SK'] = 'EN', **kw):
        super(ExplorationTable, self).__init__(*args, **kw)
        
        self.language = language
        self.cur_column_names = self.COLUMN_NAMES_EN if self.language == 'EN' else self.COLUMN_NAMES_SK

        self.market_hub = market_hub
        self.markets = market_hub.markets()


        self.cells: List[List[ tuple[StringVar, Label] ]] = []
        market_count = len(self.markets)



        for i in range(self.ROW_COUNT):
            self.cells.append([])

            pad_y = 2

            if i == 0:
                pad_y = (5, 2)
            elif i == self.ROW_COUNT - 1:
                pad_y = (2, 5)


            for g in range(market_count + 1):

                var = StringVar()
                var.set(value="")
                label = Label(self, textvariable=var, font=("Arial",  12, "bold"))

                pad_x = 2

                if g == 0:
                    pad_x = (5, 2)
                elif g == market_count:
                    pad_x = (2, 5)

                label.grid(row=i, column=g, sticky="NSEW", padx=pad_x, pady=pad_y)

                self.cells[i].append( (var, label) )

        for i in range(4):
            self.columnconfigure(i, weight=1, minsize=100)

        for g in range(4):
            self.rowconfigure(g, weight=1)

    
        self.cells[1][0][0].set(value=self.cur_column_names[0])
        self.cells[1][0][1].config(font=('Arial', 13, 'bold'))

        self.cells[2][0][0].set(value=self.cur_column_names[1])
        self.cells[2][0][1].config(font=('Arial', 13, 'bold'))

        self.cells[3][0][0].set(value=self.cur_column_names[2])
        self.cells[3][0][1].config(font=('Arial', 13, 'bold', 'underline'))


        for index, market in enumerate(self.markets):
            self.cells[0][index + 1][0].set(value=market.name().lower())



    def insert_value(self, row: int, col: int, value: object | PhotoImage):
        
        # here we insert an image or icon instead of text
        if isinstance(value, PhotoImage):
            self.cells[row][col][0].set("")
            self.cells[row][col][1].config(image=value, compound='center')
        else:
            self.cells[row][col][0].set(value=value)




class ExplorerView(Frame):
    BACKGROUND = 'lightblue'
    FONT = ('Arial', 13)
    
    EXPL_TABLE_ORDERING_LABEL_EN = 'Evaluate by: '
    EXPL_TABLE_ORDERING_LABEL_SK = 'Vyhodnoť podľa: '
    
    EXPL_TABLE_ORDERING_OPTIONS_EN = ('Price&Availability', 'Price', 'Availability Rate')
    EXPL_TABLE_ORDERING_OPTIONS_SK = ('Ceny a dostupnosti', 'Ceny', 'Miery dostupnosti')
    PRODUCT_DETAIL_TITLE_EN = 'Product Details'
    PRODUCT_DETAIL_TITLE_SK = 'Detaily o produkte'

    def __init__(self, *args, market_hub: MarketPlace, language: Literal['EN', 'SK'] = 'EN',
                  **kw):

        super(ExplorerView, self).__init__(*args, **kw)
        self.language = language
        self.cur_expl_table_ordering_options = (self.EXPL_TABLE_ORDERING_OPTIONS_EN if self.language == 'EN' else
                                                self.EXPL_TABLE_ORDERING_OPTIONS_SK)
        self.cur_product_detail_title = self.PRODUCT_DETAIL_TITLE_EN if self.language == 'EN' else self.PRODUCT_DETAIL_TITLE_SK
        self.cur_expl_table_ordering_label = (self.EXPL_TABLE_ORDERING_LABEL_EN if self.language == 'EN' else
                                          self.EXPL_TABLE_ORDERING_LABEL_SK)
        
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=10)
        self.columnconfigure(0, weight=1)

        self.expl_table_control_panel = Frame(self, background=self.BACKGROUND)
        self.expl_table_control_panel.grid(row=0, column=0, sticky="NSEW")

        style = ttk.Style()
        style.configure('Custom.TCombobox', font=("Helvetica", 20)) 

        self.expl_table_ordering_options = ttk.Combobox(self.expl_table_control_panel, background=self.BACKGROUND,
                                                         font=self.FONT, state='readonly',
                                                         width=17)
        self.expl_table_ordering_options.config(style='Custom.TCombobox')


        self.expl_table_ordering_options['values'] = self.cur_expl_table_ordering_options
        self.expl_table_ordering_options.current(0)
        self.expl_table_ordering_options.pack(side='right', ipady=10, padx=5, pady=(5, 4))
        

        self.expl_table_ordering_options_label = Label(self.expl_table_control_panel, background=self.BACKGROUND, text=self.cur_expl_table_ordering_label, font=self.FONT)
        self.expl_table_ordering_options_label.pack(side='right', pady=(5, 2))



        self.table = ExplorationTable(self, bg='black', market_hub=market_hub, language=self.language)
        self.table.grid(row=1, column=0, sticky="NSEW", padx=5, pady=(0, 5))

        self.detailed_results = LabelFrame(self,
                                           bg=BACKGROUND,
                                           text=self.cur_product_detail_title,
                                           font=('Arial', 15, 'bold'))
        
        self.detailed_results.grid(row=2, column=0, sticky="NSEW", pady=(58, 5))
        self.detailed_results.rowconfigure(0, weight=1, minsize=50)
        self.detailed_results.rowconfigure(1, weight=200)
        self.detailed_results.columnconfigure(0, weight=1)

        self.detailed_results_table = Table(self.detailed_results, rows=4, columns=3)
        self.detailed_results_table.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        self.detailed_results_table.col_proportion(values=(2, 40, 1))


        self.detailed_results_padding = Frame(self.detailed_results, bg=BACKGROUND)
        self.detailed_results_padding.grid(row=1, column=0, sticky="NSEW")
    
    def bind_options(self, ordering_options_selected):
        self.expl_table_ordering_options.bind("<<ComboboxSelected>>", ordering_options_selected)

    



class MarketExplorerFrame(LabelFrame):
    BUTTON_TEXTS_EN = ('   search',)
    BUTTON_TEXTS_SK = ('   hľadať',)
    PRODUCT_DETAILS_COLS_NAMES_EN = ('Market', 'Product', 'Price')
    PRODUCT_DETAILS_COLS_NAMES_SK = ('Obchod', 'Produkt', 'Cena')

    def __init__(self, *args, root: Tk, market_hub: MarketPlace, shopping_list_frame: ShoppingListFrame,
                 language: Literal['EN', 'SK'] = 'EN',
                 **kw):
        super(MarketExplorerFrame, self).__init__(*args, **kw)
        
        self.language = language
        self.cur_button_texts = self.BUTTON_TEXTS_EN if self.language == 'EN' else self.BUTTON_TEXTS_SK
        self.cur_product_details_cols_names = (self.PRODUCT_DETAILS_COLS_NAMES_EN if self.language == 'EN' else
                                               self.PRODUCT_DETAILS_COLS_NAMES_SK)

        self.accept_icon = PhotoImage(file=cfg.ACCEPT_ICON).subsample(18, 18)
        self.decline_icon = PhotoImage(file=cfg.DECLINE_ICON).subsample(18, 18)
        self.search_icon = PhotoImage(file=cfg.SEARCH_ICON).subsample(18, 18)
        
        self.root = root
        self.shopping_list = shopping_list_frame
        self.market_hub = market_hub
        self.markets = market_hub.markets()
        self.market_explorer = MarketExplorer(market_place=market_hub, alternatives=5)

        self.product_items = shopping_list_frame.product_list.items
        # self.product_target_mappings: Dict[str, int] = {}
        # self.product_items: List[ShoppingListItem] = []
        self.explorations: List[List[MarketExplorer.Exploration]] = []
    

        # ---- Frame Configuration ---- #

        self.rowconfigure(0, weight=11)
        self.rowconfigure(1, weight=200)
        self.rowconfigure(2, weight=10, minsize=60)
        self.columnconfigure(0, weight=1)

        # ---- ExplorerView Configuration ---- #

        self.best_markets: List[str] = []

        self.explorer_view = ExplorerView(self, market_hub=market_hub, bg=BACKGROUND, language=self.language,
                                          )
        self.explorer_view.bind_options(ordering_options_selected=self.refresh_recommendation)
        self.explorer_view.grid(row=0, column=0, sticky="NSEW", pady=(15, 70))


        self.padding = Frame(self, background='skyblue')
        self.padding.grid(row=1, column=0, sticky="NSEW")

        # ---- ControlPanel Configuration ---- #

        self.control_panel = Frame(self, bg='lightblue')
    
        self.control_panel.grid(row=2, column=0, sticky="NSEW")#,pady=(20, 0))
        self.control_panel.rowconfigure(0, weight=1)
        self.control_panel.columnconfigure(0, weight=1)
        self.control_panel.columnconfigure(1, weight=1)
        self.control_panel.grid_propagate(0)
        

        self.search_button = ttk.Button(self.control_panel,
                                    text=self.cur_button_texts[0],
                                    style='TButton',
                                    command=self.explore_markets,
                                    padding=(0, 7),
                                    image=self.search_icon,
                                    compound='left')
        self.search_button.grid(row=0, column=1, sticky="EWS", padx=5, pady=(8, 6))

        self.search_bar = CircularProgress(self.control_panel, width=30, height=30)

        self.explorer_view.detailed_results_table.insert_value(row=0, column=0, value=self.cur_product_details_cols_names[0])
        self.explorer_view.detailed_results_table.insert_value(row=0, column=1, value=self.cur_product_details_cols_names[1])
        self.explorer_view.detailed_results_table.insert_value(row=0, column=2, value=self.cur_product_details_cols_names[2])

        self.search_executed: bool = False
        self.next_target_ID: int = 1
    

    
    def delete_product(self, item = None):

        if item is None:
            item = self.shopping_list.product_list.remove_selected_item(return_=True)
        
        if item is None:
            return
        
    
        # if not self.shopping_list.product_list.items:
        #     self.search_button.config(state='disabled')


        self.market_explorer.remove_target(ID=item.details.ID)
        # self.product_items.remove(item)
    

    def combobox_selected(self, event, box: ttk.Combobox, index: int):
        info = box.grid_info()
        cur_price = float(self.explorer_view.detailed_results_table.cells[info['row']][info['column'] + 1].cget('text'))
        new_price = self.product_price_mappings[info['row'] - 1][box.get()]
        market = self.explorer_view.detailed_results_table.cells[info['row']][info['column'] - 1].cget('text')

        for i in range(len(self.markets)):
            
            if self.explorer_view.table.cells[0][i + 1][0].get() == market:

                original_val = float(self.explorer_view.table.cells[1][i + 1][0].get())

                self.explorer_view.table.insert_value(row=1, col=i + 1, value=round(original_val + (new_price - cur_price), 2))


        self.explorer_view.detailed_results_table.insert_value(row=info['row'], column=info['column'] + 1, value=
                                              self.product_price_mappings[info['row'] - 1][box.get()])
        
        row_i = box.grid_info()['row']
        market_name = self.explorer_view.detailed_results_table.cells[row_i][0].cget("text").upper()


        market_ID = None
        for market in self.markets:
            if market.name() == market_name:
                market_ID = market.ID()
                break
        else:
            raise ValueError("Unkown market name!")

     
        self.market_explorer.swap_expl_products(market_ID=market_ID, expl_1_index=0, expl_2_name=box.get(), product_index=index)
        self.refresh_recommendation()
        



    def show_product_details(self, event, item: ShoppingListItem, target_ID: int):
        item.on_item_clicked(event=event)
        

        product_explorations: List[List[str]] = []
        prices: List[List[float]] = []

        market_len = len(self.markets)
        alternative_limit = self.market_explorer.get_limit()

        self.product_price_mappings: List[Dict[str, float]] = []

        for i in range(market_len):
            self.product_price_mappings.append({})

        for i in range(market_len):
            product_explorations.append([])
            prices.append([])

        markets = []
       # prices = []

        for i in range(market_len):
            
            #k = (i * 5) + 5

            markets.append(self.explorations[i][0].market_ID)
            
            # try:
            #     prices[i].append(self.explorations[i][0].product_data[0][1].price)
            # except IndexError:
            #     # No products found in the first exploration
            #     prices[i].append("---")
                

            for g in range(alternative_limit):
                expl = self.explorations[i][g]
                
                prod_data = None

                for data in expl.product_data:
                    if data[0] == target_ID:
                        prod_data = data


                try:
                    self.product_price_mappings[i][prod_data[1].name] = prod_data[1].price

                    product_explorations[i].append(prod_data[1].name)
                    prices[i].append(prod_data[1].price)
                except (IndexError, AttributeError):
                    product_explorations[i].append("---")
                    prices[i].append("---")
                    # no products were found
                    pass
                # except TypeError:
                #     product_explorations[i].append("---")
                #     prices[i].append("---")
                #     #
        

            # for g in range(i * 5, (i * 5) + 5):
                
            #     expl = self.explorations[g]
            #     self.product_price_mappings[i][expl.products[index][0].name] = expl.products[index][0].price
            #     products[i].append(expl.products[index][0].name)
            #     prices[i].append(expl.products[index][0].price)


                # for index, product in enumerate(expl.products):

                    
                #     products[index % len(self.product_data)] = product[0].name


        combo_boxes = []




        for i in range(market_len):
            box = ttk.Combobox(self.explorer_view.detailed_results_table, state='readonly')
            #text = products[i]

            # if no products were found, we
            box['values'] = product_explorations[i]
            
            try:
                box.set(box['values'][0])
            except IndexError:
                # No products were found
                pass
  
            
            box.bind('<<ComboboxSelected>>', lambda event, box=box: self.combobox_selected(event, box=box, index=target_ID))
   
            combo_boxes.append(box)


        for i, market in enumerate(markets):
            self.explorer_view.detailed_results_table.insert_value(row=i + 1, column=0,
                                                                    value=self.market_hub.market(
                                                                        identifier=market
                                                                    ).name().lower())
            self.explorer_view.detailed_results_table.insert_value(row=i + 1, column=1,
                                                                    value=combo_boxes[i])
            self.explorer_view.detailed_results_table.insert_value(row=i + 1, column=2,
                                                                    value=prices[i][0])

        # for index, expl in enumerate(self.exploration):
            
        #     if index % (5 * len(self.product_data)) == 0:
        #         products.clear()
        #         self.explorer_view.detailed_results_table.insert_value(row=index + 1, column=0,
        #                                                             value=self.market_hub.market(identifier=expl.market_ID).name().lower())
        #     else:



        # for index, expl in enumerate(self.exploration):
        #     self.explorer_view.detailed_results_table.insert_value(row=index + 1, column=0,
        #                                                             value=self.market_hub.market(identifier=expl.market_ID).name().lower())

        #     combo_box = Combobox(self.explorer_view.detailed_results_table)

        #     products = []

        #     for product in enumerate(expl.products):
        #         products.append()

        #     #acombo_box['values'] = tuple(expl.)


        #     self.explorer_view.detailed_results_table.insert_value(row=index + 1, column=1,
        #                                                            value=expl.products[item.ID - 1][0].name)
        #     self.explorer_view.detailed_results_table.insert_value(row=index + 1, column=2,
        #                                                            value=expl.products[item.ID - 1][0].price)



    def create_handler(self, item, index):
        return lambda event: self.show_product_details(event=event, target_ID=index, item=item)    


    def refresh_recommendation(self, _ = None):
        if not self.search_executed:
            return
        
        self.best_markets.clear()
        best_metric = -1

        mode = self.explorer_view.expl_table_ordering_options.current()
      

        if mode == 0:
            # here evaluation is based on general metric of explorations, thus on price and availability as well

            for i  in range(len(self.explorations)):
                first_expl = self.explorations[i][0]

                if not self.best_markets or first_expl.general_metric > best_metric:
                    self.best_markets.clear()
                    self.best_markets.append( self.explorer_view.table.cells[0][first_expl.market_ID][0].get())
                    best_metric = first_expl.general_metric
                    
                elif first_expl.general_metric == best_metric:
                    self.best_markets.append( self.explorer_view.table.cells[0][first_expl.market_ID][0].get())
        elif mode == 1:
            # here evalulation is based solely on the total price of the explorations

            for i in range(len(self.markets)):
                cur_metric = float(self.explorer_view.table.cells[1][i + 1][0].get())
                if not self.best_markets or best_metric == cur_metric:
                    self.best_markets.append( self.explorer_view.table.cells[0][i + 1][0].get())
                    best_metric = cur_metric
                elif best_metric > cur_metric:
                    self.best_markets.clear()
                    self.best_markets.append( self.explorer_view.table.cells[0][i + 1][0].get())
                    best_metric = cur_metric
        elif mode == 2:
            # pass
            for i in range(len(self.markets)):
                cur_metric = float(self.explorer_view.table.cells[2][i + 1][0].get())
                if not self.best_markets or best_metric == cur_metric:
                    self.best_markets.append( self.explorer_view.table.cells[0][i + 1][0].get())
                    best_metric = cur_metric
                elif best_metric < cur_metric:
                    self.best_markets.clear()
                    self.best_markets.append( self.explorer_view.table.cells[0][i + 1][0].get())
                    best_metric = cur_metric

                


        
        for i in range(len(self.explorations)):
            if self.explorer_view.table.cells[0][i + 1][0].get() in self.best_markets:
                self.explorer_view.table.insert_value(row=3, col=i + 1, value=self.accept_icon)
            else:
                self.explorer_view.table.insert_value(row=3, col=i + 1, value=self.decline_icon)

    def explore_product(self, item: ShoppingListItem):
        """
            New product is prepared for exploration. It receives specification based on the user input
            stored in the provided ShoppingItemDetails instance. It is also assigned a unique target identifier.
        """
        product_name = TextEditor.standardize_str(item.details.name)
        category = None if item.details.category == 0 else ProductCategory(value=item.details.category)
        item_data = [MarketExplorer.ExplorationParams(target_id=self.next_target_ID,
                                                      product_name=product_name,
                                                      product_category=category,
                                                      required_quantity=item.details.amount,
                                                      categorization=item.details.category_search_mode,
                                                      weight_unit=item.details.weight_unit,
                                                      weight=item.details.weight)]
        item.details.target_ID = self.next_target_ID
        
        

        self.next_target_ID += 1
        
        self.market_explorer.explore(product_list=item_data)

    def is_bound(self, widget, event):
        """
        Check if a widget is bound to a certain event.
        """

        bindtags = widget.bindtags()

        for tag in bindtags:
            bind_info = widget.bind_class(tag, None)

            if event in bind_info:
                return True

        return False

    # def is_bound_2(self, widget):
    #     existing_bindings = widget.bind("<Button-1>")
    #     if existing_bindings and str(existing_bindings) == str(widget.bind(on_button_click)):
    #         print("Event is already bound to the function")
    #     else:
    #         # Bind the event to the function
    #         root.bind("<Button-1>", on_button_click)
    #         print("Event bound to the function")

    def search_markets(self):
        self.search_executed = True
        
        for item in self.product_items:
            # if not self.is_bound(widget=item, event='<Button-1>'):
            bind_widgets_recursive(widget=item, event="<Button-1>", handler=self.create_handler(index=item.details.target_ID, item=item))
            # self.next_target_ID += 1


        self.explorations = self.market_explorer.get_explorations()
        
        
        for expl in self.explorations:
            expl = expl[0]


            self.explorer_view.table.insert_value(row=0, col=expl.market_ID, value=self.market_hub.market(identifier=expl.market_ID).name().lower())
            self.explorer_view.table.insert_value(row=1, col=expl.market_ID, value= round(expl.total_price, 2))
            self.explorer_view.table.insert_value(row=2, col=expl.market_ID, value=int(round(expl.availability_rate, 0)))
            

            
        self.refresh_recommendation()        

        self.search_bar.grid_forget()
        self.search_bar.config(state="disabled")
        

        self.search_button.config(text="search")



    def explore_markets(self):
        if not self.product_items:
            messagebox.showerror(title="Empty list", message="Nákupný zoznam neobsahuje žiadne položky!")
            return

        self.search_button.config(text="")
        self.search_bar.grid(row=0, column=1, pady=(5, 12))
        self.search_bar.config(state="normal")


        thread = threading.Thread(target=self.search_markets)
        thread.start()

    




        
        

