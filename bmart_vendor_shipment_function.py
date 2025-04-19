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
        shipment_items (dict{str:int}): Dictionary containing pairs of the item name and the amount of each item being shipped
        vendor_name (str): The name of the vendor sending the reorder
    """
    # Potential SQL issues:
    # reorder foreign key error * check 3rd
    # product doesn't exist, or isn't in any of the reorders

    # Check if items are being reordered.

    conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt')
    if not conn.is_connected() or conn is None:
        print("unable to connect")
        return

    try:
        conn.start_transaction()

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
        store = cursor.fetchone()
        if not store:
            raise ValueError(f"The input store does not exist: {store}")

        # check if reorder numbers exist and match up to the store. Also count items remaining in reorders
        expected_item_count = 0
        items_expected = []
        for reorder in reorders:
            cursor.execute("SELECT reorder_requests.store_id, reorder_requests.quantity_of_product, reorder_requests.percent_completed, products.product_name "
                           "FROM reorder_requests "
                           "JOIN products ON reorder_requests.product_ordered = prodcuts.product_UPC "
                           "WHERE reorder_requests.reorder_id = %s",
                           (reorder,))
            reorder_valid = cursor.fetchone()
            if not reorder_valid:
                raise ValueError(f"One of the reorder numbers does not exist: {reorder}")
            elif store != reorder_valid[0][0]:
                raise ValueError(f"One of the reorder numbers does not match the store id: {reorder}")
            quantity = reorder_valid[0][1]
            percent_compete = reorder_valid[0][2]
            items_expected.append(reorder_valid[0][3])
            expected_item_count += quantity * (1 - percent_compete)

        # get count of items in shipment
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
        cursor.execute("UPDATE reorder_requests SET confirmed = 1 WHERE reorder_id in %s", (reorders,))

        conn.commit()


        # Print manifest
        print(f"New Shipment Processed, Shipment_no: {new_ship_id}")
        print("Shipment Manifest:")
        for item in shipment_items:
            print(f"{item} : {shipment_items.get(item)}")
        print()

        # Print reorders forfilled by this shipment
        print(f" Shipment {new_ship_id} forfills Reorder(s):")
        for reorder in reorders:
            print(reorder)

        # Print outstanding Count of Store
        cursor.execute("SELECT count(reorder_requests.reorder_id) "
                       "FROM reorder_requests "
                       "LEFT JOIN reorders_in_shipments ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id" # any reorder in a shipment is no longer outstanding
                       "WHERE reorder_requests.vendor_name = %s AND reorder_requests.store_id = %s AND reorders_in_shipments.shipment_id = NULL",
                       (vendor_name, store))
        store_outstanding = cursor.fetchone()
        print(f"Outstanding Reorder Requests to store {store}: {store_outstanding}")

        # Print Bmart outstanding count
        cursor.execute("SELECT count(reorder_requests.reorder_id) "
                       "FROM reorder_requests "
                       "LEFT JOIN reorders_in_shipments ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id "
                       "WHERE reorder_requests.vendor_name = %s AND reorders_in_shipments.shipment_id = NULL",
                       (vendor_name))
        bmart_outstanding = cursor.fetchone()
        print(f"Outstanding Reorders Requests to Bmart: {bmart_outstanding}")


    except ValueError:
        print(f"Value Error: {ValueError}")
        conn.rollback()
    except Error:
        print(f"Database Error: {Error}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()
