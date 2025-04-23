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
    shipment_items (dict[str,in]): the list of items in the shipment

    """

    # Deepu's local/root server.
    #conn, cursor = connect_to_bmart_db('127.0.0.1', 'root', 'DocDeeps!', 'cs314_project')

    conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt') #iwu database server

    #Raise error if connection is unsuccessful
    if conn is None or not conn.is_connected():
        raise Error("Unable to Connect")
    
    try:

        #Start a new transaction
        conn.start_transaction()

        print(40*"-")    
        print("Shipment Details")
        print(40*"-")      

        #check if shipment exists in the DB
        cursor.execute("""
                        SELECT shipment_id, delivered FROM shipments
                        WHERE shipment_id = %s
                        """, (shipment_id,))
        
        shipment_valid = cursor.fetchone()

        if shipment_valid == None :
            raise ValueError("Invalid Shipment!")
            #If shipment id is not in the database, raise an error as we don't want to process unmarked shipments
        elif shipment_valid['delivered'] == 1:
            raise ValueError("Shipment already processed!")
            #If shipment has already been processed, raise an error as we don't want to reprocess shipments
        
        #check if store exists in the DB
        cursor.execute("""
                        SELECT store_id FROM stores
                        WHERE store_id = %s
                    """, (store_id,))
        
        store_valid = cursor.fetchone()

        if store_valid == None:
            raise ValueError("Invalid Store!")
            #If store id is not in the database, raise an error as we are processing for a non-BMart store
        

        # Check if shipment has valid reorders
        # Basically checking that all items in the shipment_items dictionary are EXPECTED to be in this shipment
        # Based on the reorders pooled in the shipment.
        # This is understood from an intermediary table, reorder_in_shipments

        #Might delete this
        #Because what if two reorders for the same item are in the same shipment
        # Then, length of shipment items is 1, but length of reorders list is 2
        cursor.execute(
                        """
                        SELECT reorders_in_shipments.reorder_id FROM shipments
                        JOIN reorders_in_shipments ON shipments.shipment_id = reorders_in_shipments.shipment_id
                        WHERE shipments.shipment_id = %s
                        AND reorders_in_shipments.reorder_id IN (SELECT reorder_id FROM reorder_requests);
                        """, (shipment_id,))

        valid_reorders = cursor.fetchall()

        if len(valid_reorders) != len(shipment_items):
            raise ValueError("Shipment contains unplaced reorders!")

        #Checking item counts and shipment sizes
        
        #Checking if shipment items are in reorders associated with the shipment
        # So, same product_id and same item count
        # Also check total product count
        # 

        # "Manually" count the total number of items in the shipment
        shipment_size = 0
        for key in shipment_items.keys():
            shipment_size = shipment_items[key] + shipment_size
        
        #Compare to the expected total number of items on the shipment
        cursor.execute("SELECT shipments.expected_num_items FROM shipments WHERE shipments.shipment_id = %s", (shipment_id,))
        expected_shipment_count = cursor.fetchone()

        # Basically checking that all items in the shipment_items dictionary are EXPECTED to be in this shipment
        # Based on the reorders pooled in the shipment.
        # This is understood from an intermediary table, reorder_in_shipments
        # This query returns the products ordered, the quantity of products ordered,
        # and whether the reorder request has been marked as completed.
        cursor.execute(
                        """
                        SELECT reorder_requests.product_ordered, reorder_requests.quantity_of_product, reorder_requests.completed FROM shipments
                        JOIN reorders_in_shipments AS ros ON shipments.shipment_id = ros.shipment_id
                        JOIN reorder_requests ON ros.reorder_id = reorder_requests.reorder_id
                        WHERE shipments.shipment_id = %s
                        """, (shipment_id,))
        
        items_in_reorders = cursor.fetchall()
        #print(items_in_reorders)
        #print(shipment_items)

        #Create a dictionary of discrepancies between reorder and shipment
        item_discrepancies = {}

        # Create a dictionary of expected items in the shipment
        # This will be similar to the shipment_items parameter, but is built from the DB
        expected_items = {}

        #Check each reorder
        for record in items_in_reorders:
            #if product_ordered - how much shipped != 0:
            #add to dictionary:  [product_ordered]: item discrepancy
            if record['completed'] == 1:
                raise ValueError("The reorder has already been processed and completed!")
                #ensures that the reorder request is still active and needs to be stocked

            product_UPC = str(record['product_ordered']) #label for the product ordered
            expected_product_count = record['quantity_of_product'] 

            #Append reorder data of a product from the DB to our dictionary
            expected_items[product_UPC] = expected_product_count

                        #check that the shipment size is accurate
            if expected_shipment_count['expected_num_items'] != shipment_size:
                print("Incorrect shipment size!")

            #Calculate any item discrepancies
            item_discrepancy = expected_product_count - shipment_items[product_UPC]

            #Append any item discrepancies to the item discrepancy dictionary
            if item_discrepancy != 0:
                item_discrepancies[product_UPC] = item_discrepancy
            
        
        #Check that shipment size  = expected shipment count
        #Then check that reorder item count = shipment item count
        # 

        #Updates shipments DB
        # Sets the shipment received dat to the current timestamp
        # Also marks that shipment has been delivered     
        cursor.execute("""UPDATE shipments
                SET received_delivery = current_timestamp(), delivered = TRUE
                WHERE shipment_id = %s""",
                (shipment_id,))
        

        #Update shipments table for number of total shipped items
        cursor.execute("""UPDATE shipments
                       SET num_shipped_items = %s
                       WHERE shipment_id = %s"""
                       , (shipment_size, shipment_id))
        
        #Update Inventory Table
        #Also create a dictionary of stocked items for items that have been entered into the inventory
        stocked_items = {}

        for key in shipment_items.keys():
            cursor.execute("""UPDATE inventory
                    SET inventory.current_inventory = inventory.current_inventory + %s
                    WHERE inventory.product_UPC = %s
                    AND inventory.store_id = %s""",(shipment_items[key], key, store_id))
            stocked_items[key] = shipment_items[key]
        

        #Mark reorder request as completed after stocking;
        #Don't invoke if any of the previous steps fail

        cursor.execute(
            """UPDATE reorder_requests JOIN reorders_in_shipments
                ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id
                SET reorder_requests.completed = TRUE
                WHERE reorders_in_shipments.shipment_id = %s;""", (shipment_id,))
        
        conn.commit()

        #Print Output
        
        cursor.execute("SELECT shipments.received_delivery, shipments.expected_delivery, shipments.vendor_name FROM shipments WHERE shipments.shipment_id = %s", (shipment_id,))
        shipment_data = cursor.fetchone()

        print(f"Shipment Delivery Date:\t{shipment_data['received_delivery']}")
        print(f"Expected Delivery Date:\t{shipment_data['expected_delivery']}\n")
        print(f"Vendor:\t{shipment_data['vendor_name']}\n")

        #Find product name given product UPC
        cursor.execute("SELECT products.product_UPC, products.product_name FROM products")

        product_names = {}

        product_data = cursor.fetchall()
        
        for record in product_data:
            product_data = []
            for key in record.keys():
                product_data.append(record[key])
            product_names[product_data[0]] = product_data[1]
             
        print("Expected Product Counts:")
        for key in expected_items.keys():
            print(f"{key} - {product_names[key]}:\t{expected_items[key]}")
        print()
        print("Actual Product Counts:")
        for key in stocked_items.keys():
            print(f"{key} - {product_names[key]}:\t{stocked_items[key]}")
        print()
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
    #Sample test cases below

    #Test case should work and will not display any item discrepancies
    stock(1,2,{'710492385612': 50, '680193472561': 50})

    #Raises Value Error that store is invalid
    #stock(14,25, {'nothing':2})
  
