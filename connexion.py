import sshtunnel
from sshtunnel import SSHTunnelForwarder, logging
import mysql.connector as mysql
import pandas as pd
import pymysql

#
# DATABASE_URI = "mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_ADDR}/{DB_NAME}".format(
#     DB_USER="dimitrim",
#     DB_PASS="&dimitrim,",
#     DB_ADDR="i3l.univ-grenoble-alpes.fr:3306",
#     DB_NAME="merabetw",
# )


def open_ssh_tunnel(verbose=False):
    """Open an SSH tunnel and connect using a username and password.
    
    :param verbose: Set to True to show logging
    :return tunnel: Global SSH tunnel connection
    """
    
    if verbose:
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG
    
    global tunnel
    tunnel = SSHTunnelForwarder(
        ('i3l.univ-grenoble-alpes.fr', 22),
        ssh_username = 'dimitrim',
        ssh_pkey = 'static/SSHKey2',
        remote_bind_address = ('localhost', 3306)
    )
    tunnel.start()

def mysql_connect():
    """Connect to a MySQL server using the SSH tunnel connection
    
    :return connection: Global MySQL database connection
    """
    
    global connection
    connection = mysql.connect(
        host='127.0.0.1',
        user='merabetw',
        passwd='&merabetw,',
        db='TL_DataCNIL',
        # db='TL_DataCNIL',
        port=tunnel.local_bind_port
    )

def run_query(sql):
    """Runs a given SQL query via the global database connection.
    
    :param sql: MySQL query
    :return: Pandas dataframe containing results
    """
    
    return pd.read_sql_query(sql, connection)

def mysql_disconnect():
    """Closes the MySQL database connection.
    """
    
    connection.close()

def close_ssh_tunnel():
    """Closes the SSH tunnel connection.
    """
    
    tunnel.close