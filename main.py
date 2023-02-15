from flask import Flask, render_template, request
<<<<<<< HEAD
#from flask_mysqldb import MySQL
=======
>>>>>>> 489ab7137fb0b7f5ab9b6b84f50023cdd6a4643e
from sshtunnel import SSHTunnelForwarder
import pandas as pd 
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
import smtplib
import re
<<<<<<< HEAD
#from flask_sqlalchemy import SQLAlchemy
import connexion
=======
from sqlalchemy import *
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
>>>>>>> 489ab7137fb0b7f5ab9b6b84f50023cdd6a4643e


# Constants for email and password
OWN_EMAIL = 'marko.python.test@gmail.com'
OWN_PASSWORD = 'ykordwhlvmciffbw'

# Create a Flask app instance
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
<<<<<<< HEAD
# app.config ['SQLALCHEMY_DATABASE_URI'] = connexion.DATABASE_URI
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db = SQLAlchemy(app)

@app.route("/", methods=('GET', 'POST'))
def index():    
    connexion.open_ssh_tunnel()
    connexion.mysql_connect()

    df_latest_del = connexion.run_query("""SELECT IDDelib, Titre, TitreLong, DateTexte 
                                FROM Deliberation 
                                ORDER BY DateTexte DESC 
                                LIMIT 10""")

    df_delib_graph = connexion.run_query("""SELECT YEAR(DateTexte) AS year, COUNT(IDDelib) AS nb 
                                        FROM Deliberation 
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

    df_natur_doc = connexion.run_query("SELECT NatureDocument, COUNT(NatureDocument) AS NbDoc FROM Deliberation GROUP BY NatureDocument")
    df_natur_delib = connexion.run_query("SELECT NatureDeliberation, COUNT(NatureDeliberation) AS NbDelib FROM Deliberation GROUP BY NatureDeliberation")

    connexion.mysql_disconnect()
    connexion.close_ssh_tunnel()
=======

with SSHTunnelForwarder(
        ('i3l.univ-grenoble-alpes.fr', 22),
        ssh_username='merabetw',
        ssh_pkey='static/SSHprivatekey',
        remote_bind_address=('localhost', 3306)
) as tunnel:
    tunnel.start()
    print('Server connected via SSH...')
    local_port = str(tunnel.local_bind_port)
    engine = create_engine('mysql+pymysql://merabetw:&merabetw,@localhost:' + local_port + '/merabetw')

    metadata = MetaData()
    deliberation = Table('Deliberation', metadata, autoload_with=engine)
    token = Table('Token', metadata, autoload_with=engine)
    token2deliberation = Table('Token2Deliberation', metadata, autoload_with=engine)


    # Create a single session for the entire application
    Session = sessionmaker(bind=engine)
    # session = Session()

    latest_delib = None
    search_result = None
    
    # Route for the homepage
    @app.route("/", methods=('GET', 'POST'))
    def index():
        with Session() as session:
            global latest_delib
            latest_delib = (
                session.query(deliberation.c).order_by(desc(deliberation.c.DateTexte)).limit(10).all()
            ) 

            nature_doc = (
                session.query(deliberation.c.NatureDocument, func.count(deliberation.c.NatureDocument).label("NbDoc"))
                .group_by(deliberation.c.NatureDocument)
                .all()
            )
            nature_delib = (
                session.query(deliberation.c.NatureDeliberation, func.count(deliberation.c.NatureDeliberation).label("NbDoc"))
                .group_by(deliberation.c.NatureDeliberation)
                .all()
            )            

        return render_template('index.html', nature_doc=nature_doc, nature_delib=nature_delib, latest_delib=latest_delib)
>>>>>>> 489ab7137fb0b7f5ab9b6b84f50023cdd6a4643e
    
    @app.route("/resultats/<int:IDDelib>", methods=['GET', 'POST'])
    def get_article(IDDelib):
        # global latest_delib
        global article
        for delib in latest_delib:
            if delib.IDDelib == IDDelib:
                article = delib
                break

        return render_template('search.html', article=article)
    
    @app.route("/resultats", methods=['POST', 'GET'])
    def get_results():
        if request.method == 'POST':
            nature_doc = request.form.getlist('nature_doc_box')
            nature_delib = request.form.getlist('nature_delib_box')
            from_date = request.form.get('from-date')
            to_date = request.form.get('to-date')
            title_contains = request.form.get('title-contains')
            title_contains_not = request.form.get('title-contains-not')
            text_contains = request.form.get('text-contains')
            text_contains_not = request.form.get('text-contains-not')

            with Session() as session:
                global search_result
                # Construct the query
                query = session.query(deliberation)

                # Add conditions for the nature of the document and the nature of the deliberation
                if nature_doc:
                    query = query.filter(deliberation.c.NatureDocument.in_(nature_doc))
                if nature_delib:
                    query = query.filter(deliberation.c.NatureDeliberation.in_(nature_delib))

                # Add conditions for the date range
                if from_date:
                    query = query.filter(deliberation.c.DateTexte >= from_date)
                if to_date:
                    query = query.filter(deliberation.c.DateTexte <= to_date)

                # Add conditions for the title and text of the deliberation
                if title_contains:
                    query = query.filter(deliberation.c.TitreLong.contains(title_contains))
                if title_contains_not:
                    query = query.filter(~deliberation.c.TitreLong.contains(title_contains_not))
                if text_contains:
                    query = query.filter(deliberation.c.Contenu.like(f"%{text_contains}%"))
                if text_contains_not:
                    query = query.filter(~deliberation.c.Contenu.like(f"%{text_contains_not}%"))

                # Execute the query and get the results
                search_result = query.all()

            return render_template('search.html',
                            nature_doc=nature_doc,
                            nature_delib=nature_delib,
                            from_date=from_date,
                            to_date=to_date,
                            title_contains=title_contains,
                            title_contains_not=title_contains_not,
                            text_contains=text_contains,
                            text_contains_not=text_contains_not,
                            search_result=search_result)

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

    @app.route("/statistiques")
    def get_stats():
        if article:
            

            return render_template('stats.html', article=article)

        if search_result:
            

            return render_template('stats.html', search_result=search_result)


    if __name__ == '__main__':
        app.run(debug=True)




