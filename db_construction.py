import os
import spacy
from bs4 import BeautifulSoup
import pandas as pd
import time
import sqlalchemy
from sqlalchemy import MetaData, Table, insert
import glob

start = time.time()

# Path to dataset
path = "./27/"
# path = "./cnil_dataset/"

# get the content of xml files
def tag_extraction(xmlfile, id_delib):
    with open(xmlfile, encoding="utf-8", mode="r") as f:
        soup = BeautifulSoup(f, 'xml')

    # Tag content extraction
    dict = {
        "IDDelib": id_delib,
        "IDCNIL": soup.ID.text, 
        "NatureDocument": soup.NATURE.text, 
        "Titre": soup.TITRE.text, 
        "TitreLong": soup.TITREFULL.text, 
        "Numero": soup.NUMERO.text, 
        "NatureDeliberation": soup.NATURE_DELIB.text,
        "DateTexte": soup.DATE_TEXTE.text, 
        "DatePublication": soup.DATE_PUBLI.text, 
        "EtatJuridique": soup.ETAT_JURIDIQUE.text, 
        "Contenu": soup.CONTENU.text.strip(), 
        "NomFichier": soup.ID.text + ".xml"
    }

    return dict

# clean the content of the deliberations (lowercase and delete whitespace and punctuation)
def clean_data(text):
    text = text.lower()
    doc = nlp(text)
    tokens = [{'Token': token.text, 'Lemme': token.lemma_, 'POS': token.pos_} for token in doc if not token.is_punct and not token.is_space]
    
    return tokens

# insert dictionaries into database using sqlalchemy engine
def insert_many(data_list, table_name):
    with engine.connect() as connection:
        # Get the metadata for the table and the corresponding insert object.
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine, autoload=True)
        insert_stmt = insert(table)

        # Execute the insert statement with the list of data.
        connection.execute(insert_stmt, data_list)


engine = sqlalchemy.create_engine('mysql+pymysql://merabetw:&merabetw,@localhost:3306/merabetw')

print("Chargement model spacy...")
nlp = spacy.load('fr_core_news_md', exclude=['parser', 'attribute_ruler'])

id_delib = 0
id_tok = 0
lexicon = {}

header_tok2delib = ["IDDelib", "IDToken"]
df_tok2delib = pd.DataFrame(columns=header_tok2delib)

# Recursively search for all xml files in the directory and its subdirectories
xml_files = glob.glob(os.path.join(path, '**/*.xml'), recursive=True)

# Count the number of files in the list
num_files = len(xml_files)

# Loop through all files in root_dir and its subdirectories
for dirpath, dirnames, filenames in os.walk(path):
    # Loop through all filenames in the current directory
    for filename in filenames:
        # Check if the file has an XML extension
        if filename.endswith('.xml'):
            # XML file path
            xml_path = os.path.join(dirpath, filename)

            id_delib += 1
            print(f"analyse fichier:{filename} --- fichier {id_delib}/{num_files}")
            data_delib = tag_extraction(xml_path, id_delib)

            for key, value in data_delib.items():
                if key != "IDDelib" and value == "":
                    data_delib[key] = 'N/A'

            # Deliberation insertion in database
            insert_many(data_delib, "Deliberation")

            # Text tokenization and cleaning
            text = data_delib["TitreLong"] + " " + data_delib["Contenu"]
            tokens_dict = clean_data(text)

            for token in tokens_dict:
                # Check if token exists in lexicon dictionary
                key = token["Token"]+token["POS"]
                if key not in lexicon.keys():
                    id_tok += 1
                    lexicon[key] = {
                        "IDToken": id_tok,
                        "Token": token["Token"],
                        "Lemme": token["Lemme"],
                        "POS": token["POS"]
                    }

                key_token = lexicon[key]["IDToken"]
                data_tok2delib = [id_delib, key_token]
                df_tok2delib.loc[len(df_tok2delib.index)] = data_tok2delib

            # grouping same lines in tok2delib to count the occurence of word in xml document
            occurrence = df_tok2delib.groupby(df_tok2delib.columns.tolist()).size().reset_index().rename(columns={0: 'NbOcc'})
            occurrence_list = occurrence.to_dict(orient='records')

            # inserting tok2delib lines into database
            insert_many(occurrence_list, "Token2Deliberation")

            # emptying the dataframes
            df_tok2delib = df_tok2delib.iloc[0:0]
            occurrence = occurrence.iloc[0:0]

# extracting list of inner dictionaries from lexicon
data_tokens = []
for key, value in lexicon.items():
    data_tokens.append(value)
insert_many(data_tokens, "Token")


end = time.time() - start
print('Execution time:', time.strftime("%H:%M:%S", time.gmtime(end)))