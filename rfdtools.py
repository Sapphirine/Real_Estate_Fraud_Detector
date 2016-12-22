###############################################################################
#
# Columbia University EECS E6893 Big Data Analytics Fall 2016
# Nathaniel Jones (nj2315) Final Project
#
# Real Estate Fraud Detection Library for Python
# Dependencies: PySpark, numpy
#
###############################################################################


# Import PySpark Machine Learning Libraries
from pyspark.mllib.regression import LabeledPoint
from pyspark.mllib.tree import RandomForest
from pyspark.mllib.clustering import KMeans
from pyspark import SparkContext

# Import Handy Python Methods
import numpy
import datetime

# Line parsing function for non-numeric operations (like outliers)
def parse_line(line):
    output = []
    e = line.split(",")
    if len(e) >= 10:
        output.append(int(e[0])) # ID
        output.append(e[1]) # State
        output.append(e[2]) # Region
        output.append(e[3]) # Description
        output.append(pri(e[4])) # Price
        output.append(dat(e[5])) # Date
        output.append(brs(e[6])) # BR
        output.append(ft2(e[7])) # Sqft
        output.append(e[8]) # Neighborhood
        output.append(e[9]) # URL

    return output

# Line parsing function for numeric operations (like clustering)
def convertNumeric(e):
    output = []
    if len(e) >= 10:
        output.append(e[0]) # ID
        output.append(idf(e[1])) # State
        output.append(idf(e[2])) # Region
        output.append(idf(e[3])) # Description
        output.append(e[4]) # Price
        output.append(e[5]) # Date
        output.append(e[6]) # BR
        output.append(e[7]) # Sqft
        output.append(idf(e[8])) # Neighborhood
        output.append(idf(e[9])) # URL

    return output

# Returns whether a line is incomplete
# (rudimentary input sanitization)
def isValid(line):
    if len(line) >= 10:
        return True
    else:
        return False

# Placeholder function for quantizing texxt
# Next steps: replace with proper TF-IDF function
def idf(text):
    return len(text)

# Converts text in the form "$###" to an int
def pri(text):
    if text == "null":
        return -1
    else:
        return int(text[1:])

# Converts text in the form yyyy-mm-dd hh:mm:ss to a datetime ordinal (int)
def dat(text):
    e = text.split(" ")[0].split("-")
    return datetime.date(int(e[0]),int(e[1]),int(e[2])).toordinal()
    

# Converts text of the form "#br" to an int representing the number of bedrooms
def brs(text):
    if text == "null":
        return -1
    else:
        return int(text[0:-2])

# Converts text of the form "###ft2" to an int representing square feet
def ft2(text):
    if text == "null":
        return -1
    else:
        return int(text[0:-3])

# Takes a real entry and modifies it to look more fake
# Next Steps: adapt this to consider more info than just price
def make_fake(entry):
    newEntry = list(entry)
    newEntry[4] = newEntry[4]*numpy.random.uniform()
    return newEntry

# Returns the outliers of an apartment listing dataset
# directory: the directory containing the apartment listing dataset
# target: the parameter to consider when finding outliers
#         legal values are: "price", "date", "bedrooms", and "size"
# filteringFunction: function for limiting the dataset
#                    using e[n] to refer to the nth column of a data line
#                    example filterFunction = (lambda e: e[2] == "new york city")
def outliers(directory,target,filterFunction=isValid):

    # Validate target variable (must be numeric parameter)
    if target == "price":
        index = 4
    elif target == "date":
        index = 5
    elif target == "bedrooms":
        index = 6
    elif target == "size":
        index = 7
    else:
        raise ValueError("Only numeric fields can be examined as outliers")

    # Create a Spark context for this app
    sc = SparkContext(appName="RealEstateFraudDetector")

    # Load the CSV files and filter as specified by the user
    df = sc.textFile(directory).map(parse_line).filter(isValid).filter(lambda e: e[index] >= 0).filter(filterFunction)

    # Calculate statistics using MapReduce
    stats = df.map(lambda e: e[index]).stats()
    mean, stdev = stats.mean(), stats.stdev()
    count = stats.count()
    minP = stats.min()
    maxP = stats.max()

    # Output the statistics
    print("Mean " + str(mean) + ", stdDev " + str(stdev) + ", Count " + str(count) + ", Min " + str(minP) + ", Max " + str(maxP))

    # Find and return any outliers
    outliers = df.filter(lambda e: e[index] < (mean - 2 * stdev) or e[index] > (mean + 2 * stdev))
    return outliers

# Returns the smallest cluster of apartment listing data based on a numeric vectorization of listing parameters
# User can specify standard Spark K-Means clustering parameters
# directory: the source directory containing apartment listing CSV files
def clusters(directory, count=5, maxIterations=10, runs=1, initializationMode="random", filterFunction=isValid):

    # Create a Spark Context for this App
    sc = SparkContext(appName="RealEstateFraudDetector")

    # Load the CSV files
    df_text = sc.textFile(directory).map(parse_line).filter(isValid).filter(filterFunction)
    df = df_text.map(convertNumeric)

    # Perform K-Means clustering
    cluster_model = KMeans.train(df, 5, maxIterations=10, runs=1, initializationMode="random")

    # Gather and print the cluster sizes for viewing by user
    clusters = df.map(lambda e: e + [cluster_model.predict(e)])
    sizes = clusters.map(lambda e: e[-1]).countByValue()
    print(sizes)

    # Find the smallest cluster
    minimum = float('inf')
    anomaly = -1
    for key in sizes:
        if sizes[key] < minimum:
            minimum = sizes[key]
            anomaly = key

    anomalyIDs = df.filter(lambda e: e[-1]==anomaly).map(lambda e: e[0]).collect()

    # Return the cluster results
    return df_text.filter(lambda e: e[0] in anomalyIDs)

# Trains a Random Forest to identify possible fraudulent listings
def train_forest(model, falsifier=make_fake):
    def run(df, *args, **kwargs):
        fake = df.map(falsifier)
        labeled = df.map(lambda e: LabeledPoint(1, e)).union(fake.map(lambda e: LabeledPoint(0, e)))
        return model(labeled, *args, **kwargs)
    return run

# Creates and trains an unsupervised random forest
# Returns an RDD containing listings that tested positive for fraud indicators
def random_forest(directory, fraction=0.7, numTrees=10, maxDepth=15, maxBins=50, filterFunction=isValid, falsifier=make_fake):

    # Create a Spark Context for this App
    sc = SparkContext(appName="RealEstateFraudDetector")

    # Load the CSV files
    df_text = sc.textFile(directory).map(parse_line).filter(isValid).filter(filterFunction)
    (df_train, df_test) = df_text.map(convertNumeric).randomSplit([0.7,0.3])

    # Create and train the random forest model
    unsupervised = train_forest(RandomForest.trainClassifier, falsifier=falsifier)
    rf_model = unsupervised(df_train, numClasses=2, categoricalFeaturesInfo={}, numTrees=numTrees, featureSubsetStrategy="auto", impurity='gini', maxDepth=maxDepth, maxBins=maxBins)

    # Run the random forest model on the provided data
    predictions = rf_model.predict(df_test)
    results = df_test.zip(predictions)
    anomalyIDs = results.filter(lambda (k,v): v>0.5).map(lambda (k,v): k[0]).collect()
    return df_text.filter(lambda e: e[0] in anomalyIDs)




