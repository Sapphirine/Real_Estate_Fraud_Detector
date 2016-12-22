import rfdtools

items = rfdtools.outliers(directory="./craigslist", target="price", filterFunction=(lambda e: e[2] == "new york city"))

results = items.take(5)
print(results)

#clusters = rfdtools.clusters(directory="./craigslist", filterFunction=(lambda e: e[2] == "new york city"))

#print(clusters.take(5))

#results = rfdtools.create_forest(directory="./craigslist", filterFunction=(lambda e: e[2] == "new york city"))

#print(results.take(5))
