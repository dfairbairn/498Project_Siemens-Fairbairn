from scipy.spatial.distance import mahalanobis
import scipy as sp
import pandas as pd

def mahalanobisR(myRow, inData, covariance):
    """
    Find eucledian distance between given row and data given
    data could be an array or a single row
    requres covariance matrix, not inverted covariance matrix
    """
    IC = covariance.values if isinstance(covariance, pd.DataFrame) else covariance
    IC = sp.linalg.inv(IC)

    m = []
    if (len(inData.shape) == 1):
        return(mahalanobis(inData,myRow,IC) ** 2)
    for i in range(inData.shape[0]):
        m.append(mahalanobis(inData.ix[i,:],myRow,IC) ** 2)
    return(m)

if __name__=="__main__":
    x = pd.read_csv('tmp_variables.csv')
    x = x.ix[:,1:]

    Sx = x.cov().values
    #Sx = sp.linalg.inv(Sx)

    mean = x.mean().values
    mR = mahalanobisR(mean,x,Sx)

