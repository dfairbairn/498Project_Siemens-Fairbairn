from sklearn.cluster import KMeans
from sklearn.metrics.cluster import silhouette_score
from sklearn.metrics.cluster import calinski_harabaz_score
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

def cluster_number_study(n=50):
    """ Check out some basic cluster metrics for different cluster sizes. """

    fnamecsv = './AL_pchange_vars.csv'
    df = pd.read_csv(fnamecsv)
    variables = (df.as_matrix())[:,1:].astype(float)
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

def plot_cluster_performance(fn_sil='cluster_vs_silhouette.txt', fn_cal='cluster_vs_calharabaz.txt'):
    """ Plot the cluster performances vs. number of clusters """
    import matplotlib.pyplot as plt   
    f_sil = open(fn_sil,'r')
    pltdata_sil = np.array([ [int(s.split()[0]), float(s.split()[1])] for s in f_sil.readlines()])
    f_cal = open(fn_cal,'r')
    pltdata_cal = np.array([ [int(s.split()[0]), float(s.split()[1])] for s in f_cal.readlines()])

    plt.plot(pltdata_sil[:,0],pltdata_sil[:,1])
    plt.title('Silhouette Score vs. Number of Clusters')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Silhouette Score')
    plt.show()

    plt.figure()
    plt.plot(pltdata_cal[:,0],pltdata_cal[:,1])
    plt.title('Calinski-Harabaz Score vs. Number of Clusters')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Calinski-Harabaz Score')
    plt.show()

def put_in_pandas_old(fnamecsv='./AL_pchange_vars.csv'):
    tmp_df = pd.read_csv(fnamecsv)
    tmp_df2 = tmp_df.loc[:][['INN_CT','RBI_CT','PA_BALL_CT','EVENT_OUTS_CT','BAT_DEST_ID','SCORE_DIFF','PIT_COUNT']]

    normd_vars = (tmp_df2.as_matrix()).astype(float)
    variables = normd_vars.copy()  
    for j in range(len(normd_vars[0,:])): #ugly way of looping over columns
        normd_vars[:,j] = ( normd_vars[:,j] - np.mean(normd_vars[:,j]))/np.std(normd_vars[:,j])
    k = KMeans(n_clusters=3, n_init=100, n_jobs=3).fit(normd_vars)
    labels_array = np.array([k.labels_])
    tmp = np.concatenate([variables,labels_array.T],axis=1)

    df = pd.DataFrame(tmp,columns=['INN_CT','RBI_CT','PA_BALL_CT','EVENT_OUTS_CT','BAT_DEST_ID','SCORE_DIFF','PIT_COUNT','LABEL'])
    return df 

def put_in_pandas(fnamecsv='./AL_pchange_vars.csv'):
    """ 
    Performs clustering on a dataframe in a csv file and returns a dataframe 
    of the events with their cluster labeling. 
    """
    tmp_df = pd.read_csv(fnamecsv)
    tmp_df2 = tmp_df.loc[:][['GAME_ID','EVENT_ID','INN_CT','RBI_CT','PA_BALL_CT','EVENT_OUTS_CT','BAT_DEST_ID','SCORE_DIFF','PIT_COUNT']]

    variables = tmp_df2.as_matrix()
    normd_vars = (variables.copy()[:,2:]).astype(float) # Leave out the Game ID and Event ID variables
    for j in range(len(normd_vars[0,:])): # Ugly way of looping over columns
        normd_vars[:,j] = ( normd_vars[:,j] - np.mean(normd_vars[:,j]))/np.std(normd_vars[:,j])
    k = KMeans(n_clusters=3, n_init=100, n_jobs=3).fit(normd_vars)
    labels_array = np.array([k.labels_])
    tmp = np.concatenate([variables,labels_array.T],axis=1)
    df = pd.DataFrame(tmp,columns=['GAME_ID','EVENT_ID','INN_CT','RBI_CT','PA_BALL_CT','EVENT_OUTS_CT','BAT_DEST_ID','SCORE_DIFF','PIT_COUNT','LABEL'])
    return df 

if __name__=="__main__":
    #X = np.array([[30, 50, 80,20], [40, 70, 50, 23], [1, 0 ,2, 4], [5,8,8,0]])
    #kmeans = KMeans(n_clusters=2, random_state=0).fit(X)

    fnamecsv = './AL_pchange_vars.csv'
    df = pd.read_csv(fnamecsv)

    labeled_df = put_in_pandas(fnamecsv)
