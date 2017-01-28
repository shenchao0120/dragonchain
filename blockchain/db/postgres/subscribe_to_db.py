"""
Copyright 2016 Disney Connected and Advanced Technologies

Licensed under the Apache License, Version 2.0 (the "Apache License")
with the following modification; you may not use this file except in
compliance with the Apache License and the following modification to it:
Section 6. Trademarks. is deleted and replaced with:

     6. Trademarks. This License does not grant permission to use the trade
        names, trademarks, service marks, or product names of the Licensor
        and its affiliates, except as required to comply with Section 4(c) of
        the License and to reproduce the content of the NOTICE file.

You may obtain a copy of the Apache License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the Apache License with the above modification is
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the Apache License for the specific
language governing permissions and limitations under the Apache License.
"""

__author__ = "Joe Roets, Brandon Kite, Dylan Yelton, Michael Bachtel"
__copyright__ = "Copyright 2016, Disney Connected and Advanced Technologies"
__license__ = "Apache"
__version__ = "2.0"
__maintainer__ = "Joe Roets"
__email__ = "joe@dragonchain.org"


import psycopg2
import psycopg2.extras

from blockchain.qry import format_subscription

from postgres import get_connection_pool
import uuid

""" CONSTANTS """
DEFAULT_PAGE_SIZE = 1000
""" SQL Queries """
SQL_GET_ALL = """SELECT * FROM subscribe_to"""
SQL_INSERT = """INSERT into subscribe_to (
                    subscription_id,
                    subscribed_node_id,
                    host,
                    port,
                    criteria,
                    status
                ) VALUES (%s, %s, %s, %s, %s, %s) """


def insert_subscription(subscription, subscription_id=None):
    """ insert given subscription into database """
    if not subscription_id:
        subscription_id = str(uuid.uuid4())
    values = (
        subscription_id,
        subscription['subscribed_node_id'],
        subscription['host'],
        subscription['port'],
        psycopg2.extras.Json(subscription['criteria']),
        "pending"
    )
    conn = get_connection_pool().getconn()
    try:
        cur = conn.cursor()
        cur.execute(SQL_INSERT, values)
        conn.commit()
        cur.close()
    finally:
        get_connection_pool().putconn(conn)


def get_all(limit=None):
    query = SQL_GET_ALL
    query += """ WHERE (CURRENT_TIMESTAMP - last_time_called) > (synchronization_period * '1 sec'::interval) """
    query += """ ORDER BY status """
    if limit:
        query += """ LIMIT """ + str(limit)

    conn = get_connection_pool().getconn()
    try:
        cur = conn.cursor(get_cursor_name(), cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(query)
        'An iterator that uses fetchmany to keep memory usage down'
        while True:
            results = cur.fetchmany(DEFAULT_PAGE_SIZE)
            if not results:
                break
            for result in results:
                yield format_subscription(result)
        cur.close()
    finally:
        get_connection_pool().putconn(conn)


def get_cursor_name():
    return str(uuid.uuid4())
