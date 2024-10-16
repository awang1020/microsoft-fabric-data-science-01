# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "c3ab2d20-89ee-4554-a2d9-e879087149ac",
# META       "default_lakehouse_name": "Lakehouse_datascience_tuto",
# META       "default_lakehouse_workspace_id": "66a4106d-7c20-4aa8-920f-890f7fd0270e",
# META       "known_lakehouses": [
# META         {
# META           "id": "c3ab2d20-89ee-4554-a2d9-e879087149ac"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Part 3: Train and register a machine learning model
# 
# In this tutorial, you'll learn to train multiple machine learning models to select the best one in order to predict which bank customers are likely to leave.
# 
# Once a model is trained, you'll register the trained model, and log the used hyperaparameters as well as the evaluation metrics using Microsoft Fabric's native integration with the MLflow framework.
# 
# [MLflow](https://mlflow.org/docs/latest/index.html) is an open source platform for managing the machine learning lifecycle with features like Tracking, Models, and Model Registry. MLflow is natively integrated with the Fabric Data Science experience.
# 
# ## Prerequisites
# 
# - Complete [Part 2: Explore and clean data](https://learn.microsoft.com/fabric/data-science/tutorial-data-science-explore-notebook).
# - Attach the same lakehouse you used in Part 2 to this notebook.

# MARKDOWN ********************

# ## Install custom libraries
# 
# For this notebook, you'll install imbalanced-learn (imported as `imblearn`) using `%pip install`. Imbalanced-learn is a library for Synthetic Minority Oversampling Technique (SMOTE) which is used when dealing with imbalanced datasets. The PySpark kernel will be restarted after `%pip install`, so you'll need to install the library before you run any other cells. 
# 
# You'll access SMOTE using the `imblearn` library. Install it now using the in-line installation capabilities (e.g., `%pip`, `%conda`).
# 


# CELL ********************

# Install imblearn for SMOTE using pip
%pip install imblearn

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# > [!TIP]
# >
# > When you install a library in a notebook, it is only available for the duration of the notebook session and not in the workspace. If you restart the notebook, you'll need to install the library again. If you have a library you often use, you could instead [install it in your workspace](https://learn.microsoft.com/fabric/data-science/python-guide/python-library-management) to make it available to all notebooks in your workspace without further installs.


# MARKDOWN ********************

# 
# ## Load the data
# 
# Load the delta table from the lakehouse in order to read the cleaned data you created in the previous notebook.

# CELL ********************

import pandas as pd
SEED = 123
df_clean = spark.read.format("delta").load("Tables/df_clean").toPandas()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Generate experiment for tracking and logging the model using MLflow
# 
# This section demonstrates how to generate an experiment, specify model and training parameters as well as scoring metrics, train the models, log them, and save the trained models for later use.

# CELL ********************

import mlflow
# Setup experiment name
EXPERIMENT_NAME = "bank-churn-experiment"  # MLflow experiment name

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Extending the MLflow autologging capabilities, autologging works by automatically capturing the values of input parameters and output metrics of a machine learning model as it is being trained. This information is then logged to your workspace, where it can be accessed and visualized using the MLflow APIs or the corresponding experiment in your workspace. 
# 
# All the experiments with their respective names are logged and you'll be able to track their parameters and performance metrics. To learn more about  autologging, see  [Autologging in Microsoft Fabric](https://aka.ms/fabric-autologging).

# MARKDOWN ********************

# ### Set experiment and autologging specifications

# CELL ********************

mlflow.set_experiment(EXPERIMENT_NAME)
mlflow.autolog(exclusive=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Import scikit-learn and LightGBM
# 
# With your data in place, you can now define the machine learning models. You'll apply Random Forrest and LightGBM models in this notebook. Use `scikit-learn` and `lightgbm` to implement the models within a few lines of code. 

# CELL ********************

# Import the required libraries for model training
from sklearn.model_selection import train_test_split
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, confusion_matrix, recall_score, roc_auc_score, classification_report

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Prepare training, validation and test datasets
# 
# Use the `train_test_split` function from `scikit-learn` to split the data into training and test sets.

# CELL ********************

y = df_clean["Exited"]
X = df_clean.drop("Exited",axis=1)
# Split the dataset to 60%, 20%, 20% for training, validation, and test datasets
# Train-Test Separation
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=SEED)
# Train-Validation Separation
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=SEED)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Save test data to a delta table
# 
# Save the test data to the delta table for use in the next notebook.

# CELL ********************

table_name = "df_test"
# Create PySpark DataFrame from Pandas
df_test=spark.createDataFrame(X_test)
df_test.write.mode("overwrite").format("delta").save(f"Tables/{table_name}")
print(f"Spark test DataFrame saved to delta table: {table_name}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# 
# ### Apply SMOTE to the training data to synthesize new samples for the minority class
# ##### pas exécuter pour automl
# The data exploration in part 2 showed that out of the 10,000 data points corresponding to 10,000 customers, only 2,037 customers (around 20%) have left the bank. This indicates that the dataset is highly imbalanced. The problem with imbalanced classification is that there are too few examples of the minority class for a model to effectively learn the decision boundary. SMOTE is the most widely used approach to synthesize new samples for the minority class. Learn more about SMOTE [here](https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.SMOTE.html#) and [here](https://imbalanced-learn.org/stable/over_sampling.html#smote-adasyn).
# 
# > [!TIP]
# >
# > Note that SMOTE should only be applied to the training dataset. You must leave the test dataset in its original imbalanced distribution in order to get a valid approximation of how the machine learning model will perform on the original data, which is representing the situation in production.

# CELL ********************

from collections import Counter
from imblearn.over_sampling import SMOTE

sm = SMOTE(random_state=SEED)
X_res, y_res = sm.fit_resample(X_train, y_train)
new_train = pd.concat([X_res, y_res], axis=1)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Model Training

# MARKDOWN ********************

# * Train the model using Random Forest with maximum depth of 4 and 4 features

# CELL ********************

mlflow.sklearn.autolog(registered_model_name='rfc3_sm') # Register the trained model with autologging
rfc3_sm = RandomForestClassifier(max_depth=4, max_features=4, min_samples_split=3, random_state=1) # Pass hyperparameters
with mlflow.start_run(run_name="rfc3_sm") as run:
    rfc3_sm_run_id = run.info.run_id # Capture run_id for model prediction later
    print("run_id: {}; status: {}".format(rfc3_sm_run_id, run.info.status))
    # rfc1.fit(X_train,y_train) # Imbalanaced training data
    rfc3_sm.fit(X_res, y_res.ravel()) # Balanced training data
    rfc3_sm.score(X_val, y_val)
    y_pred = rfc3_sm.predict(X_val)
    cr_rfc3_sm = classification_report(y_val, y_pred)
    cm_rfc3_sm = confusion_matrix(y_val, y_pred)
    roc_auc_rfc3_sm = roc_auc_score(y_res, rfc3_sm.predict_proba(X_res)[:, 1])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# * Train the model using Random Forest with maximum depth of 8 and 6 features

# CELL ********************

mlflow.sklearn.autolog(registered_model_name='rfc4_sm') # Register the trained model with autologging
rfc4_sm = RandomForestClassifier(max_depth=10, max_features=8, min_samples_split=3, random_state=1) # Pass hyperparameters
with mlflow.start_run(run_name="rfc4_sm") as run:
    rfc4_sm_run_id = run.info.run_id # Capture run_id for model prediction later
    print("run_id: {}; status: {}".format(rfc4_sm_run_id, run.info.status))
    # rfc2.fit(X_train,y_train) # Imbalanced training data
    rfc4_sm.fit(X_res, y_res.ravel()) # Balanced training data
    rfc4_sm.score(X_val, y_val)
    y_pred = rfc4_sm.predict(X_val)
    cr_rfc4_sm = classification_report(y_val, y_pred)
    cm_rfc4_sm = confusion_matrix(y_val, y_pred)
    roc_auc_rfc4_sm = roc_auc_score(y_res, rfc4_sm.predict_proba(X_res)[:, 1])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# * Train the model using LightGBM

# CELL ********************

# lgbm_model
mlflow.lightgbm.autolog(registered_model_name='lgbm2_sm') # Register the trained model with autologging
lgbm2_sm_model = LGBMClassifier(learning_rate = 0.08, 
                        max_delta_step = 4, 
                        n_estimators = 100,
                        max_depth = 10, 
                        eval_metric = "logloss", 
                        objective='binary', 
                        random_state=SEED)

with mlflow.start_run(run_name="lgbm2_sm") as run:
    lgbm1_sm_run_id = run.info.run_id # Capture run_id for model prediction later
    # lgbm2_sm_model.fit(X_train,y_train) # Imbalanced training data
    lgbm2_sm_model.fit(X_res, y_res.ravel()) # Balanced training data
    y_pred = lgbm2_sm_model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    cr_lgbm2_sm = classification_report(y_val, y_pred)
    cm_lgbm2_sm = confusion_matrix(y_val, y_pred)
    roc_auc_lgbm2_sm = roc_auc_score(y_res, lgbm2_sm_model.predict_proba(X_res)[:, 1])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## AutoML enablement

# CELL ********************

%pip install flaml

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import mlflow
from flaml import AutoML
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score, f1_score, log_loss, precision_score, recall_score
from mlflow.models.signature import infer_signature

# Initialize AutoML
automl = AutoML()

with mlflow.start_run(run_name="AutoML_3") as run:
    automl_run_id = run.info.run_id
    print("run_id: {}; status: {}".format(automl_run_id, run.info.status))

    # Configure and run AutoML
    automl_settings = {
        "time_budget": 60,  # Time budget in seconds
        "metric": 'roc_auc',  # Metric to optimize
        "task": 'classification',  # Task type
        "log_file_name": 'automl.log',  # Log file
        "seed": 2,  # Seed for reproducibility
    }

    automl.fit(X_train, y_train, **automl_settings)

    # Make predictions
    y_pred = automl.predict(X_val)
    y_prob = automl.predict_proba(X_val)

    # Infer the model signature  
    signature = infer_signature(X_train, y_pred)  
    
    # Evaluate the AutoML model
    metrics = {  
        "val_score": automl.score(X_val, y_val),  
        "accuracy": accuracy_score(y_val, y_pred),  
        "f1_score": f1_score(y_val, y_pred, average='weighted'),  
        "log_loss": log_loss(y_val, y_prob),  
        "precision": precision_score(y_val, y_pred, average='weighted'),  
        "recall": recall_score(y_val, y_pred, average='weighted'),  
        "roc_auc": roc_auc_score(y_val, y_prob[:, 1])  
    }

    # Generate classification report and confusion matrix
    cr_automl = classification_report(y_val, y_pred)
    cm_automl = confusion_matrix(y_val, y_pred)

    # Log metrics and parameters  
    mlflow.log_metrics(metrics)  
    mlflow.log_params(automl.best_config)  

    # Log and register the model with a signature  
    mlflow.sklearn.log_model(automl.model, "model", signature=signature)  
    model_uri = f"runs:/{automl_run_id}/model"  
    model_details = mlflow.register_model(model_uri=model_uri, name="AutoML_FLAML_Model")  
    model_version = model_details.version  
mlflow.end_run()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Experiments artifact for tracking model performance
# 
# The experiment runs are automatically saved in the experiment artifact that can be found from the workspace. They're named based on the name used for setting the experiment. All of the trained models, their runs, performance metrics and model parameters are logged. 
# 
# To view your experiments:
# 1. On the left panel, select your workspace.
# 1. Find and select the experiment name, in this case _bank-churn-experiment_. If you don't see the experiment in your workspace, refresh your browser.
# 
# <img src="https://sdkstorerta.blob.core.windows.net/churnblob/experiment_runs.png"  width="400%" height="100%" title="Screenshot shows logged values for one of the models.">

# MARKDOWN ********************

# #### Assess the performances of the trained models on the validation dataset
# 
# Once done with machine learning model training, you can assess the performance of trained models in two ways.
# 
# - Open the saved experiment from the workspace, load the machine learning models, and then assess the performance of the loaded models on the validation dataset.

# CELL ********************

# Define run_uri to fetch the model
# mlflow client: mlflow.model.url, list model
load_model_rfc3_sm = mlflow.sklearn.load_model(f"runs:/{rfc3_sm_run_id}/model")
load_model_rfc4_sm = mlflow.sklearn.load_model(f"runs:/{rfc4_sm_run_id}/model")
load_model_lgbm1_sm = mlflow.lightgbm.load_model(f"runs:/{lgbm1_sm_run_id}/model")
# Assess the performance of the loaded model on validation dataset
ypred_rfc3_sm_v1 = load_model_rfc3_sm.predict(X_val) # Random Forest with max depth of 4 and 4 features
ypred_rfc4_sm_v1 = load_model_rfc4_sm.predict(X_val) # Random Forest with max depth of 8 and 6 features
ypred_lgbm1_sm_v1 = load_model_lgbm1_sm.predict(X_val) # LightGBM

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# - Directly assess the performance of the trained machine learning models on the validation dataset.

# CELL ********************

ypred_rfc3_sm_v2 = rfc3_sm.predict(X_val) # Random Forest with max depth of 4 and 4 features
ypred_rfc4_sm_v2 = rfc4_sm.predict(X_val) # Random Forest with max depth of 8 and 6 features
ypred_lgbm1_sm_v2 = lgbm2_sm_model.predict(X_val) # LightGBM

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Depending on user's preference, either approach is fine and should offer identical performances. In this notebook, you'll choose the first approach in order to better demonstrate the MLflow autologging capabilities in Microsoft Fabric.

# MARKDOWN ********************

#  #### Show True/False Positives/Negatives using the Confusion Matrix

# MARKDOWN ********************

# Next, you'll develop a script to plot the confusion matrix in order to evaluate the accuracy of the classification using the validation dataset. The confusion matrix can be plotted using SynapseML tools as well, which is shown in Fraud Detection sample that is available [here](https://aka.ms/samples/frauddectection).

# CELL ********************

import seaborn as sns
sns.set_theme(style="whitegrid", palette="tab10", rc = {'figure.figsize':(9,6)})
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import rc, rcParams
import numpy as np
import itertools

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    print(cm)
    plt.figure(figsize=(4,4))
    plt.rcParams.update({'font.size': 10})
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45, color="blue")
    plt.yticks(tick_marks, classes, color="blue")

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="red" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# * Confusion Matrix for Random Forest Classifier with maximum depth of 4 and 4 features

# CELL ********************

cfm = confusion_matrix(y_val, y_pred=ypred_rfc3_sm_v1)
plot_confusion_matrix(cfm, classes=['Non Churn','Churn'],
                      title='Random Forest with max depth of 4')
tn, fp, fn, tp = cfm.ravel()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# * Confusion Matrix for Random Forest Classifier with maximum depth of 8 and 6 features

# CELL ********************

cfm = confusion_matrix(y_val, y_pred=ypred_rfc4_sm_v1)
plot_confusion_matrix(cfm, classes=['Non Churn','Churn'],
                      title='Random Forest with max depth of 8')
tn, fp, fn, tp = cfm.ravel()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# * Confusion Matrix for LightGBM

# CELL ********************

cfm = confusion_matrix(y_val, y_pred=ypred_lgbm1_sm_v1)
plot_confusion_matrix(cfm, classes=['Non Churn','Churn'],
                      title='LightGBM')
tn, fp, fn, tp = cfm.ravel()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Next step
# 
# Continue on to [Part 4: Perform batch scoring and save predictions to a lakehouse](https://learn.microsoft.com/fabric/data-science/tutorial-data-science-batch-scoring).