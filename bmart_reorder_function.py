'''
BMart Reorder Function (2.1)
CS314 Spring 2025
Joel Madrigal
'''

from bmart_connection import connect_to_bmart_db
from mysql.connector import Error


def reorder(store_id: int):
    try:
        # Joel's local server.
        conn, cursor = connect_to_bmart_db(
            '127.0.0.1', 'root', 'MomIsTheBest1966!', 'final_proj_test')

        '''# Our actual one.
        conn, cursor = connect_to_bmart_db(
            'cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt')
'''
        try:
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

        except Error as e:
            print("This error has occured while executing the query(ies): ", e)
            raise e

    finally:
        cursor.close()
        conn.close()


reorder(1)
