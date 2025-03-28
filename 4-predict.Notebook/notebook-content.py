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

# # Part 4: Score the trained model


# MARKDOWN ********************

# 
# Microsoft Fabric allows you to operationalize machine learning models with a scalable function called PREDICT, which supports batch scoring in any compute engine. You can generate batch predictions directly from a Microsoft Fabric notebook or from a given model's item page. Learn about [PREDICT](https://aka.ms/fabric-predict).  
# 
# To generate batch predictions on our test dataset, you'll use version 1 of the trained churn model. You'll load the test dataset into a spark DataFrame and create an MLFlowTransformer object to generate batch predictions. You can then invoke the PREDICT function using one of following three ways: 
# 
# - Using the Transformer API from SynapseML
# - Using the Spark SQL API
# - Using PySpark user-defined function (UDF)
# 
# ## Prerequisites
# 
# - Complete [Part 3: Train and register machine learning models](https://learn.microsoft.com/fabric/data-science/tutorial-data-science-train-models).
# - Attach the same lakehouse you used in Part 3 to this notebook.

# MARKDOWN ********************

# ## Load the test data
# 
# Load the test data that you saved in Part 3.

# CELL ********************

df_test = spark.read.format("delta").load("Tables/df_test")
display(df_test)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### PREDICT with the Transformer API
# 
# To use the Transformer API from SynapseML, you'll need to first create an MLFlowTransformer object.
# 
# ### Instantiate MLFlowTransformer object
# 
# The MLFlowTransformer object is a wrapper around the MLFlow model that you registered in Part 3. It allows you to generate batch predictions on a given DataFrame. To instantiate the MLFlowTransformer object, you'll need to provide the following parameters:
# 
# - The columns from the test DataFrame that you need as input to the model (in this case, you would need all of them).
# - A name for the new output column (in this case, predictions).
# - The correct model name and model version to generate the predictions (in this case, `lgbm_sm` and version 1).

# CELL ********************

from synapse.ml.predict import MLFlowTransformer

model = MLFlowTransformer(
    inputCols=list(df_test.columns),
    outputCol='predictions',
    modelName='lgbm2_sm',
    modelVersion=1
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pandas

predictions = model.transform(df_test)
display(predictions)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Pour inclure les résultats de l'autoML dans le code : 

# CELL ********************

# Load test data  
df_test = spark.read.format("delta").load("Tables/df_test")  

# Specify the columns to be used as input to the model and the output column name  
input_columns = list(df_test.columns)  # Assuming all columns are used as input  
output_column = "predictions"  
  
# Instantiate MLFlowTransformer object  
mlflow_transformer = MLFlowTransformer(  
    inputCols=input_columns,  
    outputCol=output_column,  
    modelName="AutoML_FLAML_Model",  
    modelVersion=2  
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

predictions = mlflow_transformer.transform(df_test)
display(predictions)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Now that you have the MLFlowTransformer object, you can use it to generate batch predictions.

# MARKDOWN ********************

# ### PREDICT with the Spark SQL API

# CELL ********************

from pyspark.ml.feature import SQLTransformer 

# Substitute "model_name", "model_version", and "features" below with values for your own model name, model version, and feature columns
model_name = 'lgbm_sm'
model_version = 1
features = df_test.columns

sqlt = SQLTransformer().setStatement( 
    f"SELECT PREDICT('{model_name}/{model_version}', {','.join(features)}) as predictions FROM __THIS__")

# Substitute "X_test" below with your own test dataset
display(sqlt.transform(df_test))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### PREDICT with a user-defined function (UDF)

# CELL ********************

from pyspark.sql.functions import col, pandas_udf, udf, lit

# Substitute "model" and "features" below with values for your own model name and feature columns
my_udf = model.to_udf()
features = df_test.columns

display(df_test.withColumn("predictions", my_udf(*[col(f) for f in features])))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Write model prediction results to the lakehouse
# 
# Once you have generated batch predictions, write the model prediction results back to the lakehouse.  

# CELL ********************

# Save predictions to lakehouse to be used for generating a Power BI report
table_name = "customer_churn_test_predictions"
predictions.write.format('delta').mode("overwrite").save(f"Tables/{table_name}")
print(f"Spark DataFrame saved to delta table: {table_name}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Next step
# 
# Use these predictions you just saved to [create a report in Power BI](https://learn.microsoft.com/fabric/data-science/tutorial-data-science-create-report).

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
