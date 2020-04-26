from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
import json
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import re
import random


project_name = "Project Re-search"
net_id = "Nana Antwi: nka32, Max Stallop: mls235, Edwin Quaye: eq36, Stephen Adusei Owusu: sa679, Kenneth Harlley: kdh62"

# f = open('nutrients.json',)
# nutrients_data = json.load(f)


def categ_list():
    """Create a list of Cateogries from json file"""
    f = open('nutrients.json',)
    nutrients_data = json.load(f)
    cat_list = []
    for item in nutrients_data:
        food_group = item["FoodGroup"]
        if food_group not in cat_list:
            cat_list.append(food_group)
    f.close()
    return cat_list


def stop_words():
    """Defines short words in english language. Probably a better way to do this
    is to import an nltk corpus stop_words. But I was afraid it might not work
    with heroku
    """
    stop_words = []
    f = open("english_words", "r")
    for x in f:
        line = re.sub('[\n]', '', x)
        stop_words.append(line)
    return stop_words


def split_cat(cat_list):
    """ Split categories into individual groups.
    Returns a dictionary with food group and parent food group
    Example split_cat_dict[dairy] = dairy and eggs product
    """
    cat_list_1 = {}
    stop_words_1 = stop_words()
    for word in cat_list:
        if word == 'American Indian/Alaska Native Foods':
            words = ['American Indian', 'Alaska Native', 'Native']
        else:
            word_1 = word_tokenize(word)
            words = [w for w in word_1 if not w in stop_words_1]
        for food in words:
            if food != 'Products' and food != 'Foods':
                cat_list_1[food] = word
    return cat_list_1


def list_nutrients():
    f = open('nutrients.json',)
    nutrients_data = json.load(f)
    final_list = []
    prem_list = []
    non_nutrients = ["ID", "FoodGroup", "ShortDescrip", "Descrip",
                     "CommonName", "MfgName", "ScientificName", "Energy_kcal"]
    for key in nutrients_data[0].keys():
        if key not in non_nutrients:
            nut_lst = key.split("_")
            final_list.append((nut_lst[0], key))
    f.close()
    for nutrient in final_list:
        nut = nutrient[1].lower()
        if nut.find("usrda") == -1:
            prem_list.append(nutrient)
    return prem_list


@irsystem.route('/', methods=['GET'])
# if nutrient_tup not in output:
def search():
    # get list of nutrients and category name
    query_desc = request.args.get('search')
    nutr_list = request.args.getlist('nutrients')
    cat_list = request.args.get('cat_search')
    p_list = request.args.getlist('selret')
    print("p_list IS" + str(p_list))
    # final = category_filtering(str(cat_list))

    # if anthing is blank do nothing else put nutrients into list and pass category name with it to processing _data function
    if not query_desc and not nutr_list and not cat_list:
        print("HERE 1")
        data = []
        output_message = ''
    else:
        print("HERE 2")
        nutr_val = []
        for nutr in nutr_list:
            nutr_val.append(nutr)
        output_message = "Your search: " + query_desc
        # final = category_filtering(cat_list)
        # category_name = query
        if cat_list:
            category_list = category_filtering(str(cat_list))
        else:
            category_list = json.load(open('nutrients.json',))
        if nutr_val:
            # print("Category List is: " + str(category_list))
            nutr_list = nutrients_filtering(category_list, nutr_val)
        else:
            nutr_val = []
            nutr_list = category_list
        if query_desc:
          # This works only if a user provides a description list
            desc_filt_list = descrip_filtering(query_desc, nutr_list)
            desc_list = rank_results(desc_filt_list, nutr_val)
        else:
            desc_filt_list = nutr_list
            desc_list = rank_results2(desc_filt_list, nutr_val)
        data = desc_list[:10]

    return render_template('boltc.html', name=project_name, netid=net_id, output_message=output_message, data=data, nutr_list=list_nutrients(), cat_list=categ_list())


def processing_data(query_nutrients, category_name):
    output = []
    f = open('nutrients.json',)
    nutrients_data = json.load(f)
    # Loop through all the different food itwms storing their name and category
    for i in range(len(nutrients_data)):
        name = nutrients_data[i]["ShortDescrip"]
        category = nutrients_data[i]["FoodGroup"]
        # for every nutrient requested in the query, compare it with the current food item.
        # If the food item has the correct nutrient and also is in the category name add it to the output
        # and remove the nutrient from the list of requested nutrients since it has been added to the grocery list
        for nutrient in query_nutrients:
            if float(nutrients_data[i][nutrient]) > 0 and category == category_name:
                nutrient_tup = (name, category)
                # if the nutrient is already in the ouptu don't add
                if nutrient_tup not in output:
                    output.append(nutrient_tup)
                query_nutrients.remove(nutrient)
        if query_nutrients == []:
            break
    f.close()
    return output


def category_filtering(query_categories):
    """Filter query categories to include only relevant categories
    """
    f = open('nutrients.json',)
    nutrients_data = json.load(f)
    category_list = categ_list()
    split_cat_dict = split_cat(category_list)
    # separate between input to get list
    q_cat_list = query_categories.split(",")
    # Split query list into individual categories just like original categories in json
    q_split_cat = split_cat(q_cat_list)
    split_cat_keys = split_cat_dict.keys()
    output = []

    # use boolean search to match specific food groups first
    for food_group in q_split_cat:
        if food_group in split_cat_keys:
            food_item = split_cat_dict[food_group]
            if food_item not in output:
                output.append(food_item)

    # if ouput is zero user might have mispelled a food group, so every food group in the list
    # use edit distance to retrieve right nutrient. We should probably set a threshold for edit distance because certain outputs don't
    # make sense
    # else continue
    if len(output) == 0:
        for fgroup in q_split_cat:
            valid_category = edit_distance_search(fgroup, split_cat_keys)
            f_group = split_cat_dict[valid_category[1]]
            if f_group not in output:
                output.append(f_group)

    # use final cats to find food items
    food_output = []
    for food in nutrients_data:
        fgroup = food['FoodGroup']
        if fgroup in output:
            # food id is put into a list: food_output
            # food_item = {"FoodGroup": fgroup,
            #              "ShortDescrip": food['ShortDescrip'], "Descrip":  food['Descrip'], "MfgName":  food['MfgName']}
            food_output.append(food)
    return food_output


def nutrients_filtering(cat_output, query_nutrients):
    """Filter nutrients and rank results based on food_groups that meet the minimum daily requirement
    for a 2000 calorie diet
    """
    # Calorie level based on a 2000 Calorie diet
    calorie_level = {'Protein_g': 34, 'Fat_g': 44, 'Carb_g': 130, 'Sugar_g': 25,
                     'Fiber_g': 28, 'VitA_mcg': 700, 'VitB6_mg': 1.3, 'VitB12_mcg': 2.4,
                     'VitC_mg': 75, 'VitE_mg': 15, 'Folate_mcg': 400, 'Niacin_mg': 14,
                     'Riboflavin_mg': 1.1, 'Thiamin_mg': 1.1, 'Calcium_mg': 1000,
                     'Copper_mcg': 900, 'Iron_mg': 18, 'Magnesium_mg': 310,
                     'Manganese_mg': 1.8, 'Phosphorus_mg': 700, 'Selenium_mcg': 55, 'Zinc_mg': 8}

    nutr_out = []
    nutr_list = []
    for x in list_nutrients():
        nutr_list.append(x[1])

    for food_item in cat_output:
        for nutrient in query_nutrients:
            nutrient = edit_distance_search(nutrient, nutr_list)
            if float(food_item[nutrient[1]]) > 0:
                nutr_out.append(food_item)
                break
    return nutr_out


def descrip_filtering(query_desc, nutr_out):
    """Return a list of food items based on the nutrient input
    Return type is a list of dictionaries
    """
    stop_words_1 = stop_words()
    quer_desc = query_desc.lower()
    quer_desc = str(set(quer_desc.split()))
    descrip_list = []
    # Stemming
    ps = PorterStemmer()
    word_tokens = word_tokenize(query_desc)
    word_tokens_1 = [w for w in word_tokens if not w in stop_words_1]
    stem_set = set([ps.stem(word) for word in word_tokens_1])

   # Find the intersection between the query description and the food description
    # and if it's greater than 0, then there's a match.
    for food_item in nutr_out:
        # Stem the descriptions in json file
        longd = word_tokenize(food_item['Descrip'].lower())
        set_longd = set([ps.stem(descp) for descp in longd])

        if len(stem_set.intersection(set_longd)) > 0:
            if food_item not in descrip_list:
                descrip_list.append(food_item)
                continue

    return descrip_list
    # long_descrip=set(word_tokenize(food_item['Descrip']))
    #   food_item = {"FoodGroup": fgroup,
    #              "ShortDescrip": food['ShortDescrip'], "Descrip":  food['Descrip'], "MfgName":  food['MfgName']}


def curr_insertion_function(message, j):
    return 1


def curr_deletion_function(query, i):
    return 1


def curr_substitution_function(query, message, i, j):
    if query[i-1] == message[j-1]:
        return 0
    else:
        return 1


def edit_matrix(query, message):

    m = len(query) + 1
    n = len(message) + 1

    chart = {(0, 0): 0}
    for i in range(1, m):
        chart[i, 0] = chart[i-1, 0] + curr_deletion_function(query, i)
    for j in range(1, n):
        chart[0, j] = chart[0, j-1] + curr_insertion_function(message, j)
    for i in range(1, m):
        for j in range(1, n):
            chart[i, j] = min(
                chart[i-1, j] + curr_deletion_function(query, i),
                chart[i, j-1] + curr_insertion_function(message, j),
                chart[i-1, j-1] +
                curr_substitution_function(query, message, i, j)
            )
    return chart


def edit_distance(query, message):
    query = query.lower()
    message = message.lower()

    chart = edit_matrix(query, message)

    return chart[len(query), len(message)]


def edit_distance_search(query, msgs):
    output = []
    for list1 in msgs:
        score = edit_distance(query, list1)
        output.append((score, list1))
    fin = sorted(output, key=lambda x: x[0])
    return fin[0]


def rank_results(descript_list, query_nutrients):
    """ This function ranks the results of the description filter based on the
    nutrient query. Results with higher input nutrient type will rank higher than results
    with lower input nutrient type.
    For a query like Calcium and Protein and a list of viable descriptions 
    This function will return a dictionary like:

    {protein: [{Nutrient Info1},....
    Calcium: [{Nutrient Info1}, ...}]}
    """
    if query_nutrients:
        output = {}
        nut_score_dict = {}
        nutr_list = []
        final_ranks = []
        for x in list_nutrients():
            nutr_list.append(x[1])

        for nutrient in query_nutrients:
            nutrient_1 = edit_distance_search(nutrient, nutr_list)
            nut = nutrient_1[1]
            for item in descript_list:
                if nut not in nut_score_dict:
                    nut_score = float(item[nut])
                    nut_score_dict[nut] = [(item, nut_score)]
                elif nut in nut_score_dict:
                    nut_score = float(item[nut])
                    nut_score_dict[nut].append((item, nut_score))

        for nutrient in nut_score_dict.keys():
            nutrient_list = nut_score_dict[nutrient]
            fin = sorted(nutrient_list, key=lambda x: x[1], reverse=True)
            output[nutrient] = fin

        for nut_data in output.keys():
            rank_set = list(output[nut_data])
            for i in range(11):
                final_ranks.append(rank_set[i][0])

            final_ranks = random.shuffle(final_ranks)
            return final_ranks
    else:
        return descript_list[:10]


def rank_results2(query_nutrients):
    """Use this function if the user does not provide a description
    """
    f = open('nutrients.json',)
    nutrients_data = json.load(f)
    ranks = rank_results(nutrients_data, query_nutrients)
    return ranks