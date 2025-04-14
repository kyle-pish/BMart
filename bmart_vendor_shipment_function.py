"""
Bmart Vendor Shipment Function
Tom Komatsu Cs314
"""

from bmart_connection import connect_to_bmart_db
import mysql.connector
from mysql.connector import Error

def vendor_shipment(store : str, delivery_date : str, reorders : list[int], shipment_items : dict[str,int]) -> None:
    """
    Creates shipments to Bmart stores from the vendors. Also prints the shipment manifest,
    the reorders its fulfilled, count of outstanding reorders from store, count of total outstanding reorders.

    Params:
        store (str): The store the shipment is going to.
        delivery_date (str): The date of expected delivery in yyyy-mm-dd format
        reorders (list[int]): list of reorder numbers that the shipment intends to satisfy
        shipment_items (dict{str:int}): Dictionary containing pairs of the item name and the amount of each item being shipped
    """
    # Potential SQL issues:
    # store doesn't exist and fk error *check 2nd
    # date incorrect conversion format *check 1st
    # reorder foreign key error * check 3rd
    # product doesn't exist, or isn't in any of the reorders
    conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt')


    # Tom note to self, make helper function to check if an item is part of a list of reorders
    # also remember to get vendor_name, store_id, and product upcs from reorder