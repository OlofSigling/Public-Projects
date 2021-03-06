#This is a python machine learning model trained to predict whether a case of influenza is influenza A or B based on data from the state of New York. 
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier 
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error
import category_encoders as ce
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from feature_importance import FeatureImportance
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score
from xgboost.sklearn import XGBClassifier
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hpsklearn import HyperoptEstimator

influenza_file_path = 'Influenza Model/Influenza_NY.csv'
NY_data = pd.read_csv(influenza_file_path, index_col=[0])

#Dropping columns with missing values, columns with uninterpretable meanings and columns not useful for predicting future influenza outbreaks (time-related).   
dropped_columns = ['Year', 'Season',
                    'Week Ending Date', 'County_Served_hospital', 'Service_hospital']
dropped_data = NY_data.dropna().drop(columns=dropped_columns)
#Dropping cases where type of influenza was unspecified. 
dropped_data = dropped_data[dropped_data.Disease != "INFLUENZA_UNSPECIFIED"]

X = dropped_data.drop(columns='Disease')
y = dropped_data.Disease

#Replacing influenza A and B with values of 0 and 1 respectively to fit with deprecated XGBClassifier encoder. 
y.replace(to_replace="INFLUENZA_A", value=0, inplace=True) 
y.replace(to_replace="INFLUENZA_B", value=1, inplace=True)

trainX, testX, trainy, testy = train_test_split(X, y, test_size=0.8)


cat_columns = ['Region'
                #,'Year', 'Season'
                ]

categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder())])

encoder= ce.BinaryEncoder(return_df=True)
hicardinal_transformer = Pipeline(steps=[('binary', encoder)])

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', categorical_transformer, cat_columns),
        ('cat2', hicardinal_transformer, 'County'), 
    ], remainder='passthrough')

trainX, testX = preprocessor.fit_transform(trainX), preprocessor.fit_transform(testX)

#Get column names from a ColumnTransformer, with print functions commented out to return only a list
def get_column_names_from_ColumnTransformer(column_transformer):    
    col_name = []
    for transformer_in_columns in column_transformer.transformers_[:-2]: #the last transformer is ColumnTransformer's 'remainder'
        #print('\n\ntransformer: ', transformer_in_columns[0])
        
        raw_col_name = list(transformer_in_columns[2])
        
        if isinstance(transformer_in_columns[1], Pipeline): 
            # if pipeline, get the last transformer
            transformer = transformer_in_columns[1].steps[-1][1]
        else:
            transformer = transformer_in_columns[1]
            
        try:
          if isinstance(transformer, OneHotEncoder):
            names = list(transformer.get_feature_names_out(raw_col_name))
            
          elif isinstance(transformer, SimpleImputer) and transformer.add_indicator:
            missing_indicator_indices = transformer.indicator_.features_
            missing_indicators = [raw_col_name[idx] + '_missing_flag' for idx in missing_indicator_indices]

            names = raw_col_name + missing_indicators
          elif isinstance(transformer, ce.BinaryEncoder):
            names = list(transformer.get_feature_names_out(raw_col_name))

          else:
            names = list(transformer.get_feature_names())
          
        except AttributeError as error:
          names = raw_col_name
        
        #print(names)    
        
        col_name.extend(names)
            
    return col_name

#Printing new column names to ensure OneHotEncoder transformation was done correctly
new_column_names = (get_column_names_from_ColumnTransformer(preprocessor))
print(new_column_names)

#Objective function to find the best hyperparameters using Bayesian Optimization through Hyperopt
def objective_function(params):
    clf = XGBClassifier(**params)
    score = cross_val_score(clf, trainX, trainy, cv=5).mean()
    return {'loss': -score, 'status': STATUS_OK} 
#Hyperspace to search through for optimal hyperparameters.     
hyperspace={'max_depth': hp.choice('max_depth', np.arange(1, 14, dtype=int)),
        'gamma': hp.uniform ('gamma', 1,9),
        'reg_alpha' : hp.quniform('reg_alpha', 40,180,1),
        'reg_lambda' : hp.uniform('reg_lambda', 0,1),
        'colsample_bytree' : hp.uniform('colsample_bytree', 0.5,1),
        'min_child_weight' : hp.quniform('min_child_weight', 0, 10, 1),
        'learning_rate': hp.loguniform('learning_rate', np.log(0.01), np.log(1)),
        'max_leaves': hp.choice('max_leaves', np.arange(5, 50, dtype=int)),
        'n_estimators': hp.choice('n_estimators', np.arange(50, 500, dtype=int)),
        'seed': 0
    }
#Full hyperopt coding block to find the best hyperparameters. Shown to demonstrate how they were found, actual results have been 
#used in the XGB_model itself further on.  
""" tpe_algorithm = tpe.suggest
trials = Trials()
num_eval = 500
best_param = fmin(objective_function, hyperspace, algo=tpe.suggest, max_evals=num_eval, trials=trials, rstate= np.random.default_rng(1))
print(best_param)
 """

XGBparams = {'min_child_weight': 6.0, 'learning_rate': 0.14512379125105682, 'max_leaves':37, 'reg_alpha': 47.0, 'reg_lambda':0.6012254336995094, 
            'n_estimators':326, 'objective':'binary:logistic', 'n_jobs':6, 'verbosity':1, 'gamma': 1.1398031295664848, 
            'max_depth':5, 'colsample_bytree': 0.6338411499347879, 'use_label_encoder':False} 
xgb_model = XGBClassifier(**XGBparams)

#crossvalidating paremeters for scores
scores = cross_val_score(xgb_model, trainX, trainy, cv=5, scoring='accuracy')
print(scores)

#training and predicting
xgb_model.fit(trainX, trainy)
predictions = xgb_model.predict(testX)
accuracy = accuracy_score(testy, predictions)
print(accuracy)

