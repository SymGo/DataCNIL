import plotly.express as px
import pandas as pd
from wordcloud import WordCloud

def generate_wordcloud(text):
    wordcloud = WordCloud().generate(text)

    words = [word for word, freq in wordcloud.words_.items()]
    counts = [freq for word, freq in wordcloud.words_.items()]

    df = pd.DataFrame({'word': words, 'count': counts})

    fig = px.scatter(df, x=0, y=0, text='word', size='count', color='count',
                     hover_data=['word', 'count'],
                     title="Word Cloud",
                     width=800, height=800)

    fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False,
                      xaxis_showticklabels=False, yaxis_showticklabels=False,
                      xaxis_zeroline=False, yaxis_zeroline=False)

    fig.show()
