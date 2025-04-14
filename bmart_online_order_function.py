'''
BMart Online Order Function
CS314 Spring 2025
Kyle Pish
'''

from bmart_connection import connect_to_bmart_db
import mysql.connector
from mysql.connector import Error


def online_order(store_id, customer_id, order_items):
    """
    Function to process online orders
    online_orders will:
        Check that the input customer and store are valid
        Check the inventory of the store
        If all items are avaliable, the order is placed and the store inventory is updated
        If an item is not avaliable, the order is cancelled and check stores in the same state to see if they have the item

        Output results to console
            If success:
                Details about the order they just placed, including their own information for confirmation
                A list of the ordered items and their quantities
                The total price for that order, based on the current store price for each of those items.

            If failure:
                Output error details (invalid customer, invalid store, item not in inventory, etc.)
                If store doesn't have an item that was ordered but another store in the same state does, output that stores info

    Params:
        store_id (int): Unique identifier for a BMart store
        customer_id (int): Unique identifier for a unique customer
        order_items (dict[str, int]): Dictionary containing key, value pairs of product_UPC, item_quantity
    """

    conn, cursor = connect_to_bmart_db('127.0.0.1', 'root', 'tC!9PLCu7c', 'cs314') # Kyle's local server
    # conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt') # Actual project server

    # If there is an error in connection and no cursor is made then exit the function
    if not cursor:
        return
    
    try:
        # Using conn.start_transaction allows for manual commit and rollback
        # Since this function can make multiple related changes to the database, avoiding autocommit
        # can make rollback easier if one of multiple related changes is invalid
        # https://stackoverflow.com/questions/52723251/mysql-connector-python-how-to-use-the-start-transaction-method
        conn.start_transaction()

        # With a successful connection and cursor creation...

        # Check that the input customer is valid
        cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        #print(customer)
        if not customer:
            raise ValueError(f"The input customer does not exists: customer_id {customer_id}")
        
        # Check that the input store is valid
        cursor.execute("SELECT * FROM stores WHERE store_id = %s", (store_id,))
        store = cursor.fetchone()
        if not store:
            raise ValueError(f"The input store does not exist: store_id {store_id}")

        # Check that all products to order are valid and in stock
        invalid_inventory = []
        invalid_items = []
        order_price = 0.0

        # Check over each item in the order_items to ensure they are valid products and in stock
        for product, quantity in order_items.items():
            cursor.execute("SELECT 1 FROM products WHERE product_UPC = %s", (product,))
            valid_product = cursor.fetchone()

            # Ensure that the product to order is actually a valid item (exists in the products table)
            if not valid_product:
                invalid_items.append(product)
                continue

            cursor.execute("SELECT current_inventory, product_price FROM inventory WHERE store_id = %s AND product_UPC = %s", (store_id, product))
            result = cursor.fetchone()

            # If query returns nothing or if the customer tries to order more than the store has
            if result is None or result['current_inventory'] < quantity:
                invalid_inventory.append(product)
            # If everything is good, add item price to the order cost
            else:
                order_price += result['product_price'] * quantity

        if invalid_items or invalid_inventory:
            print("Your order could not be completed")
            for product in invalid_items:
                print(f"- Product {product} is not sold by any BMart stores currently")
            
            for product in invalid_inventory:
                print(f"- BMart store {store_id} does not have enough of product {product} in stock")

                # If product exists but store doesn't have enough inventory, check other BMarts in same state
                cursor.execute("SELECT stores.store_id, stores.city, inventory.current_inventory FROM stores JOIN inventory ON stores.store_id = inventory.store_id WHERE stores.state = %s and inventory.product_UPC = %s AND inventory.current_inventory >= %s", (store['state'], product, order_items[product]))
                other_stores = cursor.fetchall()

                if other_stores:
                    print(f"Product {product} is avaliable at: ")
                    for store in other_stores:
                        print(f"- Store {store['store_id']} in {store['city']} (Quantity in stock: {other_stores['current_inventoy']})")
                else:
                    print(f"We apologize, product {product} is not avaliable in any nearby store")
            conn.rollback()
            return
        
        # Place the order

        # Output confirmation

    finally:
        cursor.close()
        conn.close()



if __name__ == '__main__':

    order_items = {
        '836492571203': 2000,
        '987654321098': 1
    }

    online_order(store_id=1, customer_id=1, order_items=order_items)