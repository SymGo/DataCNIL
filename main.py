from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import sshtunnel
from sshtunnel import SSHTunnelForwarder
import pandas as pd 
import mysql.connector as mysql
import matplotlib.pyplot as plt
import connexion


app = Flask(__name__)


@app.route("/")
def index():    
    connexion.open_ssh_tunnel()
    connexion.mysql_connect()

    df = connexion.run_query("SELECT IDDelib, Titre, TitreLong, DateTexte FROM Deliberation ORDER BY DateTexte DESC LIMIT 10")

    df_delib = connexion.run_query("SELECT AnneeTexte, COUNT(IDDelib) AS nb FROM Deliberation GROUP BY AnneeTexte ORDER BY AnneeTexte ASC")
    x = list(df_delib['AnneeTexte'])
    y = list(df_delib['nb'])
    plt.bar(x, y, color ='maroon', width = 0.8)
    plt.xlabel("Année")
    plt.xticks(rotation=90, ha='right')
    plt.ylabel("Nombre de délibérations")
    plt.title("Nobmre de délibérations par année")
    plt.savefig('static/images/delib.png')
    url = 'static/images/delib.png'

    connexion.mysql_disconnect()
    connexion.close_ssh_tunnel()
    
    return render_template('index.html', df=df, url=url)


if __name__ == '__main__':
    app.run(debug=True)




