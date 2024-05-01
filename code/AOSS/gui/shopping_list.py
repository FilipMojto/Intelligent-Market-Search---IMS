from tkinter import *
from tkinter import ttk

from typing import List, Literal

import config_paths as cfg
from AOSS.structure.shopping import ProductCategory, ProductWeightUnit

# class BoundableFrame(Frame):
#     def __init__(self,*args, **kw):
#         super(BoundableFrame, self).__init__(*args, **kw)

#     def bind_widgets_recursive(self, event, handler):
#         self.bind(event, handler)
#         for child in self.winfo_children():
#             child.bind(event, handler)
#             #self.bind_widgets_recursive(event, handler)

# --- ShoppingListItem - Class Declaration&Definition --- #

class ShoppingListDetails(LabelFrame):
    
    """
        This class represents a single product item in the user's shopping list.
    """

    FONT = ('Arial', 11)
    FONT_BOLD = ('Arial', 11, 'bold')
    LABELS_EN = ('Name:', 'Category:', 'Amount:', 'Weight Unit:', 'Weight:')
    LABELS_SK = ('Meno:', 'Kategória:', 'Množstvo', 'Jednotka:', 'Váha:')
    MAX_LABEL_LENGTH = 20

    def __init__(self, *args, name: str, category: int, amount: int,
                 weight_unit: ProductWeightUnit = ProductWeightUnit.NONE, weight: float,
                  ID: int,
                  language: Literal['EN', 'SK'] = 'EN',
                  category_search_mode: str, on_widget_click: callable = None, **kw):
        super(ShoppingListDetails, self).__init__(*args, **kw)

        self.language = language
        self.cur_labels = self.LABELS_EN if self.language == 'EN' else self.LABELS_SK


        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

        self.columnconfigure(0, weight=1)


        self.name = name
        self.name_text = StringVar()
        self.name_text.set(f"{self.cur_labels[0]} {name}")

        self.name_label = Label(self, textvariable=self.name_text, font=self.FONT)
        self.name_label.grid(row=0, column=0, sticky="NSW")
        self.name_label.bind("<Button-1>", on_widget_click)

        truncated_name = self.name[:self.MAX_LABEL_LENGTH] + '...' if len(self.name) > self.MAX_LABEL_LENGTH else self.name
        
        # Set the truncated name to the text variable
        self.name_text.set(f"{self.cur_labels[0]} {truncated_name}")

        
        self.category_search_mode = category_search_mode

        self.category = category
        self.category_text = StringVar()
        self.category_text.set(f"{self.cur_labels[1]} {category}")


        self.amount = amount
        self.amount_text = IntVar()
        self.amount_text.set(f"{self.cur_labels[2]} {amount}")

        self.weight_unit = weight_unit
        self.weight_unit_text = StringVar()
        self.weight_unit_text.set(f"{self.cur_labels[3]} {self.weight_unit.name}")



        self.weight = weight
        self.weight_text = DoubleVar()
        self.weight_text.set(f"{self.cur_labels[4]} {weight}")


        
        self.second_line = Frame(self)
        self.second_line.grid(row=1, column=0, sticky="NSEW")
        self.second_line.rowconfigure(0, weight=1)
        self.second_line.columnconfigure(0, weight=1)
        self.second_line.columnconfigure(1, weight=1)
        self.second_line.bind("<Button-1>", on_widget_click)
        


        self.category_label = Label(self.second_line, textvariable=self.category_text, font=self.FONT)
        self.category_label.grid(row=0, column=0, sticky="W")
        self.category_label.bind("<Button-1>", on_widget_click)



        self.amount_label = Label(self.second_line, textvariable=self.amount_text, font=self.FONT)
        self.amount_label.grid(row=0, column=1, sticky="E")
        self.amount_label.bind("<Button-1>", on_widget_click)


        self.third_line = Frame(self)
        self.third_line.grid(row=2, column=0, sticky="NSEW")
        self.third_line.rowconfigure(0, weight=1)
        self.third_line.columnconfigure(0, weight=1)
        self.third_line.columnconfigure(1, weight=1)
        self.third_line.bind("<Button-1>", on_widget_click)

        self.weight_unit_label = Label(self.third_line, textvariable=self.weight_unit_text, font=self.FONT)
        self.weight_unit_label.grid(row=0, column=0, sticky="W")
        self.weight_unit_label.bind("<Button-1>", on_widget_click)

        self.weight_label = Label(self.third_line, textvariable=self.weight_text, font=self.FONT)
        self.weight_label.grid(row=0, column=1, sticky="E")
        self.weight_label.bind("<Button-1>", on_widget_click)
        

        self.ID = ID
        self.ID_text = StringVar()
        self.ID_text.set(ID)

        self.ID_label = Label(self, textvariable=self.ID_text, font=self.FONT_BOLD)
        self.ID_label.grid(row=3, column=0, sticky="NSEW")
        self.ID_label.bind("<Button-1>", on_widget_click)

        if callable:
            self.name_label.bind("<Button-1>", on_widget_click)
            self.category_label.bind("<Button-1>", on_widget_click)
            self.ID_label.bind("<Button-1>", on_widget_click)


        


class ShoppingListItem(Frame):
    
    """
        This class represents a single product item in the user's shopping list.
    """

    def __init__(self, *args, name: str, category: str, amount: int, category_search_mode: str,
                 weight_unit: ProductWeightUnit = ProductWeightUnit.NONE, weight: float,
                  ID: int, on_widget_click: callable = None, language: Literal['EN', 'SK'] = 'EN', **kw):
        super(ShoppingListItem, self).__init__(*args, **kw)

        self.details = ShoppingListDetails(self,  name=name,
                                           category_search_mode=category_search_mode, category=category,
                                           amount=amount,
                                           weight_unit=weight_unit, weight=weight,
                                           ID=ID, on_widget_click=self.on_item_clicked, bd=1,
                                           language=language)

        self.details.grid(row=0, column=0, sticky="NSEW", padx=2, pady=2)
        self.details.bind("<Button-1>", self.on_item_clicked)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.on_widget_click = on_widget_click

        self.is_clicked_on = False
    
    def on_item_clicked(self, event):
        if self.is_clicked_on:
            return
        self.on_widget_click()
        self.details.configure(bd=4)
        self.is_clicked_on = True


class ShoppingList(Frame):
    
    ITEM_LIMIT = 9999

    def __init__(self, *args, **kw):
        super(ShoppingList, self).__init__(*args, **kw)
        self.items: List[ShoppingListItem] = []
        self.__ID = 1
    
    def assign_ID(self):
        old_val = self.__ID
        self.__ID += 1
        return old_val

    def remove_selected_item(self, return_: bool = False, executable = None):

        for item in self.items:

            if item.is_clicked_on:
                item.destroy()
                self.items.remove(item)
                
                if executable is not None:
                    executable(item)

                if return_:
                    return item
                else:
                    break
        



    def get_items(self):
        """
            Returns currently stored items in the form a tuple.
        """
        product_data: List[tuple[str, ProductCategory, int]] = []


        for item in self.items:
            product_data.append((item.details.name, ProductCategory(value=item.details.category), item.details.amount))
            #item.destroy()
        
           # item.details.

        return product_data

    def remove_click_texture(self, event = None):

        for item in self.items:
            item.configure(background='white')
            item.details.configure(bd=1)
            item.is_clicked_on = False
    


class ShoppingListFrame(LabelFrame):
    WIDTH = 268

    BUTTON_TEXTS_EN = ('remove',)
    BUTTON_TEXTS_SK = ('odstrániť',)

    def __init__(self, *args, on_delete, language: Literal['EN', 'SK'] = 'EN', **kw):
        super(ShoppingListFrame, self).__init__(*args, **kw)
        
        self.language = language
        self.cur_button_texts = self.BUTTON_TEXTS_EN if self.language == 'EN' else self.BUTTON_TEXTS_SK

        self.config(width=self.WIDTH)
        self.pack_propagate(0)
        
        self.list_view = Frame(self)
        self.list_view.pack(side='top', fill='both', expand=True, pady=(13, 0))



        self.canvas = Canvas(self.list_view, width=5, bg='lightgrey')
        self.canvas.pack(side='left', fill='both', expand=True, pady=5)

        self.scrollbar = Scrollbar(self.list_view, orient='vertical',  command=self.canvas.yview)
        self.scrollbar.pack(side='right', fill='y', expand=False, pady=5, padx=3)

        self.scrollbar.config(command=self.canvas.yview)

        self.product_list = ShoppingList(self.canvas, bg='lightgrey', width=15)

        self.product_list.bind('<Configure>', self.configure_interior)
        self.canvas.bind('<Configure>', self.configure_canvas)
        self.__interior_ID = self.canvas.create_window(0, 0, window=self.product_list, width=236, anchor='nw')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.trash_bin_icon = PhotoImage(file=cfg.TRASH_BIN_ICON).subsample(18, 18)

        self.style_1 = ttk.Style()
        self.style_1.configure("TButton", font=("Arial", 15), background="skyblue", foreground="black")

        self.delete_product_button = ttk.Button(self,
                                            text=self.cur_button_texts[0],
                                            style="TButton",
                                            width=27,
                                            padding=(0, 6),
                                            #pady=6,
                                            image=self.trash_bin_icon,
                                            compound='left',
                                            command=lambda: self.product_list.remove_selected_item(False, on_delete))
        self.delete_product_button.pack_propagate(0)
        self.delete_product_button.pack(side='top', fill='y', expand=False, pady=(7, 5))


    def configure_interior(self, event):
        size = (self.product_list.winfo_reqwidth(), self.product_list.winfo_reqheight())
        self.canvas.config(scrollregion=(0, 0, size[0], size[1]))

    def configure_canvas(self, event):
        if self.product_list.winfo_reqheight() != self.canvas.winfo_height():
            self.canvas.itemconfigure(self.__interior_ID, height=self.product_list.winfo_reqheight())
            self.update_scrollbar()


    def update_scrollbar(self):
        self.canvas.update_idletasks()
        size = (self.product_list.winfo_reqwidth(), self.product_list.winfo_reqheight())
        self.canvas.config(scrollregion=(0, 0, size[0], size[1]))
        self.scrollbar.update()



    def insert_item(self, name: str, category: int, amount: int, category_search_mode: str,
                    weight_unit: ProductWeightUnit, weight: float):

        """
            Inserts a new ShoppingListItem instance into the shopping list.

            Items are stored by using pack manager, they are appended to the top, so that they are
            placed vertically representing a shopping list.

            Newly created instance is returned immediatelly.
        
        """

        item = ShoppingListItem(self.product_list,
                                name=name,
                                category=category,
                                amount=amount,
                                category_search_mode=category_search_mode,
                                weight_unit=weight_unit,
                                weight=weight,
                                ID=self.product_list.assign_ID(),
                                on_widget_click=self.product_list.remove_click_texture,
                                width=240, bg='lightgrey',
                                language=self.language)

        item.pack(side="top", fill="x", expand=False, padx=2, pady=2)

        self.product_list.items.append(item)
        item.bind("<Button-1>", self.product_list.remove_click_texture)

        # Update scrollbar after inserting new item
        self.update_scrollbar()

        event = Event()
        event.widget = self.canvas
        self.configure_canvas(event)


        self.canvas.update_idletasks()
        self.canvas.update()

        return item
