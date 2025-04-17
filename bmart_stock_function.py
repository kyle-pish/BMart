import mysql.connector

try:
    with mysql.connector.connect(user = 'test', password = 'test', host = 'root', )

finally:
    pass



'''
BMart Reorder Function (2.1)
CS314 Spring 2025
Joel Madrigal
'''

from bmart_connection import connect_to_bmart_db
from mysql.connector import Error


#Based on Joel's Code in the reorder function
def stock(store_id: int, shipment_id : int, shipment_items : dict[str, int] ):
    try:
        # Deepu's local server.
        conn, cursor = connect_to_bmart_db(
            '127.0.0.1', 'root', 'DocDeeps!', 'cs314_project')

        '''# Our actual one.
        conn, cursor = connect_to_bmart_db(
            'cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt')
'''
"""
 uses stock(<store>, <shipment>, <shipment_items>).
 - when shipment arrives (overnight)
    Stockers unload shipment and move into store
        redo the inventory tables
- Note that shipment arrived (bool)
- Note when shipment arrived (date-time)
- Count of number of items arriving (updates inventory)
    - update store inventory to be updated at opening the next day
    - updated DB
- if errors occur in the process of executing the stock funding,
    everything should roll back and an error message will be printed
    - ex. "Invalid shipment item ______ !"
- If no errors occur, then the SQL operations should be commited to the DB and
    print stocker information
    - details about the shipment that was just received
    - list of shipment items and quantities stocked
        - how many were stocked in comaprison to how many were sent
    - A list of any inventory discrepancies between the shipment and promised by the vendor
    and the shipment received by the store

    - specify how <store>, <shipment>, <shipment_items> are to be passed into the function

    - <store> and shipment shoudl presumably align with how your database identifies stores and shipments
    - <shipment_items>, specify info via a parameter; either a string that follows some precise formatting or 
        a dictionary mapping items to the quantity for each item in that shipment
    
    
    - descirbe everything in docstrings for the functions
    - document design decision as well as how the funciton accomplishes the steps required.

 

 
 """
        try:
            
            pass
        # Joel's code
        """
            products_to_be_ordered = {}

            prod_query = (
                "SELECT inventory.product_UPC, inventory.current_inventory, inventory.max_inventory FROM inventory JOIN stores ON "
                "inventory.store_id = stores.store_id WHERE "
                "stores.store_id = %s;")

            cursor.execute(
                prod_query, (store_id,))

            for prod_stocking in cursor:
                if prod_stocking["current_inventory"] <= prod_stocking["max_inventory"]:
                    derived_prod = prod_stocking["max_inventory"] - \
                        prod_stocking["current_inventory"]
                    products_to_be_ordered[prod_stocking["product_UPC"]
                                           ] = derived_prod

            check_ord_ship_query = ("SELECT inventory.product_UPC FROM inventory "
                                    "JOIN stores ON inventory.store_id = stores.store_id "
                                    "JOIN reorder_requests ON stores.store_id = reorder_requests.store_id "
                                    "JOIN shipments ON stores.store_id = shipments.store_id "
                                    "WHERE shipments.delivered != TRUE || reorder_requests.completed != TRUE "
                                    "GROUP BY stores.store_id HAVING stores.store_id = %s;")

            cursor.execute(check_ord_ship_query, (store_id,))
            data = cursor.fetchall()
            """
        except Error as e:
            print("This error has occured while executing the query(ies): ", e)
            raise e

    finally:
        cursor.close()
        conn.close()



