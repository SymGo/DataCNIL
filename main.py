from flask import Flask, render_template, request
from configparser import ConfigParser
from sshtunnel import SSHTunnelForwarder
import matplotlib
matplotlib.use('Agg')
import smtplib
import re
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from flask_caching import Cache
import stats


# Create a Flask app instance
app = Flask(__name__)
config = ConfigParser()
config.read('config.ini')

app.config['SECRET_KEY'] = config.get('app', 'SECRET_KEY')
app.config['OWN_EMAIL'] = config.get('app', 'OWN_EMAIL')
app.config['OWN_PASSWORD'] = config.get('app', 'OWN_PASSWORD')
DATABASE_URI = 'dialect+driver://username:password@host:port/database'

cache = Cache(config={'CACHE_TYPE': 'simple'})

# Initialize the cache with default settings
cache.init_app(app)

# connection to the database with sqlalchemy engine
engine = create_engine(DATABASE_URI)

# retrieval of existing tables in database
metadata = MetaData()
deliberation = Table('Deliberation', metadata, autoload_with=engine)
token = Table('Token', metadata, autoload_with=engine)
token2deliberation = Table('Token2Deliberation', metadata, autoload_with=engine)

# Create a single session with the database
Session = sessionmaker(bind=engine)

# Route for the homepage
@app.route("/", methods=['GET', 'POST'])
@cache.cached()
def index():
    with Session() as db_session:
        latest_delib = (
            db_session.query(deliberation.c).order_by(desc(deliberation.c.DateTexte)).limit(20).all()
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
        bar_chart = (
            db_session.query(func.year(deliberation.c.DateTexte).label("Année"),
                            func.count(deliberation.c.IDDelib).label("Nombre_de_délibérations"))
                .group_by(func.year(deliberation.c.DateTexte))
                .order_by(func.year(deliberation.c.DateTexte).asc())
                .all()
        )
        global_wordcloud = (
            db_session.query(token.c.Token, func.sum(token2deliberation.c.NbOcc))
                .join(token2deliberation, token.c.IDToken == token2deliberation.c.IDToken)
                .group_by(token.c.Token)
                .order_by(token2deliberation.c.NbOcc.desc())
                .all()
        )
        nb_delib = (
            db_session.query(func.count(deliberation.c.IDDelib)).all()
        )

        nb_delib_count = nb_delib[0][0]
        word_cloud_all = stats.generate_wordcloud(global_wordcloud)
        stats.bar_chart(bar_chart)

        cache.set("latest_delib", latest_delib)

    return render_template('index.html', nb_delib=nb_delib_count, nature_doc=nature_doc, nature_delib=nature_delib, latest_delib=latest_delib, word_cloud_all=word_cloud_all)

@app.route("/deliberation/<int:IDDelib>", methods=['GET', 'POST'])
def get_deliberation(IDDelib):
    IDDelib = IDDelib
    cache.set("IDDelib", IDDelib)
    latest_delib = cache.get("latest_delib")
    search_result = cache.get("search_result")  

    if latest_delib is not None:
        for delib in latest_delib:
            if delib.IDDelib == IDDelib:
                deliberation=delib
                                
    if search_result is not None:
        for delib in search_result:
            if delib.IDDelib == IDDelib:
                deliberation=delib                  

    with Session() as db_session:
        result = (
            db_session.query(token.c.Token, token.c.Lemme, token.c.POS, token2deliberation.c.NbOcc)
                .join(token2deliberation, token.c.IDToken == token2deliberation.c.IDToken)
                .filter(token2deliberation.c.IDDelib == IDDelib)
                .order_by(token2deliberation.c.NbOcc.desc())
                .all()
        )
        if deliberation == None:
            deliberation = (
                db_session.query(deliberation.c).filter(deliberation.c.IDDelib == IDDelib).all()
            )
    
    word_freq = stats.word_frequency(result)

    wordcloud_data = [(t[0], t[-1]) for t in result]
    word_cloud = stats.generate_wordcloud(wordcloud_data)

    return render_template('deliberation.html', IDDelib=IDDelib, deliberation=deliberation, word_freq=word_freq, word_cloud=word_cloud)
        
@app.route("/resultats_recherche", methods=['POST', 'GET'])
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

            cache.set("search_result", search_result)

            result_list = []
            for delib in search_result:
                result = (
                    db_session.query(token.c.Token, token.c.Lemme, token.c.POS, token2deliberation.c.NbOcc)
                        .join(token2deliberation, token.c.IDToken == token2deliberation.c.IDToken)
                        .filter(token2deliberation.c.IDDelib == delib.IDDelib)
                        .order_by(token2deliberation.c.NbOcc.desc()).all()
                )
                result_list.extend(result)

            wordcloud_data = [(t[0], t[-1]) for t in result_list]

            word_freq = stats.word_frequency(result_list)
            word_cloud = stats.generate_wordcloud(wordcloud_data)

        return render_template('resultat_recherche.html',
                        nature_doc=nature_doc,
                        nature_delib=nature_delib,
                        from_date=from_date,
                        to_date=to_date,
                        title_contains=title_contains,
                        title_contains_not=title_contains_not,
                        text_contains=text_contains,
                        text_contains_not=text_contains_not,
                        search_result=search_result, word_freq=word_freq,
                        word_cloud=word_cloud)

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

@app.route("/concordance_et_chronogram", methods=['POST', 'GET'])
def autres_stats():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        # text = request.form.get('concordance-ngram')

        with Session() as db_session:
            left_context_length = 20  # length of left context
            right_context_length = 20  # length of right context
            concordance_query = (
                db_session.query(deliberation.c.IDDelib, deliberation.c.DateTexte, deliberation.c.Contenu) 
                    .filter(deliberation.c.Contenu.like(f'%{search_term}%')).all())

            ngram_query = (
                db_session.query(deliberation.c.DateTexte, func.sum(token2deliberation.c.NbOcc))
                    .join(token2deliberation, deliberation.c.IDDelib == token2deliberation.c.IDDelib)
                    .join(token, token.c.IDToken == token2deliberation.c.IDToken)
                    .filter(token.c.Token == search_term)
                    .group_by(deliberation.c.DateTexte)
                    .order_by(deliberation.c.DateTexte)
                    .all()
            )
    
        stats.n_gram(ngram_query, search_term)
        concordance = stats.concordance(concordance_query, search_term)
    
        return render_template('autres_stats.html', search_term=search_term, results=concordance)
    
    else:

        return render_template('autres_stats.html')


if __name__ == '__main__':
    app.run(debug=True)