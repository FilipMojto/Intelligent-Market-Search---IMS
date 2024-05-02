from tkinter import *
from tkinter import ttk
from tkinter import messagebox

import csv
from typing import List, Dict, Literal
import threading
import time
from datetime import datetime

from AOSS.structure.shopping import ProductCategory, ProductWeightUnit
from AOSS.components.categorization import ProductCategorizer

from AOSS.gui.shopping_list import ShoppingListFrame
from AOSS.gui.market_explorer import MarketExplorerFrame
from AOSS.gui.utils import AmountEntryFrame
from AOSS.gui.category_search_mode_panel import CategorySearchModePanel


from config_paths import *

BACKGROUND = 'lightblue'

class SearchedProductWindow(Toplevel):

    WIDTH = 38
    FONT = ("Arial", 13, 'italic')
    CLOSE_BUTTON_FONT = ("Arial", 12, 'bold')

    def __init__(self, *args, row_limit, min_char_limit = 10, max_char_limit, **kw):
        super(SearchedProductWindow, self).__init__(*args, **kw)

        self.row_limit = row_limit
        self.min_char_limit = min_char_limit
        self.max_char_limit = max_char_limit

        self.overrideredirect(True)
        self.bind("<Destroy>", self.save_products)


        self.listbox = Listbox(self, width=self.WIDTH, font=self.FONT)
        self.listbox.bind("<Motion>", self.on_motion)
        self.listbox.bind("<Leave>", self.on_leave)
        self.listbox.pack(side='left')

        self.close_window_button = Button(self, background='red', text='x', foreground='white',
                                           font=self.CLOSE_BUTTON_FONT, padx=2, pady=0, height=1)
        self.close_window_button.pack(side='top')

        self.products: Dict[str, List[int, str, str]] = {}
        self.next_ID = None

    def on_motion(self, event):
        index = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, END)  # Clear previous selection
        self.listbox.selection_set(index)  # Set new selection
        self.listbox.activate(index)  # Set the item as active

    def on_leave(self, event):
        self.listbox.selection_clear(0, END)  # Clear selection


    def update_listbox_size(self, char_count: int = None):
        # Get the number of items in the listbox
        num_items = self.listbox.size()

        # Set the height of the listbox based on the number of items
        self.listbox.config(height=num_items if num_items < self.row_limit else self.row_limit)

        # if char_count is not None and char_count > self.listbox.winfo_width():

        #     # if char_count > self.max_char_limit:
        #     #     char_count = self.max_char_limit
            
        #     self.listbox.config(width=self.max_char_limit if char_count > self.max_char_limit else char_count)

    
    def insert_product(self, content: str):
        """
            Inserts new searched product and its metadata to the dictionary.

            If the content is already present in the dictionary, searched_at attribute is updated.
        """

        if content in self.products:
            self.products[content][2] = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        else:
            self.products[content] = [self.next_ID, content, datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')]
            self.next_ID += 1
            self.update_listbox_size(char_count=len(content))



    def show_matches(self, content: str):
       
        self.listbox.delete(0, END)

        # Filter and display matching recommendations
        matching_results = [element for element in self.products.values() if content in element[1].lower()]
        for result in matching_results:
            self.listbox.insert(END, result[1])
        
        self.update_listbox_size(char_count=None)

        
    def load_products(self):
        """
            Loads the history of previosly searched products into the dictionary.
            Searched text is used as a key which maps a tuple containing metadata about
            the search.
        """

        with open(file=SEARCHED_PRODUCTS_FILE['path'], mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
        
            if SEARCHED_PRODUCTS_FILE['header']:
                try:
                    next(reader)
                except StopIteration:
                    self.next_ID = 1
                    return


            for row in reader:
                cur_ID = int(row[SEARCHED_PRODUCTS_FILE['cols']['ID']])

                if self.next_ID is None or self.next_ID < cur_ID:
                    self.next_ID = cur_ID

                self.products[row[SEARCHED_PRODUCTS_FILE['cols']['content']]] = [row[SEARCHED_PRODUCTS_FILE['cols']['ID']],
                                                                                row[SEARCHED_PRODUCTS_FILE['cols']['content']],
                                                                                row[SEARCHED_PRODUCTS_FILE['cols']['searched_at']]]
                


        self.next_ID += 1
                
        
    def save_products(self, event = None):
        """
            Saves the object's current dictionary data back to the source file.
        """

        with open(file=SEARCHED_PRODUCTS_FILE['path'], mode='w', encoding='utf-8', newline='') as file:
            
            writer = csv.writer(file)
            writer.writerow(('ID', 'content', 'searched_at'))

            for element in self.products.values():
                writer.writerow(element)
        
            #writer.writerows(self.products)

class ProductSpecificationMenu(LabelFrame):

    BACKGROUND = 'lightblue'
    FONT = ('Arial', 13)
    ENTRY_LABELS_EN = ('Enter Name:', 'Enter Amount:', 'Weight Unit:', 'Weight:', 'Category Search:')
    ENTRY_LABELS_SK = ('Zadaj meno:', 'Uveď množstvo:', 'Jednotka váhy:', 'Váha:', 'Kategórie:')
    WEIGHT_UNITS_VALUES_EN = ('---', 'GRAMS', 'LITRES')
    WEIGHT_UNITS_VALUES_SK = ('---', 'GRAMY', 'LITRE')
    CATEGORY_SEARCH_VALES_EN = ('Off', 'Manual Mapping', 'TM-based Mapping')
    CATEGORY_SEARCH_VALES_SK = ('Vypnuté', 'Manuálne mapovanie', 'Mapovanie založené na TO')

    @staticmethod
    def map_weight_unit(weight_unit: str):
        """
            Maps weigh unit value in Slovak language to its English counterpart.
        """
        
        for index, unit in enumerate(ProductSpecificationMenu.WEIGHT_UNITS_VALUES_SK):
            if unit == weight_unit:
                return ProductSpecificationMenu.WEIGHT_UNITS_VALUES_EN[index]



    def __init__(self, *args, root: Tk, shopping_list_frame: ShoppingListFrame,
                   market_explorer_frame: MarketExplorerFrame,
                    language: Literal['EN', 'SK'] = 'EN', **kw):
        super(ProductSpecificationMenu, self).__init__(*args, **kw)
        

        #self.config(background=BACKGROUND)
        self.language = language
        self.cur_entry_labels = self.ENTRY_LABELS_EN if self.language == 'EN' else self.ENTRY_LABELS_SK
        self.cur_weight_units_values = self.WEIGHT_UNITS_VALUES_EN if self.language == 'EN' else self.WEIGHT_UNITS_VALUES_SK
        self.cur_category_search_values = self.CATEGORY_SEARCH_VALES_EN if self.language == 'EN' else self.CATEGORY_SEARCH_VALES_SK


        self.root = root
        self.root.bind("<Configure>", self.on_root_window_moved)
        self.shopping_list_f = shopping_list_frame
        self.market_explorer_f = market_explorer_frame

        # ------ Frame Configuration ------ #
        
        self.rowconfigure(0, weight=1, minsize=110)
        self.rowconfigure(1, weight=3, minsize=50)
        self.rowconfigure(2, weight=200)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1, minsize=630)

        # ------ MAIN_DETAILS_MENU - CONFIGURATION ------ #

        self.main_details_menu = Frame(self, bg=self.BACKGROUND)
        self.main_details_menu.grid(row=0, column=0, sticky="NEW", pady=(17, 7), padx=5)

        # frame configuration

        self.main_details_menu.grid(row=0, column=0, sticky="NEW")
        self.main_details_menu.rowconfigure(0, weight=1)
        self.main_details_menu.rowconfigure(1, weight=1)
        self.main_details_menu.rowconfigure(2, weight=1)
        self.main_details_menu.columnconfigure(0, weight=1)



        # name configuration

        self.upper_wrapper_frame = Frame(self.main_details_menu, background=BACKGROUND)
        self.upper_wrapper_frame.grid(row=0, column=0, sticky="NSEW", pady=(5, 0))
        self.upper_wrapper_frame.rowconfigure(0, weight=1, minsize=50)
        self.upper_wrapper_frame.columnconfigure(0, weight=1)
        self.upper_wrapper_frame.columnconfigure(1, weight=100)

        self.name_frame = Frame(self.upper_wrapper_frame, bg=BACKGROUND)
        self.name_frame.grid(row=0, column=0, sticky="NSEW", pady=8, padx=(3, 35))
        self.name_frame.rowconfigure(0, weight=1)
        self.name_frame.columnconfigure(0, weight=1)

        self.name_frame_label = Label(self.name_frame, text=self.cur_entry_labels[0], bg=BACKGROUND, font=self.FONT)
        
        
        self.name_frame_label.grid(row=0, column=0, sticky="E")

        s = ttk.Style()
        s.configure('Rounded.TEntry', borderwidth=5, relief="flat", foreground="black", background="white")

        self.name_frame_entry = ttk.Entry(self.upper_wrapper_frame, style='Rounded.TEntry', font=self.FONT)
        self.name_frame_entry.grid(row=0, column=1, sticky="NSEW", pady=3, padx=8)
        self.name_frame_entry.bind("<KeyRelease>", self.show_product_name_matches)
        self.name_frame_entry.bind("<FocusOut>", self.destroy_product_name_matches)
        # amount configuration
        
        self.middle_wrapper_frame = Frame(self.main_details_menu, background=self.BACKGROUND)
        self.middle_wrapper_frame.grid(row=1, column=0, sticky="NSEW", pady=5)
        self.middle_wrapper_frame.rowconfigure(0, weight=1, minsize=50)
        self.middle_wrapper_frame.columnconfigure(0, weight=1)
        self.middle_wrapper_frame.columnconfigure(1, weight=1, minsize=100)
        self.middle_wrapper_frame.columnconfigure(2, weight=1)
        self.middle_wrapper_frame.columnconfigure(3, weight=1)
        self.middle_wrapper_frame.columnconfigure(4, weight=1)
        self.middle_wrapper_frame.columnconfigure(5, weight=1)

        self.amount_frame_wrapper = Frame(self.middle_wrapper_frame, bg=self.BACKGROUND)
        self.amount_frame_wrapper.grid(row=0, column=0, sticky="NSEW", pady=8, padx=(3, 17))
        self.amount_frame_wrapper.rowconfigure(0, weight=1)
        self.amount_frame_wrapper.columnconfigure(0, weight=1)

        self.amount_frame_label = Label(self.amount_frame_wrapper, text=self.cur_entry_labels[1], bg=BACKGROUND, font=self.FONT)
        self.amount_frame_label.grid(row=0, column=0, sticky="E")



        #self.amount_frame_entry = ttk.Entry(self.main_details_menu, style='Rounded.TEntry', font=("Arial", 13))
        self.amount_frame_entry = AmountEntryFrame(self.middle_wrapper_frame)
        self.amount_frame_entry.grid(row=0, column=1, sticky="NSEW", padx=8, pady=(0, 3))
        
        self.weight_unit_label_wrapper = Frame(self.middle_wrapper_frame, bg='lightblue')
        self.weight_unit_label_wrapper.grid(row=0, column=2, sticky="NSEW")
        self.weight_unit_label_wrapper.rowconfigure(0, weight=1)
        self.weight_unit_label_wrapper.columnconfigure(0, weight=1)

        self.weight_unit_label = Label(self.weight_unit_label_wrapper, text=self.cur_entry_labels[2], bg=self.BACKGROUND,
                                       font=self.FONT)
        self.weight_unit_label.grid(row=0, column=0, sticky="NSEW")

        self.weight_unit_box = ttk.Combobox(self.weight_unit_label_wrapper, state='readonly', font=self.FONT, width=8)
        self.weight_unit_box['values'] = self.cur_weight_units_values
        self.weight_unit_box.current(0)
        self.weight_unit_box.bind("<<ComboboxSelected>>", self.handle_combobox_selection)
    
        self.weight_unit_box.grid(row=0, column=3, sticky="NSEW")

        self.weight_label_wrapper = Frame(self.middle_wrapper_frame, background=self.BACKGROUND)
        self.weight_label_wrapper.grid(row=0, column=4, sticky="NSEW")
        self.weight_label_wrapper.rowconfigure(0, weight=1)
        self.weight_label_wrapper.columnconfigure(0, weight=1)

        self.weight_label = Label(self.weight_label_wrapper, text=self.cur_entry_labels[3], background=self.BACKGROUND,
                                  font=self.FONT)
        self.weight_label.grid(row=0, column=0, sticky="NSE")

        self.weight_entry = ttk.Entry(self.middle_wrapper_frame, font=self.FONT, width=15, state='disabled')
        self.weight_entry.grid(row=0, column=5, sticky="NSEW", padx=8)




        self.lower_wrapper_frame = Frame(self.main_details_menu, background=BACKGROUND)
        self.lower_wrapper_frame.grid(row=2, column=0, sticky="NSEW", pady=(0, 5))

        self.lower_wrapper_frame.rowconfigure(0, weight=1, minsize=50)
        self.lower_wrapper_frame.columnconfigure(0, weight=1)

        self.categories_menu = CategoriesMenu(self, parent=self, bg=BACKGROUND)

        self.category_search_mode_panel = CategorySearchModePanel(self.lower_wrapper_frame, on_select=self.categories_menu.set_mode,
                                                                  label_text=self.cur_entry_labels[4],
                                                                  options=self.cur_category_search_values)
        self.category_search_mode_panel.grid(row=0, column=0, sticky="NSW", padx=(0, 9))
        # self.category_mode_label = Label(self.lower_wrapper_frame, text="Category Search:")
        # self.category_mode_label.grid(row=0, column=2, sticky="NSEW")


        # ------ CATEGORIES - CONFIGURATION ------ #

        # self.categories_menu = CategoriesMenu(self, bg=BACKGROUND)
        self.categories_menu.grid(row=1, column=0, sticky="NEW", pady=(10, 5), padx=5)


        # ------- PADDING - CONFIGURATION ------ #
        self.padding = Frame(self, background='skyblue')
        self.padding.grid(row=2, column=0, sticky="NSEW")


        # ------- BUTTON_PANEL - CONFIGURATION ------ #

        self.button_panel = ButtonPanel(self, bg='lightblue', parent_frame=self, language=self.language)
        self.button_panel.grid(row=3, column=0, sticky="NEW")


    

        # Create a modal window positioned beneath the Entry widget
        self.modal_window = SearchedProductWindow(self.root, row_limit=5, max_char_limit=50)
        #self.modal_window.listbox.config(width=self.name_frame_entry.winfo_width())

        self.modal_window.load_products()
        self.modal_window.withdraw()

    def handle_combobox_selection(self, event):
        if self.weight_unit_box.current() == 0:
            self.weight_entry.delete(0, 'end')
            self.weight_entry.config(state='disabled')
            
        else:
            self.weight_entry.config(state='normal')


    def on_root_window_moved(self, event):

        # Catching some exceptions that will be thrown when the main window is created and the modal
        # window not yet.
        try:
            self.modal_window.withdraw()
        except AttributeError:
            pass   


    def show_product_name_matches(self, event):
        

        x, y = self.name_frame_entry.winfo_rootx(), self.name_frame_entry.winfo_rooty()
        _, h = self.name_frame_entry.winfo_width(), self.name_frame_entry.winfo_height()

        self.modal_window.geometry(f"+{x}+{y + h}")
        
        self.modal_window.show_matches(content=self.name_frame_entry.get())

        if self.modal_window.listbox.size() > 0:
            self.modal_window.deiconify()
        else:
            self.modal_window.withdraw()

    def get_selected_product(self):
        time.sleep(0.1)
        selection = self.modal_window.listbox.curselection()
        
        if selection:
            self.name_frame_entry.delete(0, END)
            self.name_frame_entry.insert(0, self.modal_window.listbox.get(selection[0]))
            #print(self.modal_window.listbox.get(selection[0]))



        self.modal_window.withdraw()
        
    
    def destroy_product_name_matches(self, event):
        thread = threading.Thread(target=self.get_selected_product)
        thread.start()
    
    def show_error(self):
        # Create a Toplevel window
        error_window = Toplevel(self.root)
        error_window.title("Error")
        
        # Create a Message widget with the error message
        error_message = Message(error_window, text="Product Specification\nName field cannot be empty!", padx=10, pady=10)
        error_message.pack()

        # Add a button to close the error window
        btn_ok = Button(error_window, text="OK", command=error_window.destroy)
        btn_ok.pack()



    def insert_item(self):


        name = self.name_frame_entry.get()
        
        

        if name is None or name == "":
           # self.show_error()

            #message = messagebox.Message(self)
            messagebox.showerror("Product Specification", "Name field cannot be empty!")
            return

        if not self.shopping_list_f.can_insert(name=name):
            messagebox.showerror(title="Product Specification", message="List already contains a product with the same name!")
            return

        

        category = self.categories_menu.buttons_panel.get_option()

        try:
            amount = int(self.amount_frame_entry.entry.get())

            if amount < 1:
                raise ValueError("Product amount must be positive integer!")
            elif amount > self.shopping_list_f.product_list.ITEM_LIMIT:
                raise ValueError(f"Product amount above allowed limit: {self.shopping_list_f.product_list.ITEM_LIMIT}")
            
            weight_unit = self.weight_unit_box.get()

            if self.language == 'SK':
                weight_unit = self.map_weight_unit(weight_unit=weight_unit)

            weight_unit=ProductWeightUnit[weight_unit if weight_unit != '---' else 'NONE']
            weight=self.weight_entry.get()

            if weight_unit != ProductWeightUnit.NONE:
                try:
                    weight = float(weight)
                except ValueError:
                    messagebox.showerror(title="Product Specification", message='Invalid weight value, must be a digit or float!')
                    return
            else:
                weight = -1
                
            self.name_frame_entry.delete(0, END)
            self.amount_frame_entry.entry.delete(0, END)
            self.amount_frame_entry.entry.insert(0, 1)

            # here program sents the newly inserted item to the market explorer so that it can pre-explore it
            item = self.shopping_list_f.insert_item(name=name, category=category, amount=amount,
                                                    category_search_mode=self.category_search_mode_panel.selected_option.get(),
                                                    weight_unit=weight_unit,
                                                    weight=weight)
            self.market_explorer_f.explore_product(item=item)

            self.market_explorer_f.search_button.config(state='normal')
            
        except ValueError as error:
            messagebox.showerror("Product Specification", error)
            return
        
        return 0
        
        

    def clear_all_data(self):
        self.name_frame_entry.delete(0, END)
        self.amount_frame_entry.entry.delete(0, END)
        self.amount_frame_entry.entry.insert(0, 1)



class CategoriesMenu(Frame):
    """
    
    """

    def __init__(self, *args, parent: ProductSpecificationMenu,  **kw):
        super(CategoriesMenu, self).__init__(*args, **kw)

        self.parent = parent
        # --- Frame Configuration --- #

        self.rowconfigure(0, weight=2, minsize=100)
        self.rowconfigure(1, weight=1, minsize=0)
        self.columnconfigure(0, weight=1)

        # --- ButtonsPane Configuration --- #

        self.buttons_panel = CategoryButtonsPanel(self, parent_frame=self, bg=BACKGROUND, text="Categories", font=("Arial", 15, 'bold'))
        self.buttons_panel.grid(row=0, column=0, sticky="NSEW", padx=5, pady=3)

        # --- DetailsPanel Configuration --- #

        self.details_panel = Text(self, height=5)
        self.details_panel.configure(state='disabled')
        self.details_panel.grid(row=1, column=0, sticky="NEW", padx=5, pady=3)

    
    def set_mode(self, mode: str):
        """
            Sets the category search mode, accepted values of mode:
                
                a) Off - disables whole frame, user is unable to specify any category
                b) Manual Mapping - sets the state to normal, user has to specify a category
                c) TM-based Mapping - sets the state to normal, user has to specify a category
        """


        if mode == self.parent.cur_category_search_values[0]:
            self.buttons_panel.set_option(0)
            self.buttons_panel.set_state('disabled')
            
        elif mode == self.parent.cur_category_search_values[1] or mode == self.parent.cur_category_search_values[2]:
            self.buttons_panel.set_state('normal')

    def disable_widgets(self):
        for widget in self.winfo_children():
            widget.configure(state='disabled')

    def enable_widgets(self):
        for widget in self.winfo_children():
            widget.configure(state='normal')


    def show_details(self, category: str, text: str):
        if text is not None and text:
            self.details_panel.configure(state='normal')
            self.details_panel.delete("1.0", END)  # Delete existing content
            self.details_panel.insert(END, category + '\n')
            self.details_panel.insert(END, text)
            self.details_panel.configure(state='disabled')
            





class CategoryButtonsPanel(LabelFrame):
    TEXT_WIDTH = 23
    FONT = ('Arial', 12)
    _BACKGROUND = BACKGROUND

    RADIOBUTTON_1_VAL = "0 - Neurčená"


    def __init__(self, *args, parent_frame: CategoriesMenu, **kw):
        super(CategoryButtonsPanel, self).__init__(*args, **kw)

        self.parent = parent_frame

        self.state = 'disabled'


        

       # self.__category_info_view = category_info_view

        self.__variable = IntVar()
        self.__old_val = self.__variable.get()

        self.__variable.trace_add("write", callback=self.__notify)

        self.__unspecified = Radiobutton(self, bg=self._BACKGROUND, text=self.RADIOBUTTON_1_VAL, font=self.FONT,  width=self.TEXT_WIDTH, variable=self.__variable, value=0, anchor='w',
                                         activebackground='grey')#highlightbackground='grey', highlightcolor='grey', highlightthickness='grey')
        
        self.__unspecified.config(highlightbackground='grey', highlightcolor='grey')
        self.__unspecified.grid(row=0, column=0, sticky="W")


        self.__fruit_vegetables = Radiobutton(self, activebackground='grey', state=self.state, bg=self._BACKGROUND, text="1 - Ovocie a zelenina", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=1, anchor='w')
        self.__fruit_vegetables.grid(row=0, column=1, sticky="W")

        self.__baked_products = Radiobutton(self, bg=self._BACKGROUND, state=self.state, activebackground='grey', text="2 - Pečivo", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=2, anchor='w')
        self.__baked_products.grid(row=1, column=0, sticky="W")

        self.__meat_and_frost = Radiobutton(self, bg=self._BACKGROUND, state=self.state, activebackground='grey', text="3 - Mäso a mrazené výrobky", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=3, anchor='w')
        self.__meat_and_frost.grid(row=1, column=1, sticky="W")

        self.__smoked_paste = Radiobutton(self, bg=self._BACKGROUND, state=self.state,  activebackground='grey', text="4 - Udeniny, natierky a pastety", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=4, anchor='w')
        self.__smoked_paste.grid(row=2, column=0, sticky="W")

        self.__dairies = Radiobutton(self, bg=self._BACKGROUND, state=self.state, activebackground='grey', text="5 - Mliečne výrobky", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=5, anchor='w')
        self.__dairies.grid(row=2, column=1, sticky="W")

        self.__durables_eggs = Radiobutton(self, bg=self._BACKGROUND, state=self.state, activebackground='grey', text="6 - Trvanlivé potraviny, vajcia", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=6, anchor='w')
        self.__durables_eggs.grid(row=3, column=0, sticky="W")

        self.__sweets = Radiobutton(self, bg=self._BACKGROUND, state=self.state, activebackground='grey', text="7 - Sladkosti", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=7, anchor='w')
        self.__sweets.grid(row=3, column=1, sticky="W")

        self.__snacks_seeds = Radiobutton(self, bg=self._BACKGROUND, state=self.state, activebackground='grey', text="8 - Slané, snacky a semienka", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=8, anchor='w')
        self.__snacks_seeds.grid(row=4, column=0, sticky="W")

        self.__non_alcoholic_drinks = Radiobutton(self, bg=self._BACKGROUND, state=self.state, activebackground='grey', text="9 - Nealkoholické nápoje", font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=9, anchor='w')
        self.__non_alcoholic_drinks.grid(row=4, column=1, sticky="W")

        self.__alcohol = Radiobutton(self, bg=self._BACKGROUND, text="10 - Alkohol", state=self.state, activebackground='grey', font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=10, anchor='w')
        self.__alcohol.grid(row=5, column=0, sticky="W")

        self.__hot_drinks = Radiobutton(self, bg=self._BACKGROUND, text="11 - Horúce nápoje", state=self.state, activebackground='grey', font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=11, anchor='w')
        self.__hot_drinks.grid(row=5, column=1, sticky="W")

        self.__prepared_food = Radiobutton(self, bg=self._BACKGROUND, text="12 - Hotové či instatné jedlá", state=self.state, activebackground='grey', font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=12, anchor='w')
        self.__prepared_food.grid(row=6, column=0, sticky="W")

        self.__healthy_products = Radiobutton(self, bg=self._BACKGROUND, text="13 - Zdravé potraviny", state=self.state, activebackground='grey', font=self.FONT, width=self.TEXT_WIDTH, variable=self.__variable, value=13, anchor='w')
        self.__healthy_products.grid(row=6, column=1, sticky="W")        



    def set_state(self, state):
        self.state = state


        for rb in self.winfo_children():
            if isinstance(rb, Radiobutton) and rb.cget('text') != self.RADIOBUTTON_1_VAL:
                
                rb.config(state=self.state)

   

    def get_option(self) -> int:
        return self.__variable.get()

    def set_option(self, value: int):
        self.__variable.set(value=value)

    def __notify(self, *args):

        new_value = self.__variable.get()

        if new_value != self.__old_val: 

            category_name = ProductCategory(value=new_value).name
            
            self.parent.show_details(text=ProductCategorizer.category_details(category=category_name.lower()),
                                     category=category_name)

           # self.__category_info_view.show_category_details(category_name=category_name, details=ProductCategorizer.category_details(category=category_name.lower()))
            self.__old_val = new_value



class ButtonPanel(Frame):
    BUTTON_TEXTS_EN = ("   to List",)
    BUTTON_TEXTS_SK = ("   vložiť",)

    def __init__(self, *args, parent_frame: ProductSpecificationMenu, language: Literal['EN', 'SK'] = 'EN', **kw):

        super(ButtonPanel, self).__init__(*args, **kw)

        self.language = language
        self.cur_button_texts = self.BUTTON_TEXTS_EN if self.language =='EN' else self.BUTTON_TEXTS_SK

        self.parent = parent_frame

        self.eraser_icon = PhotoImage(file=ERASER_ICON).subsample(17, 17)
        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.trash_bin_icon = PhotoImage(file=TRASH_BIN_ICON).subsample(18, 18)

        self.style_1 = ttk.Style()
        self.style_1.configure("TButton", font=("Arial", 13), background="skyblue", foreground="black")


        self.cart_icon = PhotoImage(file=SHOPPING_CART_ICON_2).subsample(17, 17)

        

        self.to_cart_button = ttk.Button(self,
                                         text=self.cur_button_texts[0],
                                         style="TButton",
                                     command=self.to_list,
                                     image=self.cart_icon,
                                     compound='left',
                                     padding=4
                                     )
        
        self.to_cart_button.grid(row=0, column=1, sticky="SNEW", padx=5, pady=(6, 5))
    
    def to_list(self):
        content = self.parent.name_frame_entry.get()
        
        # updating the search history
        if self.parent.insert_item() == 0:
            self.parent.modal_window.insert_product(content=content)
        

        
        



