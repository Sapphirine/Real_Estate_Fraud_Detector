Real Estate Fraud Detection Toolbox
 
Nathaniel Jones
Electrical Engineering
Columbia University
nj2315@columbia.edu

 
Abstract— This toolbox provides an interface for applying the Apache Spark machine learning library to detection of rental fraud through analysis of online listing data. Interfaces are provided for calculation of univariate statistical outliers, K-Means clustering, and the Random Forest algorithm.

Real Estate, Python, K-Means, Clustering, Random Forest, Apache Spark, Machine Learning, Prediction, Classification
I.	INTRODUCTION 
Internet rental scams have become a common problem as online listing sites have become more popular. This problem is particularly prevalent in high-demand markets such as New York City. The anonymous nature of online listings makes detection and tracking of fraudulent posts difficult. Due to the large number of online listings, searching for fraudulent posts manually is time and cost prohibitive. Machine learning algorithms are an ideal solution for this problem, allowing fast, automated detection of anomalies. This toolbox aims to provide a simple interface for applying anomaly detection algorithms to online listings. Its intended market is online listing sites who wish to detect and examine anomalous listings to increase the reliability, and thereby the reputation of their service.
II.	RELATED WORKS
Machine learning algorithms are frequently used for anomaly detection, most notably in security applications, such as anti-malware solutions, insider threat detection, and financial fraud detection. Some applications use anomaly detection methods similar to those in this toolbox, while others use reasoning structures, such as Bayesian Networks. Notable examples of these include Neo4j and IBM System G. The approaches used in this toolbox are based on the unsupervised anomaly detection algorithms presented in chapter 8 of Jim Scott’s Getting Started with Apache Spark. In short, the algorithms used are well understood, but to my knowledge they have not previously been applied to real estate fraud in the open source world.
III.	SYSTEM OVERVIEW
The Real Estate Fraud Detection Toolbox contains three main parts: univariate outlier calculation, K-Means clustering, and an unsupervised Random Forest model. The toolbox is structured as a Python library that can be imported for access to a simple interface to those algorithms. The library contains built-in functions for parsing listing data as scraped by the included Craigslist web-scraper. (Note: the web-scraper is included as a formatting example and was used in gathering test data for the toolbox. Do not use it to gather more data, or Craigslist may ban your IP address.) The web-scraper uses the Python requests library and BeautifulSoup for retrieving and parsing HTML. The dataset used for testing is a 1GB set of comma-separated value files containing web-scraped Craigslist listings from between 12/01/2016 to 12/20/2016 represented by 10 columns: uniqueID, state, region, title, price, date, bedrooms, size, neighborhood, and URL. Of these fields, price, date, bedrooms, and size are numeric and can be used to calculate univariate outliers. The remaining arguments are strings and need to be converted into numeric vectors for use in K-Means clustering and Random Forests. The library rfdtools.py contains two built-in methods for parsing the CSV files: one converts string fields into numbers (the length of the string field) for use in clustering and random forests. The other keeps string fields intact for convenience of identifying outliers in the univariate outliers method. 
IV.	ALGORITHM
The Real Estate Fraud Detection Toolbox makes use of three algorithms provided in Apache Spark. First, it takes advantage of statistics calculated over a large, distributed dataset via MapReduce. A MapReduce job calculates the univariate mean and standard deviation of the dataset, allowing the RFDTools library to filter the dataset into a set of outliers. These outliers are intended to be reviewed by a human to find any errored or potentially fraudulent listings. The second algorithm used in the library is K-Means Clustering. RFDTools calls Spark’s k-means clustering methods through PySpark, allowing computation of clusters within the apartment listing data. Small clusters are likely to contain outliers. The user may have to try various clustering parameters before finding an appropriate configuration for the sub-set of data being analyzed. The third algorithm used by the toolbox is Spark’s Random Forest algorithm implementation, with a slight modification. In Getting Started with Apache Spark, Jim Scott proposes that the Random Forest algorithm can be trained using purposely errored data, modified to match expected anomalies. In his case, Scott randomly selects values for each column in his training dataset from the real dataset, randomizing the relationships between columns to teach the Random Forest model how to discern when the elements of an entry have an anomalous relationship. The RFDTools library generates the training dataset by attempting to mimic the behavior of a fraudulent lister. For instance, a fraudulent apartment listing will likely have a lower price than is appropriate for the neighborhood, size, and amenities. Thus, RFDTools trains its Random Forest model on a modified subset of the original dataset, reducing all rents by a different random factor to mimic fraudulent listings.

V.	SOFTWARE PACKAGE DESCRIPTION
The RFDTools package contains two Python files. The first is apartmentScraper.py, a web-scraping tool for gathering listings from all regions of Craigslist. (Note: widely using this tool is not recommended, as Craigslist frowns upon web-scraping and may ban your IP address) The scraping tool can be modified to save data to a particular directory at a particular time, or filter by certain regions. In its base form, the tool waits for 4pm local time, then scrapes data from all regions of Craigslist, collects them in a CSV file named after the current date, then waits for 4pm local time the next day. As RFDTools is intended for use by listing sites, who would not need to web-scrape their own content, the web-scraping tool is not intended for further use and is not formatted as a Python library. In its current form, it is a script that can be run normally through Python, and may be referenced as a web-scraping example or for information on how the test data files are formatted.

The second Python file included is the actual RFDTools library, rfdtools.py. This library can be used in any Python program by standard Python import. The next section gives examples of library function usage.

VI.	EXPERIMENT RESULTS
Testing for each method of RFDTools was performed using 1GB of web-scraped Craigslist data. Each method was tested with sanity checks on the results. For instance, the outliers method was tested by calculating statistics and univariate outliers for apartments in New York City to check whether calculated statistics were reasonable and if any potentially fraudulent listings could be identified. Consider the following sample code for using the outliers function. The outliers function calculates the mean, standard deviation, minimum, and maximum prices among the apartment listings in NYC and returns any outliers in a Spark RDD.

import rfdtools
results = rfdtools.outliers(directory=“./craigslist”, target=“price”, filterFunction = (lambda e: e[2] == “new york city”)
results.take(5)
Valid values for target are limited to numeric fields: “price”, “date”, “bedrooms”, and “size”. The filterFunction can use any field of the data, indexed by column starting from 0. Remember that the library converts all numeric fields to integers for this function, including dates (converted to ordinal form using the Python datetime library). All other fields are left as strings, and must be treated as such by the filterFunction. The code above outputs a mean of $2614, standard deviation of $1033, minimum of $11, and maximum of $9000. All outliers can be collected in a list by using the collect() function of RDD objects, but the above code just looks at 5 of the outliers. Those five turn out to be:
•	A 2br in Greenwich for $11 a month
•	A 3br on the Upper East Side for $5065
•	A 3br in Gramercy for $4900
•	A 1br in the North Bronx for $200
•	An unspecified layout on the Upper East Side for $5495

Of these listings, at least 2 look like possible candidates for further examination. The $11 a month listing and the $200 a month listing could be errors at best or fraud at worst. Based on these results, the outliers method appears to be a good approach for simple anomaly detection in apartment listings.

The clustering function was likewise tested by clustering data from NYC listings to determine whether a set of clustering parameters could be found that would create a small cluster containing anomalous listings. The cluster function returns an RDD containing the smallest cluster produced by the K-Means clustering algorithm, and allows the user to specify Spark algorithm parameters.

import rfdtools
results = rfdtools.clusters(directory=“./craigslist”, count=5, maxIterations=10, runs=1, initializationMode=”random”, filterFunction = (lambda e: e[2] == “new york city”)
results.take(5)

The 5 results produced by this code were unexpectedly intriguing. Clustering in this particular case uncovered a completely different type of anomalous listing than the outliers function. Within the smallest cluster formed using these algorithm parameters, all the clustered listings are duplicates of one another. The clustering algorithm uncovered a rental company’s attempts to spam Craigslist with repeated posts of their own listings. While such behavior may not be strictly illegal, it may violate the terms of use for some listing sites, and the RFDTools clustering method could help rental listings sites find and take action against companies that post hundreds of duplicate listings. Such listings take up storage space and clog up listing searches, frustrating site users and hurting site’s reputation.
The Random Forest method was tested by running a trained Unsupervised Random Forest model against individual listings and examining flagged listings manually to determine whether the listings are indeed suspicious. This test is similar to those performed on the clustering method. It takes some of the PySpark random forest parameters users might want to tweak, as well as the option to specify a custom filtering function and falsification function. The falsification function is meant to take in real apartment listings and modify them in a manner consistent with the characteristics of fraudulent listings. RFDTools default falsifier reduces the rent by a random ratio. Since we do not know what listings are fraudulent ahead of time, we cannot evaluate this model the usual way. Parameters and the falsification function must be tweaked until the model is able to successfully pull out listings of interest to the user.

import rfdtools
results = rfdtools.random_forest(directory=“./craigslist”, fraction=0.7, numTrees=10, maxDepth=15, maxBins=50, filterFunction = (lambda e: e[2] == “new york city”, falsifier=rfdtools.make_fake)
results.take(5)

The 5 results produced by this code are as follows:
•	A 1br for $900 a month in Yonkers
•	A 1br for $2425 in the East Village
•	A studio for $2350 in Murray Hill
•	A 2br for $2500 near St Albans
•	A 3br for $585 in Queens with utilities included

Several of these listings are clearly in error or fraudulent upon visual inspection due to excessively low rents for the area or for the amenities listed. Some seem perfectly innocuous. These could indicate that the falsification function produces insufficiently detailed changes for the random forest to tell the difference between real and fraudulent listings, or maybe the random forest sees something we don’t at first glance. The output of the random forest classifier helps single out listings for further inspection by the user, allowing more subtly suspicious listings to be found and examined.

VII.	CONCLUSION
The development and testing of RFDTools shows that anomaly detection algorithms in Spark could be useful for detecting errored or fraudulent apartment listings. This functionality could benefit apartment listing sites, since they could more easily track down potentially fraudulent listings, increase the reliability of their listings, and thereby foster an improved reputation over their competitors.
ACKNOWLEDGMENT
THE AUTHORS WOULD LIKE TO THANK…
Dr. Ching-Yung Lin, Course Professor
Eric Johnson, Head TA
All the TAs of EECSE6893
Dr. Guangnan Ye
REFERENCES

[1]	Scott, Jim, Getting Started with Apache Spark,    https://www.mapr.com/ebooks/spark/
[2]	CodeFellows Python Documentation http://cewing.github.io/training.codefellows/index.html 
[3]	Craigslist Apartment Listings http://www.craigslist.org/about/sites 