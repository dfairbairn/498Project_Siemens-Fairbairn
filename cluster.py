from sklearn.cluster import KMeans
from sklearn.metrics.cluster import silhouette_score
import numpy as np
import pandas as pd

def try_kmeans(fnamecsv,n_clusters=8):
    """ 
    Attempts a kmeans clustering on a dataset in a file, returning the kmeans object
    """
    from sklearn.cluster import KMeans
    import numpy as np
    df = pd.read_csv(fnamecsv)
    #TODO check for successful read
    variables = (df.as_matrix())[:,1:] #exclude first column which is pandas indices
    # for j in columns of variables
    #   modify each entry by subtracting mean of this column, dividing by stdev of this column
    # Could be using pandas' built-in means and standard deviation functions if I think of a nice way to do this for each column
    for j in range(len(variables[0,:])): #ugly way of looping over columns
        variables[:,j] = ( variables[:,j] - np.mean(variables[:,j]))/np.std(variables[:,j])
    
    # now each row of variables can be used for euclidean distance in kmeans
    k = KMeans(n_clusters=n_clusters, n_init=30,n_jobs=3).fit(variables)
    print "Labels: ",k.labels_
    print "Cluster centers: ",k.cluster_centers_
    return k

def cluster_study(n=50):
    """ Check out some basic cluster metrics for different cluster sizes. """

    fnamecsv = './AL_pchange_vars.csv'
    df = pd.read_csv(fnamecsv)
    variables = (df.as_matrix())[:,1:]
    for j in range(len(variables[0,:])): #ugly way of looping over columns
        variables[:,j] = ( variables[:,j] - np.mean(variables[:,j]))/np.std(variables[:,j])

    scores = []
    for i in (2+np.array(range(n))):
        k = KMeans(n_clusters=i, n_init=50, n_jobs=3).fit(variables)
        y = silhouette_score(variables,k.labels_)
        scores.append( (i, y) )
    
    with open('cluster_vs_silhouette.txt','w') as f:
        for s in scores:
            f.write(str(s[0]) + "\t" + str(s[1]) + "\n")
    print scores   

    scores = []
    for i in (2+np.array(range(n))):
        k = KMeans(n_clusters=i, n_init=50, n_jobs=3).fit(variables)
        #y = silhouette_score(variables,k.labels_)
        y = calinski_harabaz_score(variables,k.labels_)
        scores.append( (i, y) )

    with open('cluster_vs_calharabaz.txt','w') as f:
        for s in scores:
            f.write(str(s[0]) + "\t" + str(s[1]) + "\n")
   

if __name__=="__main__":
    #X = np.array([[30, 50, 80,20], [40, 70, 50, 23], [1, 0 ,2, 4], [5,8,8,0]])
    #kmeans = KMeans(n_clusters=2, random_state=0).fit(X)

    #k = try_kmeans('./AL_pchange_vars.csv',n_clusters=2)

    fnamecsv = './AL_pchange_vars.csv'
    df = pd.read_csv(fnamecsv)
    variables = (df.as_matrix())[:,1:]
    for j in range(len(variables[0,:])): #ugly way of looping over columns
        variables[:,j] = ( variables[:,j] - np.mean(variables[:,j]))/np.std(variables[:,j])

    from sklearn.metrics.cluster import calinski_harabaz_score
    k = KMeans(n_clusters=3, n_init=100, n_jobs=3).fit(variables)
     
    for l in k.labels_:
        print "Cluster centroid: ",l
