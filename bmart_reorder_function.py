'''
BMart Reorder Function (2.1)
CS314 Spring 2025
Joel Madrigal
'''

from bmart_connection import connect_to_bmart_db
from mysql.connector import Error
from datetime import datetime


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
            reorder_prod_unconfirmed = []

            conn.start_transaction()

            prod_query = (
                "SELECT inventory.product_UPC, inventory.current_inventory, inventory.max_inventory, products.vendor_name FROM inventory "
                "JOIN products ON inventory.product_UPC = products.product_UPC "
                "JOIN stores ON inventory.store_id = stores.store_id "
                "WHERE stores.store_id = %s;")

            cursor.execute(
                prod_query, (store_id,))

            for prod_stocking in cursor:

                if prod_stocking["current_inventory"] <= prod_stocking["max_inventory"]:

                    derived_prod_amt = prod_stocking["max_inventory"] - \
                        prod_stocking["current_inventory"]
                    products_to_be_ordered[prod_stocking["product_UPC"]] = [
                        derived_prod_amt, prod_stocking["vendor_name"]]

            reorder_update_in_progress = ("UPDATE reorder_requests SET reorder_requests.quantity_of_product = %s "
                                          "WHERE reorder_requests.product_ordered = %s AND reorder_requests.confirmed != TRUE AND "
                                          "reorder_requests.store_id = %s;")

            reorder_insert_fill_inv = (
                "INSERT INTO reorder_requests VALUES (DEFAULT, %s, %s, FALSE, FALSE, %s, %s, %s);")

            update_or_insert_check = ("SELECT * FROM reorder_requests "
                                      "JOIN stores ON reorder_requests.store_id = stores.store_id "
                                      "WHERE reorder_requests.confirmed != TRUE && stores.store_id = %s;")

            cursor.execute(update_or_insert_check, (store_id,))
            check = cursor.fetchall()

            for i in check:
                reorder_prod_unconfirmed.append(i["product_ordered"])

            date_time = datetime.now()

            for product_upc, quantity_and_vendor in products_to_be_ordered.items():

                for update_checker in reorder_prod_unconfirmed:

                    if update_checker == product_upc:
                        count_of_updates += 1
                        cursor.execute(reorder_update_in_progress,
                                       (quantity_and_vendor[0], update_checker, store_id))

                cursor.execute(
                    reorder_insert_fill_inv, (quantity_and_vendor[0], date_time, store_id, quantity_and_vendor[1], product_upc))

            conn.commit()

        except Error as e:
            conn.rollback()
            print("This error has occured while executing the query(ies): ", e)
            raise e

    finally:
        cursor.close()
        conn.close()


reorder(2)
