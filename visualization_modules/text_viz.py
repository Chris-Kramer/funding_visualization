import pandas as pd
from math import inf, floor, isnan, ceil
import plotly.express as px
import plotly.graph_objects as go
from typing import Literal, Any
import networkx as nx
from wordcloud import WordCloud, STOPWORDS

####################
# Helper functions #
####################

def _sort_tuples(tuple_list: tuple[Any, int]):
    """
    Returns a sorted list of tuple, sorted by second item
    
    """
    return sorted(tuple_list, key=lambda x: x[1], reverse=True) 


def _make_same_keys(filtered_dict: dict,
                    non_filtered_dict: int) -> dict:
    """
    Creates a dict, which contains the same keys as another dictionary, while still keeping the original values
    """
    return_dict = {}
    for key in filtered_dict:
        val = non_filtered_dict[key]
        return_dict[key] = val
    return return_dict


def _filter_dict(dictionary: dict,
                 lower_thresh: int = 0,
                 upper_thresh: int = inf) -> dict:
    """
    Removes key: value pairs, where the value is not between lower_thresh and upper_thresh
    """
    filtered_dict = {}
    for key, val in dictionary.items(): 
        if  lower_thresh <= val <= upper_thresh:
            filtered_dict[key] = val
    return filtered_dict


def _get_remaining_perc(val: int | float) -> int | float:
    """
    Returns the remaining percent of a value 
    """
    return 100 - val


def _color_scaling(val: int | float,
                   new_min: int |float = 15,
                   new_max = 60, old_min = 0, old_max = 100) -> int | float:
    """
    Convert from a scaling of 0 to 100 to a new range for colors
    """
    val = _get_remaining_perc(val)
    old_range = old_max - old_min
    new_range = new_max - new_min
    return (((val - old_min) * new_range) / old_range) + new_min


def scale_word_dict(word_dict: dict) -> dict:
    """
    Scales word freqs to color scalings
    """
    min_val = min(word_dict.values())
    max_val = max(word_dict.values())
    scaled_dict = {}
    for key, val in word_dict.items():
        z = ((val - min_val) / (max_val - min_val)) * 100 #Scaling to between 0 and 100
        scaled_dict[key] = _color_scaling(z)
    return scaled_dict


def _cal_percentile(number_list, percentile):
    """
    Helper function to 'rescale_to_percentiles' Returns the percentiles for a list of numbers
    """
    return (max(number_list) * percentile)


def rescale_to_percentiles(number_list,
                           lowest: int = 2,
                           median: int = 4,
                           second_highest: int = 6,
                           highest: int = 8):
    """
    Takes a list and returns a list where the values are rescaled in 4 percentiles
    """ 
    lowest_25 = _cal_percentile(number_list, 0.25)
    lowest_50 = _cal_percentile(number_list, 0.50)
    lowest_75 = _cal_percentile(number_list, 0.75)
    rescaled_list = []
    for val in number_list:
        if val < lowest_25:
            rescaled_list.append(lowest)
        elif lowest_25 < val < lowest_50:
            rescaled_list.append(median)
        elif lowest_50 < val < lowest_75:
            rescaled_list.append(second_highest)
        else:
            rescaled_list.append(highest)
    return rescaled_list


def rescale_to_range(number_list, new_max, new_min):
    """
    Rescales a list to a new range
    """
    old_range = max(number_list) - min(number_list)
    new_range = (new_max - new_min)
    scaled_list = []
    for val in number_list:
        if old_range == 0:
            z_val = new_min
        else:
            z_val = ( (val - min(number_list)) * new_range  / old_range) + new_min
        scaled_list.append(ceil(z_val))
    return scaled_list



def get_stop_words(stopword_path: str = "data/stopord.txt") -> list[str]:
    """
    Description
    ------------
    Returns a list of stopwords

    Parameters
    ----------
    stopword_path (str): The path a txt file with stopwords

    Preconditions
    -------------
    The stopwords in the txt-file are seperated by a newline
    """
    # Danish stopwords
    txt = open(stopword_path, "r", encoding='utf-8')
    file_content = txt.read()
    danish_stopwords = file_content.split("\n")
    txt.close()
    
    # English stopwords
    stopwords = list(STOPWORDS)
    
    # custom stopwords
    cust_stop_w = ["-", "–", "samt", "både", "række", "hvilket",
                   "findes", "give", "øget", "ofte", "giver", "del",
                   "projektet", "udviklingen", "baseret", "studier",
                   "within", "1", "1600", "1660", "1978", "1865", "1895",
                    "19", "ranking", "academia", "novel", "new", "using", 
                    "effects", "impact", "materials", "targeting", "early",
                    "function", "high", "role", "using", "based", "non", "no",
                    "s", "t", "2", "effect", "basis", "next", "factors", "acute",
                    "making", "inge", "single", "long", "higher"]
    
    # Combine english and danish
    stopwords.extend(danish_stopwords)
    stopwords.extend(cust_stop_w)
    
    return stopwords

####################
# Public functions #
####################
def tokenize_and_stem(text: str) -> list[str]:
    """
    Get uniques token word stems from text string
    """
    stopwords = get_stop_words()
    tokens = set()
    replace_chars = "; ,.:;*'_#!?´-()^"
    for char in replace_chars:
        text = text.replace(char, " ")
    for token in text.split():
        token = token.lower()
        if token not in stopwords:
            tokens.add(token)
    return list(tokens)


def get_all_words(df: pd.DataFrame) -> list:
    """
    Returns a list of all words in the dataframe
    """
    word_list = []
    # Create Graph
    for text in df["Titel"]:
        # Split each token/word on whitespace
        tokens = tokenize_and_stem(text)
        word_list += tokens
    
    return list(set(word_list))


def dict_to_df(data_dict: dict) -> pd.DataFrame:
    """
    Description
    -----------
    Converts a word - value (such af word - frequency) dict to a dataframe

    Parameters
    ----------
    data_dict (dict): a dictionary where the keys are word and they have and associated value
    """
    return pd.DataFrame({"word": data_dict.keys(), "value": data_dict.values()})


def generate_data(df: pd.DataFrame,
                  funding_thresh_hold: int = 0) -> tuple[dict, dict, dict]:
    """
    Description
    -----------
    Generatives three key: value dictionaries where the key is a word:
    - word: funding
    - word: average funding
    - word: frequency

    Parameters
    ----------
    - df (pandas.DataFrame): A dataframe containing the following columns: 
        - "År" (int), "Titel" (str), "Beskrivelse" (str), "Bevilliget beløb" (int | float)
    - funding_thresh_hold (int): Only get words which have a higher funding than this
        - Default: 0

    Return
    ------
    tuple(dict, dict, dict)
    """
    
    freqs = {} # Absolute frequencies
    funding = {} # Absolute funding recieved

    # Create dict of absolute freqs and funding
    for text, amount in zip(df["Titel"], df["Bevilliget beløb"]):
        tokens = tokenize_and_stem(text)
        # Count unique tokens in each grant application
        for token in tokens:
            if not token in freqs:
                freqs[token] = 1
                funding[token] = amount
            else:
                freqs[token] += 1
                funding[token] += amount

    funding = _filter_dict(funding, funding_thresh_hold)
    freqs = _make_same_keys(funding, freqs)
    
    avg_funding = {}
    for key in funding:   
        avg_funding[key] =  funding[key] // freqs[key]
        
    return (avg_funding, funding, freqs)




    

# ------ Bar plots ------
def create_bar_plot(df,
                    x_col,
                    color_col,
                    color_label = "color label",
                    x_label = "value label",
                    top_n = 50,
                    title = "No Title") -> px.bar:
    """
    Description
    ------------
    Takes as word: value dict and returns as ploty plot
    
    Parameters
    -----------
    - data_dict (dict): A dict where the keys are word and the words associated value. 
      Can be created with the function generate_data(df, funding_thresh).The value determines the size of a word' bar
      Examples of dicts:
        - word: freqency
        - word: funding
        - word: average funding
    - color_dict (dict): A word value dict (like previously), however the value determines the bar color for a word.
    - color_label (str): The label for the colorbar
    - value_label (str): The label for the x_axis
    - title (str): The title of the plot.
    - top_n (int): Only take the top n keys with the highest value.
    
    Return
    -------
    plotly.express.bar 
    
    Preconditions
    -------------
    - data_dict and color_dict contains the same keys.
    
    """
    df["word"] = df["word"].astype(str)
    df = df.sort_values(by = x_col, ascending=True) 
    df = df.head(top_n)
    # I have no Idea why I have to sort it in ascending order to get the words with highest value on top

    fig = px.bar(df,
                  x = x_col,
                  y = "word",
                  color = color_col,
                  hover_data= [x_col, color_col, "funding"],
                  labels = {x_col: x_label,
                            color_col: color_label,
                            "funding": "Total Funding"},
                  color_continuous_scale = px.colors.sequential.Redor, 
                  height = 1000,
                  width = 800,
                  title = title)
    
    fig.update_yaxes(title = "")
    fig.update_layout(coloraxis_colorbar_title_text = color_label, margin=dict(b=50,l=150,r=50,t=50))
    fig.update_layout(hoverlabel = dict( bgcolor = "white"),
                      hoverlabel_font = dict(color = "rgb(0,0,0)"))
    fig.update_layout(yaxis_type='category')    
    return fig

def create_animated_bar(df,
                        y_col,
                        color_col,
                        color_label = "color label",
                        x_label = "value label",
                        title = "No Title",
                        top_n = 50) :
    """
    Creates an animated bar plot
    """
    years = [i for i in range(2013, 2022 + 1)]
    bar_df = pd.DataFrame(columns = ["word", "freqs", "funding", "avg_funding", "year"])
    for year in years:
        temp_df = gen_chart_data(df[df["År"] == year], top_n = top_n, yearly = True, sort_col = "freqs")
        bar_df = pd.concat([bar_df, temp_df])
    
    bar_df = bar_df.sort_values(by = ["year", y_col], ascending= [True, False])
    # I have no Idea why I have to sort it in ascending order to get the words with highest value on top
    fig = px.bar(bar_df,
                    y = y_col,
                    x = "word",
                    color = list(bar_df[color_col]),
                    hover_data= ["funding"],
                    labels = {y_col: x_label,
                              "color": color_label,
                              "funding": "Total Funding"},
                    animation_frame = "year",
                    range_y = [0, max(bar_df[y_col]) + 5],
                    range_color = [min(bar_df[color_col]), max(bar_df[color_col])], 
                    color_continuous_scale = px.colors.sequential.Redor, 
                    title = title)
        
    fig.update_layout(coloraxis_colorbar_title_text = color_label)
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 2000
    fig.update_traces(textfont_color="rgb(0,0,0)")
    fig.update_layout(hoverlabel = dict( bgcolor = "white"),
                      hoverlabel_font = dict(color = "rgb(0,0,0)"))    
    return fig


# ----- Bubble charts ------
def gen_chart_data(df: pd.DataFrame,
                    top_n: int | None = None,
                    yearly: bool = False,
                    sort_col: Literal["freqs", "funding", "avg_funding"] | None = None,
                    words: list[str] | None = None ) -> pd.DataFrame:
    """
    Description
    ------------
    Generates a dataset for bubble charts which can be filterede accorng to words, and/or value of a column
    
    Parameters
    ------------
    - df (pandas.DataFrame): A dataframe containing the following columns: 
      "År" (int), "Titel" (str), "Beskrivelse" (str), "Bevilliget beløb" (int | float)
    - top_n (int | None): The number of highest valued words to choose. If None then all words are chosen.
    - sort_col ("freqs" | "funding", "avg_funding"): The column/value to choose the top_n words from.
        - freqs = choose the top_n most used words each year. If None, the words are not sorted.
        - funding = Choose the top_n most funded words each year
        - avg_funding = Choose the top_n words with the highest average funding each year
    - words (list[str]): A list of strings if you only which to get data for the given words.

    Return
    ------
    A pandas.DataFrame with the following columns:
        - word (str): The word
        - freqs (int): The amount of grants the word is mentioned in.
        - avg_funding (int | float): The average funidng for each grant the word appears in.
        - funding (int | float): The total funding for all papers the word appears in.
        - year (int): The year data is extracted from.
    The dataframe is sorted by year
    """
    years = list(set(df["År"]))
    years.sort()
    df_dict = {"word": [], "freqs": [], "funding": [], "avg_funding": [], "year": []}
    
    if yearly:
        for year in years:
            temp_df = df[df["År"] == year]
            avg_funding, funding, freqs = generate_data(df = temp_df,
                                                        funding_thresh_hold = 0)
            if sort_col == "funding":
                value_dict = funding
            elif sort_col == "avg_funding":
                value_dict = avg_funding
            else:
                value_dict = freqs
            for key in value_dict: 
                if words is None:         
                    df_dict["word"].append(key)
                    df_dict["freqs"].append(freqs[key])
                    df_dict["funding"].append(funding[key])
                    df_dict["avg_funding"].append(avg_funding[key])
                    df_dict["year"].append(year)
                elif words is not None and key in words:
                    df_dict["word"].append(key)
                    df_dict["freqs"].append(freqs[key])
                    df_dict["funding"].append(funding[key])
                    df_dict["avg_funding"].append(avg_funding[key])
                    df_dict["year"].append(year)
    
    else:
        avg_funding, funding, freqs = generate_data(df = df,
                                                    funding_thresh_hold = 0)
        if sort_col == "funding":
            value_dict = funding
        elif sort_col == "avg_funding":
            value_dict = avg_funding
        else: value_dict = freqs
        for key in value_dict:
            if words is None:         
                df_dict["word"].append(key)
                df_dict["freqs"].append(freqs[key])
                df_dict["funding"].append(funding[key])
                df_dict["avg_funding"].append(avg_funding[key])
                df_dict["year"].append("All Years")
            elif words is not None and key in words:
                df_dict["word"].append(key)
                df_dict["freqs"].append(freqs[key])
                df_dict["funding"].append(funding[key])
                df_dict["avg_funding"].append(avg_funding[key])
                df_dict["year"].append("All Years")
      
    df = pd.DataFrame(df_dict)

    if yearly:
        sorted_df = pd.DataFrame(columns = ["word", "freqs", "funding", "avg_funding", "year"])
        for year in years:
            temp_df = df[df["year"] == year]
            if sort_col is not None:
                temp_df = temp_df.sort_values(by=sort_col, ascending = False)
            if top_n is not None:
                temp_df = temp_df.head(top_n)
            sorted_df = pd.concat([sorted_df, temp_df], ignore_index = True)
            
    else:
        if sort_col is not None:
            df = df.sort_values(by=sort_col, ascending = False) 
        
        sorted_df = df.head(top_n)
    
    return sorted_df

def create_bubble_plot(df: pd.DataFrame, 
                       x_col: str,
                       y_col: str,
                       size_col: str,
                       color_col: str,
                       x_strech: int = 0,
                       y_strech: int = 0,
                       max_bub_size: int = 55,
                       title: str = "Title",
                       x_lab: str | None = None,
                       y_lab: str | None = None,
                       size_lab: str | None = None,
                       color_lab: str | None = None) -> px.scatter:
    '''
    Description
    ------------
    Creates a bubble chart displaying the words funding, frequency and average frequency over time.

    Parameters
    ----------
    - A pandas.DataFrame with the following columns:
        - word (str): The word
        - freqs (int): The amount of grants the word is mentioned in.
        - avg_funding (int | float): The average funidng for each grant the word appears in.
        - funding (int | float): The total funding for all papers the word appears in.
        - year (int): The year data is extracted from.
        - The dataframe is sorted by year
    - x_col (str): The column name in df for the values of the x-axis
    - y_col (str): The column name in df for the values of the y-axis
    - size_col( str): The column name in df for the values of which will determine the size of the bubbles
    - color_col (str): The column name in df for the values of which will determine the color of the bubbles
    - x_strech (int): Padding which are added to the x axis 
        - So if min value is 50 and max value is 100 and x_strech is 25 then the x axis will start at 25 and end at 125
        - Default: 0
    - y_strech (int): Padding which are added to the y axis 
        - So if min value is 50 and max value is 100 and y_strech is 25 then the y axis will start at 25 and end at 125
        - Default: 0
    - max_bub_size (int): The max bubble sizes
        - Default: 55
    - title (str): The title of the bubble chart
    - x_lab (str): The labels for the x values
        - Default: x_col
    y_lab (str): The labels for the y values
        - Default: y_col
    size_lab: The label for the value determining the bubble size
        - Default: size_col
    color_lab: The label for the colorbar
        - Default: color_col
    
    Return
    -------
    plotly.express.scatter
    '''
    if x_lab == None:
        x_lab = x_col
    if y_lab == None:
        y_lab = y_col
    if size_lab == None:
        size_lab = size_col
    if color_lab == None:
        color_lab = color_col
    
    try:
        max_x = max(df[x_col]) + (max(df[x_col]) * x_strech)
        min_x = min(df[x_col]) - (max(df[x_col]) * x_strech)
        max_y = max(df[y_col]) + (max(df[y_col]) * y_strech)
        min_y = min(df[y_col]) - (max(df[y_col]) * y_strech)
        x_range = [min_x, max_x]
        y_range = [min_y, max_y]
    except ValueError:
        x_range = 0
        y_range = 0
    fig = px.scatter(df,
                     x=x_col,
                     y=y_col,
                     color= list(df[color_col]),
                     color_continuous_scale=px.colors.sequential.Redor,
                     animation_frame="year",
                     animation_group = "word",
                     size = list(df[size_col]),
                     hover_name="word",
                     size_max = max_bub_size,
                     text = "word",
                     title = title,
                     height= 1000,
                     width = 800,
                     range_x= x_range,
                     range_y= y_range,
                     labels={
                     x_col: x_lab,
                     y_col: y_lab,
                     size_col: size_lab,
                     "year": "Year"
                 }
                    )
    fig["layout"].pop("updatemenus") # Remove buttons (it does not work when animating)
    fig.update_layout(coloraxis_colorbar_title_text = color_lab)
    
    hovertemplate="<br>".join([
        f"<b>Word:</b> " + "%{text}",
        f"<b>{x_lab}:</b> " + "%{x:,.0f}",
        f"<b>{y_lab}:</b> " + "%{y}",
        f"<b>{size_lab}:</b> " + "%{marker.size:,.0f}"])

    fig.update_traces(hovertemplate=hovertemplate)
    for frame in fig.frames:
        frame.data[0].hovertemplate = hovertemplate
    fig.update_traces(textfont_color="rgb(0,0,0)")
    fig.update_layout(hoverlabel = dict( bgcolor = "white"),
                      hoverlabel_font = dict(color = "rgb(0,0,0)"))    
    return fig

def generate_graph_data_word(df: pd.DataFrame, word: str, top_n: int) -> nx.Graph:
    
    avg_funding, funding, freqs = generate_data(df)
    G = nx.Graph()

    i = 0
    # Create Graph
    for text in df["Titel"]:
        # Split each token/word on whitespace
        tokens = tokenize_and_stem(text)
        
        if word not in tokens:
            continue
        
        G.add_node(word,
                   avg_funding = avg_funding[word],
                   funding = funding[word],
                   freqs = freqs[word],
                   total_deg = 0)    
              
        targ_list = []
        for token in tokens:
            if not word == token:
                targ_list.append(token)                               
        
        for targ_tok in targ_list:
            G.add_node(targ_tok,
                        avg_funding = avg_funding[targ_tok],
                        funding = funding[targ_tok],
                        freqs = freqs[targ_tok],
                        total_deg = 0)   
            if G.has_edge(word, targ_tok):
                G[word][targ_tok]["weight"] += 1  
            else:
                G.add_edge(word, targ_tok, weight = 1)

    
    for node, deg in G.degree():
        G.nodes[node]['total_deg'] = deg
    
    edge_weights = []
    for e in G.edges():
        s_node = e[0]
        t_node = e[1]
        edge_weight = G[s_node][t_node]["weight"]
        edge_weights.append((e, edge_weight))
    #
    top_n_edges = [e for e, _ in _sort_tuples(edge_weights)[ : top_n - 1]]
    edges_remove = []
    for e in G.edges():
        if e not in top_n_edges:
            edges_remove.append(e)
            

    G.remove_edges_from(edges_remove)
    G.remove_nodes_from(list(nx.isolates(G)))
    pos = nx.spring_layout(G, weight = "weight", k = 3)
    for node in G.nodes():
        x = pos[node][0]
        y = pos[node][1]
        G.nodes[node]["pos"] = (x, y)
    return G

def generate_graph_data_words(df: pd.DataFrame, words: list[str]) -> nx.Graph:
    
    avg_funding, funding, freqs = generate_data(df)
    G = nx.Graph()

    i = 0
    # Create Graph
    for text in df["Titel"]:
        # Split each token/word on whitespace
        tokens = tokenize_and_stem(text)

        search_words = []
        for token in tokens:
            for word in words:
                if token == word:
                    search_words.append(token)
        
        if len(search_words) <= 1:
            continue
        
        
        source_list = []
        targ_list = []
        for s_word in search_words:
            source_list.append(s_word)
            targ_list.append(s_word)
        
        #print(source_list)
        for s_tok in source_list:
            G.add_node(s_tok,
                        avg_funding = avg_funding[s_tok],
                        funding = funding[s_tok],
                        freqs = freqs[s_tok],
                        total_deg = 0)   

        for s_tok in source_list:
            temp_targ_list = targ_list
            temp_targ_list.remove(s_tok)
            for targ_tok in temp_targ_list:
                if G.has_edge(s_tok, targ_tok):
                    G[s_tok][targ_tok]["weight"] += 1
                else:
                    G.add_edge(s_tok, targ_tok, weight = 1)
    

    for node, deg in G.degree():
        G.nodes[node]['total_deg'] = deg
    
    edge_weights = []
    for e in G.edges():
        s_node = e[0]
        t_node = e[1]
        edge_weight = G[s_node][t_node]["weight"]
        edge_weights.append((e, edge_weight))
    

    pos = nx.spring_layout(G, weight = "weight", k = 3)
    for node in G.nodes():
        x = pos[node][0]
        y = pos[node][1]
        G.nodes[node]["pos"] = (x, y)
    return G

def generate_graph_data_all(df: pd.DataFrame, top_n: int = 10) -> nx.Graph:
    '''
    Description
    -----------
    Preconditions
    -------------
    S
    '''
    avg_funding, funding, freqs = generate_data(df)
    G = nx.Graph()

    i = 0
    # Create Graph
    for text in df["Titel"]:
        # Split each token/word on whitespace
        tokens = tokenize_and_stem(text)
        
        source_list = []
        targ_list = []
        for token in tokens:
            source_list.append(token)
            targ_list.append(token)                               

        for s_tok in source_list:
            G.add_node(s_tok,
                        avg_funding = avg_funding[s_tok],
                        funding = funding[s_tok],
                        freqs = freqs[s_tok],
                        total_deg = 0)   

        for s_tok in source_list:
            temp_targ_list = targ_list
            temp_targ_list.remove(s_tok)
            for targ_tok in temp_targ_list:
                if G.has_edge(s_tok, targ_tok):
                    G[s_tok][targ_tok]["weight"] += 1
                else:
                    G.add_edge(s_tok, targ_tok, weight = 1)
    
    for node, deg in G.degree():
        G.nodes[node]['total_deg'] = deg
    
    edge_weights = []
    for e in G.edges():
        s_node = e[0]
        t_node = e[1]
        edge_weight = G[s_node][t_node]["weight"]
        edge_weights.append((e, edge_weight))
    
    top_n_edges = [e for e, _ in _sort_tuples(edge_weights)[ : top_n - 1]]
    edges_remove = []
    for e in G.edges():
        if e not in top_n_edges:
            edges_remove.append(e)
            

    G.remove_edges_from(edges_remove)
    G.remove_nodes_from(list(nx.isolates(G)))
    pos = nx.spring_layout(G, weight = "weight", k = 4)
    for node in G.nodes():
        x = pos[node][0]
        y = pos[node][1]
        G.nodes[node]["pos"] = (x, y)
    return G


def plot_graph(G,
               title = "All Time",
               max_node_size = 50,
               min_node_size = 20):
    
    

    hover_text = []
    node_index = 0
    if len(G.nodes()) < 2:
        return None
    for node in G.nodes():

        avg_funding_txt = f"{G.nodes[node]['avg_funding']:,}"
        funding_txt = f"{G.nodes[node]['funding']:,}"
        hover_text.append(f"<b>Word</b>: {node} <br>" +
                        f"<b>Total Word Connections</b>: {G.nodes[node]['total_deg']}<br>"
                        f"<b>Frequency</b>: {G.nodes[node]['freqs']}<br>" +
                        f"<b>Average Funding</b>: {avg_funding_txt}<br>" +
                        f"<b>Total Funding</b>: {funding_txt}<br>")
        node_index += 1

    edge_x = []
    edge_y = []
    
    # Create edge labels
    edge_hover_text = []
    weights = []
    for e in G.edges():
        source_node = e[0]
        target_node = e[1]
        weight = G[source_node][target_node]["weight"]
        edge_hover_text.append(f"<b>Words:</b> {e} <br> <b>Number of Co-Appearences in Titles:</b> {weight}")
        weights.append(weight)

    edge_colors = rescale_to_range(weights, new_max = 150, new_min = 220)
    edge_sizes = rescale_to_range(weights, new_max = 10, new_min = 1)
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(tuple([x0, x1]))
        edge_y.append(tuple([y0, y1]))
    
    # Create edge lines
    edge_traces = []
    i = 0
    for ex, ey in zip(edge_x, edge_y):
        edge_size = edge_sizes[i]
        edge_trace = go.Scatter(
            x=ex, y=ey,
            line=dict(color = f"rgba({edge_colors[i]}, 217, 245, 1)",
                    width = edge_size))
        edge_traces.append(edge_trace)
        i += 1
    
    # Create label traces
    edge_labs_x = [(x[1] + x[0])/2 for x in edge_x]
    edge_labs_y = [(y[0] + y[1])/2 for y in edge_y]
    edge_labs_traces = go.Scatter(
        x = edge_labs_x,
        y = edge_labs_y,
        mode = "markers+text",
        hoverinfo = "text",
        hovertext = edge_hover_text,
        text = weights,
        marker=dict(
            size = 40,
            opacity = 0.0,
            line_width= 0
        ),
        textfont=dict(
            size = 10,
            color="rgb(0, 0 , 0)"
        ),
        visible = True
    )
    
    # Create nodes markers
    node_x = []
    node_y = []
    for node in G.nodes():
        x = G.nodes[node]["pos"][0]
        y = G.nodes[node]["pos"][1]
        node_x.append(x)
        node_y.append(y)
    
    text = [str(node) for node in G.nodes()]
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo = "text",
        hovertext = hover_text,
        text  = text,
        textfont=dict(
            size = [],
            color="rgb(0, 0 , 0)"
        ),
        marker=dict(
            color="rgb(245, 158, 169)",
            size= [],
            line_width= 2))
    
    
    node_sizes = [val for _, val in nx.get_node_attributes(G, "total_deg").items()]
    scaled_node_sizes = rescale_to_range(node_sizes, new_max = max_node_size, new_min = min_node_size)
    node_trace.marker.size = scaled_node_sizes

    #if len(node)
    node_trace.textfont.size = rescale_to_range(node_sizes, new_max = 18, new_min = 14)
    title = " "
    
    data = [edge_trace for edge_trace in edge_traces]
    data.append(node_trace)
    data.append(edge_labs_traces)
    fig = go.FigureWidget(data=data,
                layout=go.Layout(
                    height = 1000,
                    width = 800,
                    title= title,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(t=50),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.update_traces(textfont_color="rgb(0,0,0)")
    fig.update_layout(hoverlabel = dict( bgcolor = "white"),
                      hoverlabel_font = dict(color = "rgb(0,0,0)"))        
    return fig


    