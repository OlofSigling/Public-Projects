import pandas as pd
from sklearn.tree import DecisionTreeClassifier 
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import category_encoders as ce
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from feature_importance import FeatureImportance
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier
from xgboost import cv
influenza_file_path = 'Influenza_NY.csv'
NYC_data = pd.read_csv(influenza_file_path, index_col=[0])

#Dropping columns with missing values, columns with uninterpretable meanings and columns not useful for predicting future influenza outbreaks (time-related)
dropped_columns = [#'Year', 'Season',
                    'Week Ending Date', 'County_Served_hospital', 'Service_hospital']
dropped_data = NYC_data.dropna().drop(columns=dropped_columns)
#Dropping influenza unspecified 
dropped_data = dropped_data[dropped_data.Disease != "INFLUENZA_UNSPECIFIED"]

X = dropped_data.drop(columns='Disease')
y = dropped_data.Disease

trainX, testX, trainy, testy = train_test_split(X, y, test_size=0.8)

cat_columns = ['Region',
                'Year', 'Season']

categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder())])

encoder= ce.BinaryEncoder(return_df=True)
hicardinal_transformer = Pipeline(steps=[('binary', encoder)])

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', categorical_transformer, cat_columns),
        ('cat2', hicardinal_transformer, 'County'), 
    ], remainder='passthrough')

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
            
          else:
            names = list(transformer.get_feature_names())
          
        except AttributeError as error:
          names = raw_col_name
        
        #print(names)    
        
        col_name.extend(names)
            
    return col_name

XGBparams = {'objective':'binary:logistic', 'n_estimators':200, 'n_jobs':6, 'verbosity':1, 'max_depth':6, 'min_child_weight':1} 
NYC_model = XGBClassifier(XGBparams)
NYC_pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', NYC_model)])
#NYC_pipeline.fit(trainX, trainy)
#feature names of pipeline: NYC_pipeline.feature_names_in_

# Cross_val with Scikit learn 
#scores = cross_val_score(NYC_pipeline, trainX, trainy)
#print("Average score: ", scores.mean())
#predictions = NYC_pipeline.predict(testX)
#print("Accuracy: ", accuracy_score(testy, predictions))

#Crossvall with XGBoost
cvparams = {"objective":"binary:logistic",'colsample_bytree': 0.3,'learning_rate': 0.1,
                'max_depth': 5, 'alpha': 10}

xgb_cv = cv(dtrain=data_dmatrix, params=params, nfold=3,
                    num_boost_round=50, early_stopping_rounds=10, metrics="auc", as_pandas=True, seed=123)

#new_column_names = (get_column_names_from_ColumnTransformer(preprocessor))
#print(new_column_names)



# nyc_model = DecisionTreeRegressor()
# nyc_model.fit(trainX, trainy)
# nyc_predictions = nyc_model.predict(testX)
# print(mean_absolute_error(testy, nyc_predictions))


# Empty columns: ['Beds_adult_facility_care', 'Beds_hospital', 'County_Served_hospital',
#        'Service_hospital', 'Discharges_Other_Hospital_intervention',
#        'Discharges_Respiratory_system_interventions',
#        'Total_Charge_Other_Hospital_intervention',
#        'Total_Charge_Respiratory_system_interventions']

# Beds_adult_facility_care                          1920
# Beds_hospital                                      960
# County_Served_hospital                             960
# Service_hospital                                   960
# Discharges_Other_Hospital_intervention           13650
# Discharges_Respiratory_system_interventions      13650
# Total_Charge_Other_Hospital_intervention         13650
# Total_Charge_Respiratory_system_interventions    13650

