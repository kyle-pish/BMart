"""
Bmart Vendor Shipment Function
Tom Komatsu Cs314
"""

from bmart_connection import connect_to_bmart_db
import mysql.connector
from mysql.connector import Error
import datetime

def vendor_shipment(store : int, delivery_date : str, reorders : list[int], shipment_items : dict[str,int], vendor_name : str) -> None:
    """
    Creates shipments to Bmart stores from the vendors. Also prints the shipment manifest,
    the reorders its fulfilled, count of outstanding reorders from store, count of total outstanding reorders.

    Params:
        store (int): The store id that the shipment is going to.
        delivery_date (str): The date of expected delivery in yyyy-mm-dd format
        reorders (list[int]): list of reorder numbers that the shipment intends to satisfy
        shipment_items (dict{str:int}): Dictionary containing pairs of the item upc and the amount of each item being shipped
        vendor_name (str): The name of the vendor sending the reorder
    """

    # Get connection and cursor, check if connected
    conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt')
    if not conn:
        print("unable to connect")
        return

    try:
        # Connected now starting transaction.
        conn.start_transaction()
        committed = False

        # check if date is valid format
        try:
            del_datetime = datetime.datetime.fromisoformat(delivery_date)
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")

        # Check if date is in the future
        current_date = datetime.datetime.today()
        if current_date >= del_datetime:
            raise ValueError(f"Expected Delivery Date is not in the future: {delivery_date}")

        # Check if store exists.
        cursor.execute("SELECT * FROM stores WHERE store_id = %s", (store,))
        store_check = cursor.fetchone()
        if not store_check:
            raise ValueError(f"The input store does not exist: {store}")

        # vendor exists check
        cursor.execute("SELECT * FROM vendors WHERE vendor_name = %s LIMIT 1", (vendor_name,))
        vendor_check = cursor.fetchone()
        if not vendor_check:
            raise ValueError(f"The input vendor does not exist: {vendor_name}")

        # check if reorder numbers exist and match up to the store. Also count items remaining in reorders
        expected_item_count = 0
        items_expected = []
        for reorder in reorders:
            cursor.execute("SELECT reorder_requests.store_id, reorder_requests.quantity_of_product, reorder_requests.product_ordered, reorder_requests.vendor_name, reorders_in_shipments.shipment_id, reorder_requests.completed "
                           "FROM reorder_requests "
                           "LEFT JOIN reorders_in_shipments ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id "
                           "WHERE reorder_requests.reorder_id = %s ",
                           (reorder,))
            reorder_valid = cursor.fetchone()

            # check if exists, store, vendor, and if its already in a shipment
            if not reorder_valid:
                raise ValueError(f"One of the reorder numbers does not exist: Reorder {reorder}")
            elif store != reorder_valid['store_id']:
                raise ValueError(f"One of the reorder numbers does not match the store id given: Reorder {reorder}")
            elif vendor_name != reorder_valid['vendor_name']:
                raise ValueError(f"One of the reorder numbers does not match the vendor name given: Reorder {reorder}")
            elif reorder_valid['completed']:
                raise ValueError(f"One of the reorder numbers is already completed: Reorder {reorder}")
            elif reorder_valid['shipment_id'] is not None:
                raise ValueError(f"One of the reorder is already in a shipment: Reorder {reorder}")

            quantity = reorder_valid['quantity_of_product']
            items_expected.append(reorder_valid['product_ordered'])
            expected_item_count += quantity

        # get count of items in shipment and check if they should be in shipment
        actual_item_count = 0
        for item in shipment_items:
            actual_item_count += shipment_items.get(item)
            if item not in items_expected:
                raise ValueError("Items do not match reorder request")
        if expected_item_count < actual_item_count:
            raise ValueError("This contains more items than requested")

        # All inputs checked and query inputs aquired
        # Input shipment
        cursor.execute("INSERT INTO shipments "
                       "VALUES(default, %s, NULL, %s, %s, FALSE, %s, %s)",
                       (del_datetime, expected_item_count, actual_item_count, store, vendor_name,))

        new_ship_id = cursor.lastrowid

        # Add reorders in ships
        for reorder in reorders:
            cursor.execute("INSERT INTO reorders_in_shipments VALUES(%s, %s)",
                           (reorder, new_ship_id,))
            # Update confirmation if not confirmed
            cursor.execute("UPDATE reorder_requests SET confirmed = 1 WHERE reorder_id = %s",
                           (reorder,))

        conn.commit()
        committed = True

        # Print manifest
        print(f"New Shipment Processed: Shipment {new_ship_id}")
        print(f"===== Shipment {new_ship_id} Manifest =====")
        # get item names
        for item in shipment_items:
            cursor.execute("SELECT product_name "
                           "FROM products "
                           "WHERE product_UPC = %s",
                           (item,))
            item_name = cursor.fetchone()
            print(f"{item} | {item_name['product_name']} | {shipment_items.get(item)}")
        print()

        # Print reorders forfilled by this shipment
        print(f"Shipment {new_ship_id} fulfills Reorder(s):")
        print(reorders)

        # Print outstanding Count of Store
        cursor.execute("SELECT count(reorder_requests.reorder_id) "
                       "FROM reorder_requests "
                       "LEFT JOIN reorders_in_shipments ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id " # any reorder in a shipment is no longer outstanding
                       "WHERE reorder_requests.vendor_name = %s AND reorder_requests.store_id = %s AND reorders_in_shipments.shipment_id is null",
                       (vendor_name, store))
        store_outstanding = cursor.fetchone()
        print()
        print(f"Outstanding Reorder Requests to store {store}: {store_outstanding['count(reorder_requests.reorder_id)']}")

        # Print Bmart outstanding count
        cursor.execute("SELECT count(reorder_requests.vendor_name) "
                       "FROM reorder_requests "
                       "LEFT JOIN reorders_in_shipments ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id "
                       "WHERE reorder_requests.vendor_name = %s AND reorders_in_shipments.shipment_id is null",
                       (vendor_name,))
        bmart_outstanding = cursor.fetchone()
        print(f"Outstanding Reorders Requests to Bmart: {bmart_outstanding["count(reorder_requests.vendor_name)"]}")
        print()

    # Whenever there is an error, print error and rollback
    except ValueError as valerr:
        print(f"Value Error: {valerr}")
        conn.rollback()
    except Error as err:
        if committed:
            print("Shipment was processed and commited to database, other error occurred:")
        print(f"Database Error: {err}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':


    ####### TEST CODE ######
    store_id_1 = 1
    store_id_2 = 2
    store_id_3 = 5090
    store_id_4 = 3
    delivery_date_1 = "2025-12-30"
    delivery_date_2 = "2023-12-30"
    delivery_date_3 = "7-000"
    reorders_1 = [1,2]
    reorders_2 = [3,4,5,6]
    reorders_3 = [35,36]
    reorders_4 = [5,6,7]
    reorders_5 = [11,12]
    shipment_1 = {"823647195038":100,
                  "810237465920":100}
    shipment_2 = {"158372946021":50,
                  "274918305672":75,
                  "659382047193":50}
    shipment_3 = {"987120345768":50,
                  "204839176502":50}
    vendor_1 = "C&S Wholesale Grocers"
    vendor_2 = "asdfu"
    vendor_3 = "US Foods"

    # should work once
    vendor_shipment(store_id_1, delivery_date_1,reorders_1, shipment_1,vendor_1)
    vendor_shipment(store_id_2, delivery_date_1, reorders_4, shipment_2, vendor_1)
    vendor_shipment(store_id_4,delivery_date_1,reorders_5,shipment_3,vendor_3)

    # should fail
    vendor_shipment(store_id_2, delivery_date_1, reorders_1, shipment_1, vendor_1)
    vendor_shipment(store_id_3, delivery_date_1, reorders_1, shipment_1, vendor_1)
    vendor_shipment(store_id_1, delivery_date_2, reorders_1, shipment_1, vendor_1)
    vendor_shipment(store_id_1, delivery_date_3, reorders_1, shipment_1, vendor_1)
    vendor_shipment(store_id_1, delivery_date_1, reorders_1, shipment_1, vendor_2)
    vendor_shipment(store_id_1, delivery_date_1, reorders_2, shipment_1, vendor_1)
    vendor_shipment(store_id_1, delivery_date_1, reorders_3, shipment_1, vendor_1)
    vendor_shipment(store_id_1, delivery_date_1, reorders_4, shipment_1, vendor_1)
    vendor_shipment(store_id_1, delivery_date_1, reorders_1, shipment_2, vendor_1)
    vendor_shipment(store_id_1, delivery_date_1, reorders_5, shipment_2, vendor_1)