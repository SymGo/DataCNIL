from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from sshtunnel import SSHTunnelForwarder
import pandas as pd 
import mysql.connector as mysql
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import smtplib
import re
from flask_sqlalchemy import SQLAlchemy
import connexion


OWN_EMAIL = 'marko.python.test@gmail.com'
OWN_PASSWORD = 'ykordwhlvmciffbw'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
# app.config ['SQLALCHEMY_DATABASE_URI'] = connexion.DATABASE_URI
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db = SQLAlchemy(app)

@app.route("/", methods=('GET', 'POST'))
def index():    
    connexion.open_ssh_tunnel()
    connexion.mysql_connect()

    df_latest_del = connexion.run_query("""SELECT IDDelib, Titre, TitreLong, DateTexte 
                                FROM Delib 
                                ORDER BY DateTexte DESC 
                                LIMIT 10""")

    df_delib_graph = connexion.run_query("""SELECT YEAR(DateTexte) AS year, COUNT(IDDelib) AS nb 
                                        FROM Delib 
                                        GROUP BY year 
                                        ORDER BY year ASC""")
    x = list(df_delib_graph['year'])
    y = list(df_delib_graph['nb'])
    plt.bar(x, y, color ='maroon', width = 0.8)
    plt.xlabel("Année")
    plt.xticks(rotation=90, ha='right')
    plt.ylabel("Nombre de délibérations")
    plt.title("Nobmre de délibérations par année")
    plt.savefig('static/images/delib.png')
    url = 'static/images/delib.png'

    df_natur_doc = connexion.run_query("SELECT NatureDocument, COUNT(NatureDocument) AS NbDoc FROM Delib GROUP BY NatureDocument")
    df_natur_delib = connexion.run_query("SELECT NatureDeliberation, COUNT(NatureDeliberation) AS NbDelib FROM Delib GROUP BY NatureDeliberation")

    connexion.mysql_disconnect()
    connexion.close_ssh_tunnel()
    
    if request.method == 'POST':
        nature_doc = request.form.getlist('nature_doc_box')
        nature_delib = request.form.getlist('nature_delib_box')
        from_date = request.form.get('from-date')
        to_date = request.form.get('to-date')
        title_contains = request.form.get('title-contains')
        title_contains_not = request.form.get('title-contains-not')
        text_contains = request.form.get('text-contains')
        text_contains_not = request.form.get('title-contains-not')
        return render_template('search.html',
                               nature_doc=nature_doc,
                               nature_delib=nature_delib,
                               from_date=from_date,
                               to_date=to_date,
                               title_contains=title_contains,
                               title_contains_not=title_contains_not,
                               text_contains=text_contains,
                               text_contains_not=text_contains_not)
    
    return render_template('index.html', df_latest_del=df_latest_del, url=url, df_natur_doc=df_natur_doc, df_natur_delib=df_natur_delib)

@app.route("/a_propos")
def get_about():
    return render_template('a_propos.html')

@app.route("/contact", methods=['POST', 'GET'])
def get_contact():
    if request.method == 'POST':
        data = request.form
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        email = data.get("email")
        subject = data.get("subject")
        if all(value for value in [firstname, lastname, email, subject]):
            match = re.match(r'[^@]+@[^@]+\.[^@]+', email)
            if match:
                send_email(firstname, lastname, email, subject)
                return render_template('nous_contacter.html', msg_sent=True)
            else:
                error = "Veuillez saisir une adresse e-mail valide."
                return render_template('nous_contacter.html',
                                       firstname=firstname,
                                       lastname=lastname,
                                       email=email,
                                       subject=subject,
                                       error=error)
        else:
            error = "Tous les champs sont obligatoires."
            return render_template('nous_contacter.html',
                                   firstname=firstname,
                                   lastname=lastname,
                                   email=email,
                                   subject=subject,
                                   error=error)
    return render_template('nous_contacter.html')


def send_email(first_name, last_name, email, message):
    email_msg = f'Subject: ' \
                f'Nouveau message - DataCNIL\n\n' \
                f'Prénom: {first_name}\n' \
                f'Nom de famille: {last_name}\n' \
                f'Email: {email}\n' \
                f'Message: {message}'
    with smtplib.SMTP('smtp.gmail.com', port=587) as connection:
        connection.starttls()
        connection.login(user=OWN_EMAIL, password=OWN_PASSWORD)
        connection.sendmail(from_addr=email, to_addrs=OWN_EMAIL, msg=email_msg.encode('utf-8'))


@app.route("/resultats", methods=['GET', 'POST'])
def get_results():
    return render_template('search.html')

@app.route("/statistiques")
def get_stats():
    return render_template('stats.html')


if __name__ == '__main__':
    app.run(debug=True)




