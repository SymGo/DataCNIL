from flask import Flask, render_template, request, session, url_for
from sshtunnel import SSHTunnelForwarder
import matplotlib
matplotlib.use('Agg')
import smtplib
import re
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from flask import jsonify


# Constants for email and password
OWN_EMAIL = 'marko.python.test@gmail.com'
OWN_PASSWORD = 'ykordwhlvmciffbw'

# Create a Flask app instance
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'

with SSHTunnelForwarder(
        ('i3l.univ-grenoble-alpes.fr', 22),
        ssh_username='dimitrim',
        ssh_pkey='static/SSHKey2',
        remote_bind_address=('localhost', 3306)
) as tunnel:
    tunnel.start()
    print('Server connected via SSH...')
    local_port = str(tunnel.local_bind_port)

    # connection to the database with sqlalchemy engine
    engine = create_engine('mysql+pymysql://merabetw:&merabetw,@localhost:' + local_port + '/merabetw')

    # retrieval of existing tables in database
    metadata = MetaData()
    deliberation = Table('Deliberation', metadata, autoload_with=engine)
    token = Table('Token', metadata, autoload_with=engine)
    token2deliberation = Table('Token2Deliberation', metadata, autoload_with=engine)

    # Create a single session with the db
    Session = sessionmaker(bind=engine)
    
    # Route for the homepage
    @app.route("/", methods=['GET', 'POST'])
    def index():
        with Session() as db_session:
            latest_delib = (
                db_session.query(deliberation.c).order_by(desc(deliberation.c.DateTexte)).limit(10).all()
            ) 
            nature_doc = (
                db_session.query(deliberation.c.NatureDocument, func.count(deliberation.c.NatureDocument).label("NbDoc"))
                .group_by(deliberation.c.NatureDocument)
                .all()
            )
            nature_delib = (
                db_session.query(deliberation.c.NatureDeliberation, func.count(deliberation.c.NatureDeliberation).label("NbDoc"))
                .group_by(deliberation.c.NatureDeliberation)
                .all()
            )
            print(latest_delib)
            # Convert query results to dictionaries
            latest_delib_dicts = [dict(row) for row in latest_delib]
            nature_doc_dicts = [dict(nature=nature, count=count) for nature, count in nature_doc]
            nature_delib_dicts = [dict(nature=nature, count=count) for nature, count in nature_delib]

            # Store in session
            session["latest_delib"] = latest_delib_dicts
            session["nature_doc"] = nature_doc_dicts
            session["nature_delib"] = nature_delib_dicts

        return render_template('index.html', nature_doc=nature_doc_dicts, nature_delib=nature_delib_dicts, latest_delib=latest_delib_dicts)

    @app.route("/Deliberation/<int:IDDelib>", methods=['GET', 'POST'])
    def get_deliberation(IDDelib):
        deliberation = None
        for delib in latest_delib:
            if delib.IDDelib == IDDelib:
                deliberation = delib
                session["deliberation"] = deliberation
                break
        return render_template('deliberation.html', deliberation=deliberation)
    
    @app.route("/Resultats", methods=['POST', 'GET'])
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

            with Session() as db_session:
                # Construct the query
                query = db_session.query(deliberation)

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
                session["search_result"] = search_result

            return render_template('resultat_recherche.html',
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

    @app.route("/stats_article")
    def stats_deliberation():
        deliberation = session.get("deliberation")
        return render_template('stats_article.html', deliberation=deliberation)


    @app.route("/stats_")
    def stats_search_query():
        search_result = session.get("search_result")
        return render_template('stats_recherche.html', search_result=search_result)


    if __name__ == '__main__':
        app.run(debug=True)




