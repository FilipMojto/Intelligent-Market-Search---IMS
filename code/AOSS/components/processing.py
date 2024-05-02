from typing import List

from AOSS.structure.shopping import ProductWeightUnit



def extract_weight_data(item):
    weight_unit = "unknown"
    weight_value: float = -1

    name = item.get('name')
    name_splits: List[str] = name.split(" ")

    if item['id'] == '63be747b1cbfb298235d56a9' or item['id'] == '64afa2cc054021ac79bc0341':
        pass

    try:
        weight_unit = name_splits[len(name_splits) - 1]
        weight_value = float(name_splits[len(name_splits) - 2].replace(",", "."))               
    except ValueError:
        last: str = name_splits[len(name_splits) - 1]
        i = 0

        for i in range(len(last)):
            if not last[i].isdigit():
                break
        
        try:
            weight_value = float(last[: i].replace(",", "."))
            weight_unit = last[i:]

            if weight_unit not in ['l', 'L', 'ml', 'g', 'kg', 'ks']:
                raise ValueError
            
        except ValueError:
            
            
            try:
                weight_value = float(name_splits[len(name_splits) - 2][1:].replace(",", "."))
                weight_unit = name_splits[len(name_splits) - 1][:-1]
            except ValueError:
                try:
                    last_splits = last.split("x")
                    first = int(last_splits[0])

                    i = 0

                    for i in range(len(last_splits[1])):
                        if not last_splits[1][i].isdigit():
                            break

                    weight_value = first * float(last_splits[1][: i].replace(",", "."))
                    weight_unit = last_splits[1][i:]
                except ValueError:
                    pass


    
    if weight_unit == "l" or weight_unit == "L":
        weight_unit = ProductWeightUnit.LITRES 
    elif weight_unit == "ml":
        weight_value /= 1000
        weight_unit = ProductWeightUnit.LITRES
    elif weight_unit == "g":
        
        weight_unit = ProductWeightUnit.GRAMS
    elif weight_unit == "kg":
        weight_value *= 1000
        weight_unit = ProductWeightUnit.GRAMS 
    elif weight_unit == "ks":
        weight_unit = ProductWeightUnit.NONE
    else:
        weight_unit = ProductWeightUnit.NONE
    
    return weight_unit, weight_value