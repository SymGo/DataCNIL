import base64
from io import BytesIO
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.graph_objs as go
from plotly.offline import plot
import plotly.express as px
import spacy
from spacy.lang.fr.stop_words import STOP_WORDS

# load the French language model
nlp = spacy.load("fr_core_news_sm", disable=["parser", "ner"])

# get the French stop words
stop_words = STOP_WORDS

def bar_chart(data):
    # extract the data from the query results
    years = [result[0] for result in data]
    nb_delibs = [result[1] for result in data]

    # create the plot
    fig = px.bar(x=years, y=nb_delibs)
    fig.update_traces(marker=dict(color='#6ca486'))
    fig.update_layout(
        xaxis_title="Année",
        yaxis_title="Nombre de délibérations",
        title="Nombre de délibérations par année",
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # save the plot to a file
    fig.write_html('static/images/delib.html')
    return 0

def n_gram(data, text="cnil"):
    # create x and y data from input data
    years = [item[0] for item in data]
    counts = [int(item[1]) for item in data]
    print(years)
    print(counts)

    # create Plotly line chart
    trace = go.Scatter(
        x=years,
        y=counts,
        mode='lines',
        line=dict(color='rgb(31, 119, 180)'),
        fill='tozeroy'
    )

    # set layout of chart
    layout = go.Layout(
        title=text,
        xaxis=dict(title='Année'),
        yaxis=dict(title='Fréquence mot')
    )

    # create figure
    fig = go.Figure(data=[trace], layout=layout)

    # save the plot to a file
    fig.write_html('static/images/ngram.html')
    return 0

def word_frequency(query):

    # create a dictionary mapping each word to its frequency
    word_freq = {word: freq for word, freq in query if not word in stop_words}

    items = list(word_freq.items())
    first_five = items[:5]

    return first_five

def generate_wordcloud(word_freq):

    # create a dictionary mapping each word to its frequency
    word_freq = {word: int(freq) for word, freq in word_freq if not word in stop_words}

    # generate word cloud
    wordcloud = WordCloud(background_color="white").generate_from_frequencies(word_freq)

    # render word cloud to in-memory buffer
    buf = BytesIO()
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)

    # encode image data as Base64 string
    base64_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    # return Base64-encoded image data
    return base64_image
