'''
BMart Stock Function (2.1)
CS314 Spring 2025
Gnandeep Chintala

04/23/2025
'''

from bmart_connection import connect_to_bmart_db
from mysql.connector import Error


#Based on Joel's Code in the reorder function

def stock(store_id: int, shipment_id : int, shipment_items : dict[str, int] ):

    # Deepu's local server.
    conn, cursor = connect_to_bmart_db('127.0.0.1', 'root', 'DocDeeps!', 'cs314_project') #Deepu's root server

    #conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt') #gjkt database server
    if conn is None or not conn.is_connected():
        raise Error("Unable to Connect")
    
    try:
        conn.start_transaction()

        #check if shipment exists in the DB

        cursor.execute("""
                        SELECT shipment_id, delivered FROM shipments
                        WHERE shipment_id = %s
                        """, (shipment_id,))
        
        shipment_valid = cursor.fetchone()
        print(shipment_valid)

        #print(shipment_valid)

        if shipment_valid == None :
            print("Invalid Shipment!")
            #return
        elif shipment_valid['delivered'] == 1:
            print("Shipment already processed!")
            #return
        
        #check if store exists in the DB
        cursor.execute("""
                        SELECT store_id FROM stores
                        WHERE store_id = %s
                    """, (store_id,))
        
        store_valid = cursor.fetchone()

        #print(store_valid)

        if store_valid == None:
            print("Invalid Store!")
            #return
        
        #print(shipment_items)

        #Check if shipment has valid reorders
        cursor.execute(
                        """
                        SELECT reorders_in_shipments.reorder_id FROM shipments
                        JOIN reorders_in_shipments ON shipments.shipment_id = reorders_in_shipments.shipment_id
                        WHERE shipments.shipment_id = %s
                        AND reorders_in_shipments.reorder_id IN (SELECT reorder_id FROM reorder_requests);
                        """, (shipment_id,))

        valid_reorders = cursor.fetchall()

        if len(valid_reorders) != len(shipment_items):
            print("Shipment contains unplaced reorders!")

        #Checking item counts and shipment sizes
        
        #Checking if shipment items are in reorders associated with the shipment
        # So, same product_id and same item count
        # Also check total product count

        shipment_size = 0
        for key in shipment_items.keys():
            shipment_size = shipment_items[key] + shipment_size
        
        cursor.execute("SELECT shipments.expected_num_items FROM shipments WHERE shipments.shipment_id = %s", (shipment_id,))

        expected_shipment_count = cursor.fetchone()
        print(expected_shipment_count)


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
        expected_items = {}

        for record in items_in_reorders:
            #if product_ordered - how much shipped != 0:
            #add to dictionary:  [product_ordered]: item discrepancy
            if record['completed'] == 1:
                print("The reorder has already been processed and completed!")
                #return
            product_UPC = str(record['product_ordered'])
            expected_product_count = record['quantity_of_product']
            expected_items[product_UPC] = expected_product_count
            item_discrepancy = expected_product_count - shipment_items[product_UPC]
            if expected_shipment_count['expected_num_items'] != shipment_size:
                if item_discrepancy != 0:
                    item_discrepancies[product_UPC] = item_discrepancy
                    #return
                #return
            
        
        print(item_discrepancies)

        
        #Check that shipment size  = expected shipment count
        #Then check that reorder item count = shipment item count
        # 

        #Updates shipments DB
        # Sets the current timestamp, etc.
        # Marks that delivered is true      
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
        #Also create a dictionary of stocked items
        stocked_items = {}
        for key in shipment_items.keys():
            cursor.execute("""UPDATE inventory
                    SET inventory.current_inventory = inventory.current_inventory + %s
                    WHERE inventory.product_UPC = %s
                    AND inventory.store_id = %s""",(shipment_items[key], key, store_id))
            stocked_items[key] = shipment_items[key]
        

        #Mark reorder request as completed after stocking;
        #Don't invoke if any of the previous steps fail

        cursor.execute((
            """UPDATE reorder_requests JOIN reorders_in_shipments
                ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id
                SET reorder_requests.completed = TRUE
                WHERE reorders_in_shipments.shipment_id = %s;"""
        ), (shipment_id,))
        
        conn.commit()

        #Print Output
        #NEed to FINISH!!!!!!!!!!!!
        # Print Output
        # conn.rollbacks at errors above
        #Edit DB for testing code (5 pass and 5 supposed fail)

        print("Shipment Details")
        print(40*"-")      

        cursor.execute("SELECT shipments.received_delivery FROM shipments WHERE shipments.shipment_id = %s", (shipment_id,))
        shipment_date = cursor.fetchone()

        print(f"Shipment Delivery Date:\t{shipment_date['received_delivery']}")
        
        print("Expected Product Counts:")
        for key in expected_items.keys():
            print(f"{key}:\t{expected_items[key]}")
        print()
        print("Actual Product Counts:")
        for key in stocked_items.keys():
            print(f"{key}:\t{stocked_items[key]}")
        print()
        print("Item Discrepancies:")
        for key in item_discrepancies.keys():
            print(f"{key}:\t{item_discrepancies[key]}")


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
    stock(1,2,{'710492385612': 48, '680193472561': 50})
  
