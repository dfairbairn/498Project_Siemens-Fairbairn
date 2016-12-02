from sklearn.cluster import KMeans
import numpy as np
import pandas as pd

def try_kmeans(fnamecsv):
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
    k = KMeans(n_clusters=8, n_init=30,n_jobs=3).fit(variables)
    print "Labels: ",k.labels_
    print "Cluster centers: ",k.cluster_centers_
    return k

if __name__=="__main__":
    #X = np.array([[30, 50, 80,20], [40, 70, 50, 23], [1, 0 ,2, 4], [5,8,8,0]])
    #kmeans = KMeans(n_clusters=2, random_state=0).fit(X)
    k = try_kmeans('./tmp_variables.csv')
