'''
BMart Reorder Function (2.1)
CS314 Spring 2025
Joel Madrigal
'''

from bmart_connection import connect_to_bmart_db
from mysql.connector import Error
from datetime import datetime


def reorder(store_id: int) -> None:
    """
    This function updates in-progress reorders and creates new reorders to stock the current inventory of a given store to the max/product.

    This does so by first checking that the store id entered to run this code is valid and is a store that exists in BMART.

    Then, before any reorders are considered or made, we check that stores inventory, ensure that we got an inventory, and it has something in it,
    and determine the remaining product count for each product in the inventory at that moment. From here, we look at that stores reorder requests, 
    and for the ones that are in progress(unconfirmed with the vendor), we replace the quantity of that reorder with the corresponding product count
    derived from the inventory. After reorder updates are considered/complete (after considering unconfirmed reorder requests), we create new reorders to
    fill the inventory of all products sold by a store to the max.

    If no errors occur, we output to the console:
        Confirmation that reorder updates or creation has happened,
        Which products were reordered, how many of them, and if the reorder for that product was an update or a new reorder,
        How many reorders just were updated and created per their vendor,
        What the total cost of all updated and made reorders was based on the standard price of the product which is agreed upon between the store and the vendor.

    Parameters:
        store_id (int): The ID/unique identifier of a specific BMART store.

    Returns:
        None
    """

    try:

        # Helper function from connection file with a connection to our database.
        conn, cursor = connect_to_bmart_db(
            'cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt')

        # Break out of the program if we can't connect.
        if not cursor or not conn:
            print(
                "Could not make a connection to the database. Please reconfirm connection credentials...")
            return

        try:

            # List to store all of the store IDs in the db, to check if the parameter is valid.
            valid_store_ids = []

            # Dictionary to store inventory products as the key and the amount remaining until that product is filled to the max and that products vendor and its vendor price as the value as a list.
            products_to_be_ordered = {}

            # Helper list to store UPCs of products in reorders for a store that are unconfirmed.
            reorder_prod_unconfirmed = []

            # After reorders have been updated and created, the UPC (key) and [quantity reordered, vendor] (value) are stored here for ease of printing later.
            final_reorders_updated = {}
            final_reorders_made = {}

            # Total price of all reorders made for a store.
            total_cost = 0

            # Helper dictionaries to store the vendor (key) as well as how many reorders (value) for printing later.
            products_updated_per_vend = {}
            products_made_per_vend = {}

            # Safely starting a transaction.
            conn.start_transaction()

            # Quick store ID select see all of the existing store IDs.
            store_id_validity_check = ("SELECT stores.store_id FROM stores;")
            cursor.execute(store_id_validity_check)

            # Look through, add the ID to a list.
            for id in cursor:
                valid_store_ids.append(id["store_id"])

            # Look through list, if the parameter is somewhere in the list, run the code.
            if store_id in valid_store_ids:

                # SELECT to grab needed info from the inventory table for a store to derive how many products remain until that product it filled, and its vendor.
                prod_query = (
                    "SELECT inventory.product_UPC, inventory.current_inventory, inventory.max_inventory, products.vendor_name, products.standard_price, products.product_name FROM inventory "
                    "JOIN products ON inventory.product_UPC = products.product_UPC "
                    "JOIN stores ON inventory.store_id = stores.store_id "
                    "WHERE stores.store_id = %s;")

                cursor.execute(
                    prod_query, (store_id,))

                inventory_products = cursor.fetchall()

                # Check that we successfully got the stores inventory...
                if len(inventory_products) > 0:

                    for prod_stocking in inventory_products:

                        # If the product amount isnt full...
                        if prod_stocking["current_inventory"] < prod_stocking["max_inventory"]:

                            # Calculate how much left is needed for the product to be stocked.
                            derived_prod_amt = prod_stocking["max_inventory"] - \
                                prod_stocking["current_inventory"]

                            # Add that as the value to its UPC, add the vendor name, add the standard pricen and add the name of the product.
                            # And no, im not the genius that came up with how to nicely convert MySQL decimal to Python numbers.
                            # https://python-forum.io/thread-31068.html
                            products_to_be_ordered[prod_stocking["product_UPC"]] = [
                                derived_prod_amt, prod_stocking["vendor_name"], float(prod_stocking["standard_price"]), prod_stocking["product_name"]]

                        # Otherwise, its full, so don't add it to the dict, or don't consider it
                        # This isn't a product that needs its reorder updated NOR needs a reorder created at the moment.
                        else:
                            continue

                # Rollback and throw error if we didn't.
                else:
                    conn.rollback()
                    print(
                        f'Error fetching inventory for store {store_id}. Unable to proceed and make reorders.')
                    return

                # Here, check the in progress reorders from given store.
                update_or_insert_check = ("SELECT * FROM reorder_requests "
                                          "JOIN stores ON reorder_requests.store_id = stores.store_id "
                                          "WHERE reorder_requests.confirmed != TRUE && stores.store_id = %s;")

                cursor.execute(update_or_insert_check, (store_id,))
                check = cursor.fetchall()

                # Add the products in the in-progress reorders to a list for use later.
                for i in check:
                    reorder_prod_unconfirmed.append(i["product_ordered"])

                # In-progress reorder updating query, to be executed conditionally later...
                reorder_update_in_progress = ("UPDATE reorder_requests SET reorder_requests.quantity_of_product = %s "
                                              "WHERE reorder_requests.product_ordered = %s AND reorder_requests.confirmed != TRUE AND "
                                              "reorder_requests.store_id = %s;")

                # New reorder creation query, also to be executed conditionally later...
                reorder_insert_fill_inv = (
                    "INSERT INTO reorder_requests VALUES (DEFAULT, %s, %s, FALSE, FALSE, %s, %s, %s);")

                # Iterate through all of our products that need updating or reordering...
                for product_upc, quantity_and_vendor in products_to_be_ordered.items():

                    # If the current one is in the list of products that are in a reorder thats in progress...
                    if product_upc in reorder_prod_unconfirmed:

                        # Run the updating query, and set the dictionary containing the final updated reorders to have the UPC, quantity updated and its products' vendor.
                        cursor.execute(reorder_update_in_progress,
                                       (quantity_and_vendor[0], product_upc, store_id))
                        final_reorders_updated[product_upc] = quantity_and_vendor

                    # Opposite query run here for when we see a product that is not in an in-progress reorder...
                    else:

                        # Run the insertion query...
                        cursor.execute(
                            reorder_insert_fill_inv, (quantity_and_vendor[0], datetime.now(), store_id, quantity_and_vendor[1], product_upc))
                        final_reorders_made[product_upc] = quantity_and_vendor

                # If we get to here, meaning no errors have occured, commit all changes to the DB.
                conn.commit()

                # Check to make we made any reorder updates or created any reorders before we print anything...
                if len(final_reorders_updated) > 0 or len(final_reorders_made) > 0:
                    print(
                        f'====== Reorder(s) have been made/updated in store {store_id}! ======')

                    print()

                    # Show the updated orders to the console...
                    if len(final_reorders_updated) > 0:
                        print("Updated reorders: ")
                        for upc, quantity in final_reorders_updated.items():
                            print(
                                f'Unconfirmed reorder for product ({upc} - {quantity[3]}) was updated to have {quantity[0]} items!')

                            # This is for finding products/vendor, check if we've seen the vendor before,
                            # if we haven't add it to the dict with its value being occurance count, then
                            # we add multiply the price of the product by its quantity and add that to the total cost
                            # variable anytime a reorder gets updated or created.
                            if quantity[1] not in products_updated_per_vend:
                                products_updated_per_vend[quantity[1]] = 1
                                total_cost += quantity[0] * quantity[2]

                            # If we have found it, add the occurance back into the dict.
                            else:
                                products_updated_per_vend[quantity[1]] += 1
                                total_cost += quantity[0] * quantity[2]

                    else:
                        print("No reorders were updated.")

                    print()

                    # Same exact thing here but going throught the created reorders dict...
                    if len(final_reorders_made) > 0:
                        print("New reorders: ")
                        for upc, quantity in final_reorders_made.items():
                            print(
                                f'Reorder for product ({upc} - {quantity[3]}) was successfully created with {quantity[0]} items!')
                            if quantity[1] not in products_made_per_vend:
                                products_made_per_vend[quantity[1]] = 1
                                total_cost += quantity[0] * quantity[2]

                            else:
                                products_made_per_vend[quantity[1]] += 1
                                total_cost += quantity[0] * quantity[2]

                    else:
                        print("No reorders were created.")

                    print()

                    # Printing the products/vendor data here, same looping through dictionary style here....
                    if len(products_updated_per_vend) > 0:
                        print("Unconfirmed reorders updated/vendor: ")
                        for vendor, reorder_count in products_updated_per_vend.items():
                            print(
                                f'For vendor {vendor}, there were {reorder_count} reorder(s) updated.')

                    print()

                    # Same idea here as the one above...
                    if len(products_made_per_vend) > 0:
                        print("Reorders created/vendor: ")
                        for vendor, reorder_count in products_made_per_vend.items():
                            print(
                                f'For vendor {vendor}, there were {reorder_count} reorder(s) created.')

                    print()

                    # Just printing total cost of all reorders whether they're updates or new ones.
                    print(
                        f'The total cost of all reorders in store {store_id} was ${total_cost}.')

                    print()

                    print(
                        "====== Your reorders have been successfully updated/created to fill your current inventory, thank you! ======")

                    print()

                else:
                    print("There were no reorders updated or made.")

            # Otherwise, the store id parameter isn't a valid store ID, so rollback, log error and return.
            else:
                conn.rollback()
                print("That is not a valid store ID, please try again.")
                return

        # If there was an error doing any SQL work, rollback all work, and show to the console.
        except ValueError as val_error:
            conn.rollback()
            print("This value error has occurred: ", val_error)
            raise e

        except Error as e:
            conn.rollback()
            print("This SQL error has occured: ", e)
            raise e

    # After everything, close the connection and cursor safely.
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':

    # Will run due to valid store IDs...
    reorder(1)
    reorder(2)
    reorder(3)
    reorder(4)
    reorder(5)
    reorder(6)
    reorder(7)
    reorder(8)
    reorder(9)
    reorder(10)
    reorder(11)
    reorder(12)
    reorder(13)

    print()

    # Will fail due to invalid store IDs...
    reorder(0)
    reorder(14)
    reorder(54)
    reorder('0')
    reorder('4')
    reorder("11")
    reorder("Im haxoring Brian Mart... muahahahah")
