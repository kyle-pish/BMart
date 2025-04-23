'''
BMart Stock Function (2.1)
CS314 Spring 2025
Gnandeep Chintala
04/23/2025
'''

from bmart_connection import connect_to_bmart_db
from mysql.connector import Error



def stock(store_id: int, shipment_id : int, shipment_items : dict[str, int] ):
    """
    Function processes shipments that arrive to stores from vendors
    This is done by first checking the validity of the shipment and then updating the store's inventory 
    with the shipment items. If any of the checks fail, print the output error.

    This function outputs the shipment details, including the date the shipment was recieved, the vendor the shipment is from,
    a list of the items and their counts that are expected on the shipment, a list of the actual item counts on the shipment,
    and a list of any discrepancies between the reorder and the shipment.

    param:
    store_id (int): the store that is recieving the shipmet
    shipment_id (int): the shipment that is being stocked
    shipment_items (dict[str,int]): the list of items in the shipment, with the product UPC as the key and the product amount as the value

    """
    # Create a connection to the database using the helper function

    # Deepu's local/root server.
    conn, cursor = connect_to_bmart_db('127.0.0.1', 'root', 'DocDeeps!', 'cs314_project')

    # iwu database server
    # conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt') 

    # Raise error if connection is unsuccessful
    if conn is None or not conn.is_connected():
        raise Error("Unable to Connect")
    
    try:

        # Start a new transaction
        conn.start_transaction()

        print(40*"-")    
        print("Shipment Details")
        print(40*"-")      

        # check if shipment exists in the DB using a query that returns the shipment id and if it is delivered
        # based on the shipment id that is input
        cursor.execute("""
                        SELECT shipment_id, delivered FROM shipments
                        WHERE shipment_id = %s;
                        """, (shipment_id,))
        
        shipment_valid = cursor.fetchone()

        # If shipment id is not in the database, raise an error as we don't want to process unmarked shipments
        if shipment_valid == None :
            raise ValueError("Invalid Shipment!")
        # If shipment has already been processed, raise an error as we don't want to reprocess shipments
        elif shipment_valid['delivered'] == 1:
            raise ValueError("Shipment already processed!")
            
        
        # check if store exists in the DB using a query that selects a store id if it matches the store id that is input
        cursor.execute("""
                        SELECT store_id FROM stores
                        WHERE store_id = %s;
                    """, (store_id,))
        
        store_valid = cursor.fetchone()

        # If store id is not in the database, raise an error as we only process for BMart stores
        if store_valid == None:
            raise ValueError("Invalid Store!")
           
        

        # Check if shipment has valid reorders

        # Basically checking that all items in the shipment_items dictionary are EXPECTED to be in this shipment
        # This is understood from an intermediary table, reorder_in_shipments
        # This query returns all reorders in the shipment by joining the shipments table with intermediary
        # reorders_in_shipments table
        cursor.execute(
                        """
                        SELECT reorders_in_shipments.reorder_id FROM shipments
                        JOIN reorders_in_shipments ON shipments.shipment_id = reorders_in_shipments.shipment_id
                        WHERE shipments.shipment_id = %s
                        AND reorders_in_shipments.reorder_id IN (SELECT reorder_id FROM reorder_requests);
                        """, (shipment_id,))

        valid_reorders = cursor.fetchall()

        # If the shipment items input does not match the number of reorders, raise a ValueError
        if len(valid_reorders) != len(shipment_items):
            raise ValueError("Shipment contains unplaced reorders!")


        # This query returns the list of products sold by the store input using the store_id
        cursor.execute("""
                        SELECT inventory.product_UPC FROM inventory
                        WHERE inventory.store_id = %s;             
                        """, (store_id,))
        
        # This is a list of all items sold by the store that is accessible without SQL
        store_inventory_list = []

        # Populate the store inventory list
        for record in cursor.fetchall():
            for key in record:
                store_inventory_list.append(record[key])
        
        # This is a list of items that are in the shipment but are not actually sold by this specific store
        items_wrong_store = []

        # Populate the list of incorrectly shipped items
        for item in shipment_items.keys():
            if item not in store_inventory_list:
                items_wrong_store.append(item)

        # Find product name given product UPC
        cursor.execute("SELECT products.product_UPC, products.product_name FROM products")

        # Dictionary to hold the names of the product with key as the product UPC and the value as the product name
        product_names = {}

        product_data = cursor.fetchall()
        
        # Populate the product names dictionary

        for record in product_data:
            product_data = []
            for key in record.keys():
                product_data.append(record[key])
            product_names[product_data[0]] = product_data[1]

        # If any item has been incorrectly shipped to the store, raise a value error and list the item name and UPC
        if len(items_wrong_store) > 0:
            for item in items_wrong_store:
                print(f"{product_names[item]}({item}) not sold here!")
            raise ValueError("Items not sold at store have been ordered!")
        
        #Checking item counts and shipment sizes
        
        # Checking if shipment items are in reorders associated with the shipment
        # So, same product_id and same item count
        # Also check total product count
        # 

        # "Manually" count the total number of items in the shipment
        shipment_size = 0
        for key in shipment_items.keys():
            shipment_size = shipment_items[key] + shipment_size
        
        # Compare to the expected total number of items on the shipment
        # This query returns the number of expected items in a shipment given the shipment id
        cursor.execute("SELECT shipments.expected_num_items FROM shipments WHERE shipments.shipment_id = %s", (shipment_id,))
        expected_shipment_count = cursor.fetchone()


        # This query returns the products ordered, the quantity of products ordered, and whether the reorder request has been marked as completed.
        # This is understood from an intermediary table, reorder_in_shipments
        # This checks that all items in the shipment_items dictionary are EXPECTED to be in this shipment 
        cursor.execute(
                        """
                        SELECT reorder_requests.product_ordered, reorder_requests.quantity_of_product, reorder_requests.completed FROM shipments
                        JOIN reorders_in_shipments AS ros ON shipments.shipment_id = ros.shipment_id
                        JOIN reorder_requests ON ros.reorder_id = reorder_requests.reorder_id
                        WHERE shipments.shipment_id = %s
                        """, (shipment_id,))
        
        items_in_reorders = cursor.fetchall()


        # Create a dictionary of discrepancies between reorder and shipment
        item_discrepancies = {}

        # Create a dictionary of expected items in the shipment
        # This will be similar to the shipment_items parameter, but it is built from the DB
        expected_items = {}

        # Populate the above dictionaries
        #This for loop checks that shipment received matches the reorder request
        for record in items_in_reorders:

            # ensures that the reorder request is still active and needs to be stocked by raising a Value Error 
            if record['completed'] == 1:
                raise ValueError("The reorder has already been processed and completed!")
                

            #label for the product ordered
            product_UPC = str(record['product_ordered'])

            #expected 
            expected_product_count = record['quantity_of_product'] 

            # Append reorder data of a product from the DB to our dictionary
            expected_items[product_UPC] = expected_product_count

              # Calculate any item discrepancies
            item_discrepancy = expected_product_count - shipment_items[product_UPC]

            # check that the shipment size is accurate
            if expected_shipment_count['expected_num_items'] != shipment_size:

                # Append any item discrepancies to the item discrepancy dictionary
                if item_discrepancy != 0:
                    item_discrepancies[product_UPC] = item_discrepancy
          


        # Update Database

        # This query sets the shipment receipt date to the current date-time and marks delivered as TRUE  
        cursor.execute("""UPDATE shipments
                SET received_delivery = current_timestamp(), delivered = TRUE
                WHERE shipment_id = %s""",
                (shipment_id,))
        

        # This query updates shipments table for number of total shipped items
        cursor.execute("""UPDATE shipments
                       SET num_shipped_items = %s
                       WHERE shipment_id = %s"""
                       , (shipment_size, shipment_id))
        
        # Create a dictionary of stocked items for items that have been entered into the inventory
        stocked_items = {}

        # This Query updates the inventory table with all items that arrived in the shipment based on the shipment items count,
        # the product UPC, and the store id
        for key in shipment_items.keys():
            cursor.execute("""UPDATE inventory
                    SET inventory.current_inventory = inventory.current_inventory + %s
                    WHERE inventory.product_UPC = %s
                    AND inventory.store_id = %s""",(shipment_items[key], key, store_id))
            stocked_items[key] = shipment_items[key]
        

        # This query marks the reorder request as completed after stocking. 
        # This is only invoked if none of the other steps fail.
        cursor.execute(
            """UPDATE reorder_requests JOIN reorders_in_shipments
                ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id
                SET reorder_requests.completed = TRUE
                WHERE reorders_in_shipments.shipment_id = %s;""", (shipment_id,))
        
        conn.commit()

        # Print Output/ Receipt of shipment
        
        # Query to obtain shipment information like delivery date and vendor name
        cursor.execute("""SELECT shipments.received_delivery, shipments.expected_delivery, 
                       shipments.vendor_name FROM shipments WHERE shipments.shipment_id = %s""", (shipment_id,))
        shipment_data = cursor.fetchone()

        print(f"Shipment Delivery Date:\t{shipment_data['received_delivery']}")
        print(f"Expected Delivery Date:\t{shipment_data['expected_delivery']}\n")
        print(f"Vendor:\t{shipment_data['vendor_name']}\n")

        
        # Prints in the format UPC - Product name : product amount
        print("Expected Product Counts:")
        for key in expected_items.keys():
            print(f"{key} - {product_names[key]}:\t{expected_items[key]}")
        print()

        # Prints in the format UPC - Product name : product amount
        print("Actual Product Counts:")
        for key in stocked_items.keys():
            print(f"{key} - {product_names[key]}:\t{stocked_items[key]}")
        print()

        # Prints in the format UPC - Product name : product amount
        print("Item Discrepancies:")
        if len(item_discrepancies) == 0:
            print("None")
        else:
            for key in item_discrepancies.keys():
                print(f"{key} - {product_names[key]}:\t{item_discrepancies[key]}")
        
        print(40*"-")
        print()


    except ValueError as value_error:
        print(f"Value Error: {value_error}")
        conn.rollback()

    except Error as err:
        print(f"Database Error: {err}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Sample test cases below

    # Test case should work and will display any item discrepancy of 2
    stock(1,2,{'710492385612': 48, '680193472561': 50})

    # Raises Value Error that store is invalid
    # stock(14,25, {'nothing':2})
  
