import os
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn import metrics
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split

def read_data(path):
    training_data = []
    unlabeled_data = []
    for root, dirs, files in os.walk(path):
        for file in files:
            path = os.path.join(root, file)
            if file != 'unlabeled.review':
                training_data.extend(read_data_from_file(path))
            else:
                unlabeled_data.extend(read_data_from_file(path))
    return training_data, unlabeled_data

def try_parse(review_array):
    error_position = (0, 0)
    element = None
    while element is None:
        try:
            element = ET.fromstringlist(review_array)
        except ET.ParseError as e:
            if e.position == error_position:
                #print(e)
                return False
            else:
                error_position = e.position
                line = review_array[e.position[0]]
                # Some documents have the same characters repeated
                start = e.position[1]
                end = start + 1
                while (end < len(line) and line[end] == line[start]):
                    end = end + 1
                review_array[e.position[0]] = line[:start] + '' + line[end:]
    return element

def read_data_from_file(path):
    print("Read data from file ", path)
    data = []
    unlabeled = False
    if path.endswith('positive.review'):
        is_positive = 1
    elif path.endswith('negative.review'):
        is_positive = 0
    elif path.endswith('unlabeled.review'):
        unlabeled = True
    else:
        return data
        
    with open(path, 'r', encoding='utf-8') as content_file:
        review_array = []
        errors = 0
        total = 0
        for line in content_file:
            #print line
            if line.strip() == '<review>' and len(review_array) != 0:
                #print review
                total = total + 1
                element = try_parse(review_array)                    
                if element: 
                    review = {}
                
                    for child in list(element):
                        review[child.tag] = child.text.strip()
                    
                    if 'rating' in review:
                        review['rating'] = int(round(float(review['rating'])))
                        if not unlabeled:
                            review['target'] = is_positive    
                        data.append(review)
                else:
                    errors = errors + 1
                review_array = ['<review>']
            else:
                if (not line.lstrip().startswith('<')):
                    line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                review_array.append(line)
    if errors > 0:            
        print("Errors: ", errors)
    print("Total: ", total)
    return data

def split_data(data):
    print("Split data")
    train_data, test_data = train_test_split(data, test_size = 0.2, random_state = 1)
    
    train_data_text = [x['review_text'] for x in train_data]
    train_data_target = [x['target'] for x in train_data]
    
    test_data_text = [x['review_text'] for x in test_data]
    test_data_target = [x['target'] for x in test_data]
    
    return train_data_text, train_data_target, test_data_text, test_data_target

def grid_search(text_clf, data, target):
    parameters = {'vect__ngram_range': [(1, 1), (1, 2), (1, 5)],                  
                  'vect__stop_words': [None, 'english'],
                  'tfidf__use_idf': (True, False),
                  'clf__alpha': (1e-2, 1e-3, 1e-4),
                  'clf__max_iter': (10, 50, 100)
    }
    
    gs_clf = GridSearchCV(text_clf, parameters, n_jobs=-1)
    gs_clf = gs_clf.fit(data, target)
    print(gs_clf.best_score_)

    for param_name in sorted(parameters.keys()):
        print("%s: %r" % (param_name, gs_clf.best_params_[param_name]))

def train_data(train_data_text, train_data_target, test_data_text, test_data_target):
    print("train_data")
    text_clf = Pipeline([('vect', CountVectorizer(analyzer='word')),
                     ('tfidf', TfidfTransformer()),
                     ('clf', SGDClassifier(loss='modified_huber', penalty='l2', alpha=1e-3, random_state=1, warm_start=True, n_jobs=-1))])
    
    text_clf.fit(train_data_text, train_data_target)
    
    predicted = text_clf.predict(test_data_text)
    
    print(np.mean(predicted == test_data_target))
    print(metrics.classification_report(test_data_target, predicted))   
    print(metrics.confusion_matrix(test_data_target, predicted))
    
    # grid_search(text_clf, train_data_text, train_data_target)

    return text_clf

def predict_and_validate(model, data):
    data_text = [x['review_text'] for x in data]
    #data_target = [x['target'] for x in data]
    
    #ratings = {1: [], 2: [], 3: [], 4: [], 5: []}
    predicted = model.predict(data_text)
    for i in range(0, len(data)):
        data[i]['predicted'] = predicted[i]

    target = [1 if x['rating'] > 3 else 0 for x in data]        
     
    print(np.mean(predicted == target))
    print(metrics.classification_report(target, predicted, target_names=['negative', 'positive']))   
    print(metrics.confusion_matrix(target, predicted))

if __name__ == '__main__':  
    training_data, unlabeled_data = read_data('sorted_data_acl')
    print("Total train data: ", len(training_data))
    print("Total unlabel data: ", len(unlabeled_data))
    train_data_text, train_data_target, test_data_text, test_data_target = split_data(training_data)
    model = train_data(train_data_text, train_data_target, test_data_text, test_data_target)
    predict_and_validate(model, unlabeled_data)
    
