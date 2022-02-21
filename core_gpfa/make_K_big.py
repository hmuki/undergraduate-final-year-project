# Construct full GP covariance matrix
from core_gpfa.util import invToeplitz
import numpy as np

sigma0 = 0.25
sigma = 0.25
cov = np.diag([sigma0**2, sigma**2])

def nn_kernel(x, y):
    X = np.array([1, x])
    Y = np.array([1, y])
    num = 2 * np.dot(np.dot(X.T, cov), Y) # matrix multiplication is associative
    denom = np.sqrt((1 + 2 * np.dot(np.dot(X.T, cov), X)) * (1 + 2 * np.dot(np.dot(Y.T, cov), Y)))
    return (2/np.pi) * np.arcsin(num/denom)


def circular_kernel(T):
    return np.array([[np.sqrt(1-(i/T)**2) * np.sqrt(1-(j/T)**2) for j in range(1,T+1)] for i in range(1,T+1)])


def logit_kernel(T):
    return np.array([[np.log(i/(T+2)/(1-i/(T+2))) * np.log(j/(T+2)/(1-j/(T+2))) for j in range(1,T+1)] for i in range(1,T+1)])


def Lee_metric(T):
    return np.array([[min(abs(i-j), T-abs(i-j)) for j in range(1,T+1)] for i in range(1,T+1)])


def Tsum(T):
    return np.array([[i+j for j in range(1, T+1)] for i in range(1,T+1)])


def Discrete_metric(T):
    return np.array([[0 if j==i else 1 for j in range(1,T+1)] for i in range(1,T+1)])


def make_K_big(params, T):

    x_dim = params.C.shape[1]

    # TODO check if 0 : xDim : (xDim*(T-1))
    idx = np.arange(0, x_dim*(T-1)+1, x_dim)

    K_big = np.zeros((x_dim*T, x_dim*T))
    K_big_inv = np.zeros((x_dim*T, x_dim*T))

    Tdif = np.tile(np.arange(1, T+1).reshape((T, 1)), (1, T)) - \
        np.tile(np.arange(1, T+1), (T, 1))
    diffSq = Tdif ** 2
    logdet_K_big = 0

    for i in range(x_dim):

        if params.cov_type == 'rbf':
            if params.distance == 'Root Manhattan':
                K = (1 - params.eps[i]) \
                    * (np.exp(-0.5 * params.gamma[i] * np.abs(Tdif)) + 0.5 * np.eye(T)) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Lee':
                K = (1 - params.eps[i]) \
                    * np.exp(-0.5 * Lee_metric(T)**2) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Canberra':
                K = (1 - params.eps[i]) \
                    * np.exp(-0.5 * (np.abs(Tdif)/Tsum(T))**2) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Discrete':
                K = (1 - params.eps[i]) \
                    * np.exp(-0.5 * Discrete_metric(T)**2) \
                    + params.eps[i] * np.eye(T)
            else: # Euclidean / Manhattan
                K = (1 - params.eps[i]) \
                    * np.exp(-0.5 * params.gamma[i] * diffSq) \
                    + params.eps[i] * np.eye(T)
            
        elif params.cov_type == 'rq':
            if params.distance == 'Root Manhattan':
                K = (1 - params.eps[i]) \
                    * ((1 - (params.gamma[i] * np.abs(Tdif))/(params.gamma[i] * np.abs(Tdif) + 1)) + np.eye(T)) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Lee':
                K = (1 - params.eps[i]) \
                    * (1 - (Lee_metric(T)**2)/(Lee_metric(T)**2 + 1)) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Canberra':
                K = (1 - params.eps[i]) \
                    * (1 - ((np.abs(Tdif)/Tsum(T))**2)/((np.abs(Tdif)/Tsum(T))**2 + 1)) \
                    + params.eps[i] * np.eye(T)                
            elif params.distance == 'Discrete':
                K = (1 - params.eps[i]) \
                    * (1 - (Discrete_metric(T)**2)/(Discrete_metric(T)**2 + 1)) \
                    + params.eps[i] * np.eye(T)
            else: # Euclidean / Manhattan
                K = (1 - params.eps[i]) \
                    * (1 - (params.gamma[i] * diffSq)/(params.gamma[i] * diffSq + 1)) \
                    + params.eps[i] * np.eye(T)

        elif params.cov_type == 'pw':
            if params.distance == 'Root Manhattan':
                K = ((1 - params.eps[i]) * np.sinc(0.5 * params.gamma[i] * np.sqrt(np.abs(Tdif))) + np.eye(T)) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Lee':
                K = ((1 - params.eps[i]) * np.sinc(0.5 * params.gamma[i] * Lee_metric(T)) + 5 * np.eye(T)) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Canberra':
                K = (1 - params.eps[i]) \
                    * (np.sinc(2 * (np.abs(Tdif)/Tsum(T))) + 0.1 * np.eye(T)) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Discrete':
                K = (1 - params.eps[i]) \
                    * np.sinc(2 * Discrete_metric(T)) \
                    + params.eps[i] * np.eye(T)
            else: # Manhattan / Euclidean
                K = (1 - params.eps[i]) * np.sinc(0.5 * params.gamma[i] * np.abs(Tdif)) \
                    + params.eps[i] * np.eye(T)

        elif params.cov_type == 'im':
            if params.distance == 'Root Manhattan':
                K = (1 - params.eps[i]) * (1/np.sqrt(params.gamma[i] * np.abs(Tdif) + 1)) + params.eps[i] * np.eye(T)
            elif params.distance == 'Lee':
                K = (1 - params.eps[i]) * (1/np.sqrt(Lee_metric(T)**2 + 1)) + params.eps[i] * np.eye(T)
            elif params.distance == 'Canberra':
                K = (1 - params.eps[i]) * (1/np.sqrt((np.abs(Tdif)/Tsum(T))**2 + 1)) + params.eps[i] * np.eye(T)
            elif params.distance == 'Discrete':
                K = (1 - params.eps[i]) * (1/np.sqrt(Discrete_metric(T)**2 + 1)) + params.eps[i] * np.eye(T)
            else: # Manhattan / Euclidean
                K = (1 - params.eps[i]) * (1/np.sqrt(params.gamma[i] * diffSq + 1)) + params.eps[i] * np.eye(T)
        
        elif params.cov_type == 'p':
            if params.distance == 'Lee':
                top_Kp = np.exp(np.cos(Lee_metric(T))) - np.i0(1/params.lp**2)
                bottom_Kp = np.exp(1/params.lp**2) - np.i0(1/params.lp**2)
                K = (1 - params.eps[i]) * (top_Kp/bottom_Kp + 5 * np.eye(T)) \
                    + params.eps[i] * np.eye(T)
            elif params.distance == 'Discrete':
                top_Kp = np.exp(np.cos(Discrete_metric(T))) - np.i0(1/params.lp**2)
                bottom_Kp = np.exp(1/params.lp**2) - np.i0(1/params.lp**2)
                K = (1 - params.eps[i]) * (top_Kp/bottom_Kp + 5 * np.eye(T)) \
                    + params.eps[i] * np.eye(T)
            else: # Manhattan / Euclidean
                top_Kp = np.exp(np.cos(np.abs(Tdif))) - np.i0(1/params.lp**2)
                bottom_Kp = np.exp(1/params.lp**2) - np.i0(1/params.lp**2)
                K = (1 - params.eps[i]) * (top_Kp/bottom_Kp + 5 * np.eye(T)) \
                    + params.eps[i] * np.eye(T)
        
        elif params.cov_type == 'lp':
        
            top_Kp = np.exp(np.cos(np.abs(Tdif))) - np.i0(1/params.lp**2)
            bottom_Kp = np.exp(1/params.lp**2) - np.i0(1/params.lp**2)
            Kp = top_Kp/bottom_Kp + 5 * np.eye(T)
            Kg = np.exp(-params.gamma2[i] / 2 * diffSq)
            K = (1 - params.eps[i]) * (Kp * Kg) \
                + params.eps[i] * np.eye(T)      

        elif params.cov_type == 'cos':

            K = (1 - params.eps[i]) \
                * (np.cos((2*np.pi/params.p) * params.gamma[i] * np.abs(Tdif)) + np.eye(T)) \
                + params.eps[i] * np.eye(T)

        elif params.cov_type == 'lin':

            # normalised linear kernel
            K = (1 - params.eps[i]) \
            * (np.array([[0 if i==j else i*j/(T**2) for j in range(1,T+1)] for i in range(1,T+1)]) \
            + np.eye(T)) + params.eps[i] * np.eye(T)

        elif params.cov_type == 'poly':

            # normalised polynomial kernel
            K = (1 - params.eps[i]) \
            * (np.array([[0 if i==j else (i*j)**2/(T**4) for j in range(1,T+1)] for i in range(1,T+1)]) \
            + np.eye(T)) + params.eps[i] * np.eye(T)
        
        elif params.cov_type == 'nn':

            K = (1 - params.eps[i]) \
            * np.array([[nn_kernel(i,j) for j in range(1,T+1)] for i in range(1,T+1)]) \
            + params.eps[i] * np.eye(T)

        elif params.cov_type == 'circ':
        
            K = (1-params.eps[i]) \
            * (circular_kernel(T) + np.eye(T)) + params.eps[i] * np.eye(T)
        
        elif params.cov_type == 'logit':
        
            K = (1-params.eps[i]) \
            * (logit_kernel(T) + np.eye(T)) + params.eps[i] * np.eye(T)

        elif params.cov_type == 'sm':
            w = params.gamma[i][:params.Q]
            m = params.gamma[i][params.Q:params.Q*2]
            v = params.gamma[i][params.Q*2:params.Q*3]
            K = np.zeros(diffSq.shape)
            for j in range(len(w)):
                K = K + w[j] * np.exp(-2 * np.pi**2 * v[j] ** 2 * diffSq) * np.cos(2 * np.pi * Tdif.T * m[j])
            K = K + 0.00001*np.identity(K.shape[0])

        K_big[np.ix_(idx+i, idx+i)] = K
        inv_K, logdet_K = invToeplitz(K)
        K_big_inv[np.ix_(idx+i, idx+i)] = inv_K

        logdet_K_big = logdet_K_big + logdet_K

    return K_big, K_big_inv, logdet_K_big
