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

            valid_store_ids = []

            products_to_be_ordered = {}
            reorder_prod_unconfirmed = []

            final_reorders_updated = {}
            final_reorders_made = {}

            products_updated_per_vend = {}
            products_made_per_vend = {}

            conn.start_transaction()

            store_id_validity_check = ("SELECT stores.store_id FROM stores;")
            cursor.execute(store_id_validity_check)

            for id in cursor:
                valid_store_ids.append(id["store_id"])

            if store_id in valid_store_ids:

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

                update_or_insert_check = ("SELECT * FROM reorder_requests "
                                          "JOIN stores ON reorder_requests.store_id = stores.store_id "
                                          "WHERE reorder_requests.confirmed != TRUE && stores.store_id = %s;")

                cursor.execute(update_or_insert_check, (store_id,))
                check = cursor.fetchall()

                for i in check:
                    reorder_prod_unconfirmed.append(i["product_ordered"])

                reorder_update_in_progress = ("UPDATE reorder_requests SET reorder_requests.quantity_of_product = %s "
                                              "WHERE reorder_requests.product_ordered = %s AND reorder_requests.confirmed != TRUE AND "
                                              "reorder_requests.store_id = %s;")

                reorder_insert_fill_inv = (
                    "INSERT INTO reorder_requests VALUES (DEFAULT, %s, %s, FALSE, FALSE, %s, %s, %s);")

                for product_upc, quantity_and_vendor in products_to_be_ordered.items():

                    if product_upc in reorder_prod_unconfirmed:
                        cursor.execute(reorder_update_in_progress,
                                       (quantity_and_vendor[0], product_upc, store_id))
                        final_reorders_updated[product_upc] = quantity_and_vendor

                    else:
                        cursor.execute(
                            reorder_insert_fill_inv, (quantity_and_vendor[0], datetime.now(), store_id, quantity_and_vendor[1], product_upc))
                        final_reorders_made[product_upc] = quantity_and_vendor

                conn.commit()

                if len(final_reorders_updated) > 0 or len(final_reorders_made) > 0:
                    print("Reorder(s) have been made/updated!")

                    print()

                    if len(final_reorders_updated) > 0:
                        print("Updated reorders: ")
                        for upc, quantity in final_reorders_updated.items():
                            print(
                                f'Unconfirmed reorder for product {upc} was updated to have {quantity[0]} items!')
                            if quantity[1] not in products_updated_per_vend:
                                products_updated_per_vend[quantity[1]] = len(
                                    quantity) // 2
                            else:
                                products_updated_per_vend[quantity[1]
                                                          ] += len(quantity) // 2

                    print()

                    if len(final_reorders_made) > 0:
                        print("New reorders: ")
                        for upc, quantity in final_reorders_made.items():
                            print(
                                f'Reorder for product {upc} was successfully created with {quantity[0]} items!')
                            if quantity[1] not in products_made_per_vend:
                                products_made_per_vend[quantity[1]] = len(
                                    quantity) // 2
                            else:
                                products_made_per_vend[quantity[1]
                                                       ] += len(quantity) // 2

                    print()

                    if len(products_updated_per_vend) > 0:
                        print("Unconfirmed reorders updated/vendor: ")
                        for vendor, reorder_count in products_updated_per_vend.items():
                            print(
                                f'For vendor {vendor}, there were {reorder_count} reorder(s) updated.')
                    else:
                        print("No unconfirmed reorders were updated.")

                    print()

                    if len(products_made_per_vend) > 0:
                        print("Reorders created/vendor: ")
                        for vendor, reorder_count in products_made_per_vend.items():
                            print(
                                f'For vendor {vendor}, there were {reorder_count} reorder(s) created.')
                    else:
                        print("No new reorders were created.")

                    '''Here will be where I print out the total price of all reorders'''

                else:
                    print("There were no reorders updated or made.")

            else:
                conn.rollback()
                print("That is not a valid store ID, please try again.")
                return

        except Error as e:
            conn.rollback()
            print("This error has occured while executing the query(ies). ", e)
            raise e

    finally:
        cursor.close()
        conn.close()


reorder(11)
