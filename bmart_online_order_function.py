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
        check that the input customer and store are valid
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