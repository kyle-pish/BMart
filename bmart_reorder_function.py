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

            checking_products_in_reord = ("SELECT reorder_requests.product_ordered, reorder_requests.quantity_of_product FROM reorder_requests "
                                          "JOIN stores ON reorder_requests.store_id = stores.store_id "
                                          "WHERE reorder_requests.completed != TRUE && stores.store_id = %s")

            cursor.execute(checking_products_in_reord, (store_id,))
            data = cursor.fetchall()

            for i in data:
                print(i)
                if products_to_be_ordered[prod_stocking["product_UPC"]] in i:
                    print('hi')
                    left_to_be_ordered = products_to_be_ordered[prod_stocking["product_UPC"]] - i

        except Error as e:
            print("This error has occured while executing the query(ies): ", e)
            raise e

    finally:
        cursor.close()
        conn.close()


reorder(2)
