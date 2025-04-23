'''
BMart Stock Function (2.1)
CS314 Spring 2025
Gnandeep Chintala
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
        
        print(shipment_items)

        #Check if store id exists
        cursor.execute("""SELECT COUNT(stores.store_id) FROM stores
                            WHERE stores.store_id = %s""", (store_id,))
        valid_stores = cursor.fetchone()
        
        if valid_stores["COUNT(stores.store_id)"] == 0:
            print( "Invalid Store ID")
            return

        #Check if shipment id exist
        #Check that shipment delivered is False
        cursor.execute("""SELECT shipments.shipment_id, shipments.delivered FROM shipments
                        WHERE shipments.shipment_id = %s""", (shipment_id,))
        
        cursor_result = cursor.fetchone()
        print(cursor_result)


        if cursor_result == None:
            print("Invalid Shipment")
            return
        #elif cursor_result['delivered'] != False:
        #    print("Shipment Already Delivered!")
        #    return
        
        #Check that all the reorders of the shipment_items parameter exist in shipment_id(shipment_id parameter)
        cursor.execute("""SELECT shipments.shipment_id, reorders_in_shipments.reorder_id, reorder_requests.product_ordered, stores.store_id FROM shipments 
                            JOIN reorders_in_shipments ON shipments.shipment_id = reorders_in_shipments.shipment_id
                            JOIN reorder_requests ON reorders_in_shipments.reorder_id = reorder_requests.reorder_id
                            JOIN stores ON reorder_requests.store_id = stores.store_id
                            WHERE stores.store_id = %s && shipments.shipment_id = %s""", (store_id, shipment_id))

        valid_reorders_in_ship = cursor.fetchall()


        for record in valid_reorders_in_ship:
        
            if record["product_ordered"] in shipment_items:
                print("yes")
            else:
                print('bad')
            

         #Mark as delivered
        cursor.execute("""UPDATE shipments
                SET received_delivery = current_timestamp(), delivered = TRUE
                WHERE shipment_id = %s""",
                (shipment_id,))

           
        ##if shipment date later than expected date, print shipment delayed error -> Need to do


        # Check shipment size by manually counting total items in the shipment
        shipment_size = 0
        for key in shipment_items.keys():
            shipment_size = shipment_items[key] + shipment_size
        
        #Raise error if shipment size < total reorder request count
         #if reorder size <  shipment size; raise error: improper shipment?

        cursor.execute("""UPDATE shipments
                       SET num_shipped_items = %s
                       WHERE shipment_id = %s"""
                       , (shipment_size, shipment_id))
        
        #Change data in the inventory table

               #if new inventory size >  max inventory size, raise error: shipment too large
        #Calculate how much larger and provide that in the exception

        for key in shipment_items.keys():
            cursor.execute("""UPDATE inventory
                    SET inventory.current_inventory = inventory.current_inventory + %s
                    WHERE inventory.product_UPC = %s
                    AND inventory.store_id = %s""",(shipment_items[key], key, store_id))

        #Mark reorder request as completed after stocking;
        #Don't invoke if any of the previous steps fail

        query = (
            """UPDATE reorder_requests JOIN reorders_in_shipments
                ON reorder_requests.reorder_id = reorders_in_shipments.reorder_id
                SET reorder_requests.completed = TRUE
                WHERE reorders_in_shipments.shipment_id = %s;"""
        )

        
        cursor.execute(query, (shipment_id,))
        

    except ValueError as value_error:
        print(f"Value Error: {value_error}")
        conn.rollback()

    except Error as err:
        print(f"Database Error: {err}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

stock(2,3,{"659382047193": 75, "158372946021": 50})