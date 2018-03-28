import numpy as _np
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Lasso

from .base import BaseModel, sklearn_mixin
from .utils import X_fitter, X_predictor, epistasis_fitter
from ..stats import pearson

from gpmap import GenotypePhenotypeMap

# Suppress an annoying error from scikit-learn
import warnings
warnings.filterwarnings(action="ignore", module="scipy",
                        message="^internal gelsd")


@sklearn_mixin(LinearRegression)
class EpistasisLinearRegression(BaseModel):
    """Ordinary least-squares regression for estimating high-order, epistatic
    interactions in a genotype-phenotype map.

    Methods are described in the following publication:
        Sailer, Z. R. & Harms, M. J. 'Detecting High-Order Epistasis in
        Nonlinear Genotype-Phenotype Maps'. Genetics 205, 1079-1088 (2017).

    Parameters
    ----------
    order : int
        order of epistasis

    model_type : str (default="global")
        model matrix type. See publication above for more information
    """
    def __init__(self, order=1, model_type="global", n_jobs=1, **kwargs):
        # Set Linear Regression settings.
        self.fit_intercept = False
        self.normalize = False
        self.copy_X = False
        self.n_jobs = n_jobs
        self.set_params(model_type=model_type, order=order)
        self.Xbuilt = {}

        # Store model specs.
        self.model_specs = dict(
            order=self.order,
            model_type=self.model_type,
            **kwargs)

    @property
    def num_of_params(self):
        n = 0
        n += self.epistasis.n
        return n

    @epistasis_fitter
    @X_fitter
    def fit(self, X='obs', y='obs', **kwargs):
        return super(self.__class__, self).fit(X, y)

    def fit_transform(self, X='obs', y='obs', **kwargs):
        return self.fit(X=X, y=y, **kwargs)

    @X_predictor
    def predict(self, X='obs'):
        return super(self.__class__, self).predict(X)


    def predict_transform(self, X='obs', y='obs'):
        return self.predict(X=X)

    @X_fitter
    def score(self, X='obs', y='obs'):
        return super(self.__class__, self).score(X, y)

    @property
    def thetas(self):
        return self.coef_

    @X_predictor
    def hypothesis(self, X='obs', thetas=None):
        if thetas is None:
            thetas = self.thetas
        return _np.dot(X, thetas)

    def hypothesis_transform(self, X='obs', y='obs', thetas=None):
        return self.hypothesis(X=X, thetas=thetas)

    @X_fitter
    def lnlike_of_data(
            self,
            X="obs", y="obs",
            yerr="obs",
            thetas=None):
        # If thetas are not explicitly named, get them from the model
        if thetas is None:
            thetas = self.thetas

        # Handle yerr.
        # Check if yerr is string
        if type(yerr) is str and yerr in ["obs", "complete"]:
            yerr = self.gpm.std.upper

        # Else, numpy array or dataframe
        elif type(y) != np.array and type(y) != pd.Series:
            raise FittingError("yerr is not valid. Must be one of the "
                               "following: 'obs', 'complete', "
                               "numpy.array, pandas.Series. Right now, "
                               "its {}".format(type(yerr)))

        # Calculate y from model.
        ymodel = self.hypothesis(X=X, thetas=thetas)
        return (- 0.5 * _np.log(2 * _np.pi * yerr**2) -
                (0.5 * ((y - ymodel)**2 / yerr**2)))


@sklearn_mixin(Lasso)
class EpistasisLasso(BaseModel):
    """A scikit-learn Lasso Regression class for discovering sparse
    epistatic coefficients.

    Methods are described in the following publication:
        Poelwijk FJ, Socolich M, and Ranganathan R. 'Learning the pattern of
        epistasis linking enotype and phenotype in a protein'.
        bioRxiv. (2017).

    Parameters
    ----------
    order : int
        order of epistasis

    model_type : str (default="global")
        model matrix type. See publication above for more information

    alpha : float
        Constant that multiplies the L1 term. Defaults to 1.0. alpha = 0 is
        equivalent to an ordinary least square, solved by the
        EpistasisLinearRegression object.

    precompute :
        Whether to use a precomputed Gram matrix to speed up calculations.
        If set to 'auto' let us decide. The Gram matrix can also be passed
        as argument. For sparse input this option is always True to preserve
        sparsity.

    max_iter : int
        The maximum number of iterations.

    tol : float
        The tolerance for the optimization: if the updates are smaller than
        tol, the optimization code checks the dual gap for optimality and
        continues until it is smaller than tol.

    warm_start : bool
        When set to True, reuse the solution of the previous call to fit as
        initialization, otherwise, just erase the previous solution.

    positive : bool
        When set to True, forces the coefficients to be positive.

    random_state : int
        The seed of the pseudo random number generator that selects a random
        feature to update. If int, random_state is the seed used by the random
        number generator; If RandomState instance, random_state is the random
        number generator; If None, the random number generator is the
        RandomState instance used by np.random. Used when
        selection == 'random'.

    selection : str
        If set to 'random', a random coefficient is updated every iteration
        rather than looping over features sequentially by default. This
        (setting to 'random') often leads to significantly faster convergence
        especially when tol is higher than 1e-4.
    """
    def __init__(
            self,
            order=1,
            model_type="global",
            alpha=1.0,
            precompute=False,
            max_iter=1000,
            tol=0.0001,
            warm_start=False,
            positive=False,
            random_state=None,
            selection='cyclic',
            **kwargs):
        # Set Linear Regression settings.
        self.fit_intercept = False
        self.normalize = False
        self.copy_X = True
        self.alpha = alpha
        self.precompute = precompute
        self.max_iter = max_iter
        self.tol = tol
        self.warm_start = warm_start
        self.positive = positive
        self.random_state = random_state
        self.selection = selection
        self.l1_ratio = 1.0

        self.set_params(model_type=model_type, order=order)
        self.Xbuilt = {}

        # Store model specs.
        self.model_specs = dict(
            order=self.order,
            model_type=self.model_type,
            **kwargs)

    def compression_ratio(self):
        """Compute the compression ratio for the Lasso regression
        """
        vals = self.epistasis.values
        zeros = vals[vals == 0]

        numer = len(zeros)
        denom = len(vals)
        return numer/denom

    @property
    def num_of_params(self):
        n = 0
        vals = self.epistasis.values
        vals = vals[vals > 0]
        n += len(vals)
        return n

    @epistasis_fitter
    @X_fitter
    def fit(self, X='obs', y='obs', **kwargs):
        # If a threshold exists in the data, pre-classify genotypes
        X = _np.asfortranarray(X)
        return super(self.__class__, self).fit(X, y)

    def fit_transform(self, X='obs', y='obs', **kwargs):
        return self.fit(X=X, y=y, **kwargs)

    @X_predictor
    def predict(self, X='obs'):
        X = _np.asfortranarray(X)
        return super(self.__class__, self).predict(X)

    def predict_transform(self, X='obs', y='obs'):
        return self.predict(X=X)

    @X_fitter
    def score(self, X='obs', y='obs'):
        X = _np.asfortranarray(X)
        return super(self.__class__, self).score(X, y)

    @property
    def thetas(self):
        return self.coef_

    @X_predictor
    def hypothesis(self, X='obs', thetas=None):
        if thetas is None:
            thetas = self.thetas
        return _np.dot(X, thetas)

    def hypothesis_transform(self, X='obs', thetas=None):
        pass

    @X_fitter
    def lnlike_of_data(
            self,
            X="obs", y="obs",
            yerr="obs",
            thetas=None):
        # If thetas are not explicitly named, get them from the model
        if thetas is None:
            thetas = self.thetas

        # Handle yerr.
        # Check if yerr is string
        if type(yerr) is str and yerr in ["obs", "complete"]:
            yerr = self.gpm.std.upper

        # Else, numpy array or dataframe
        elif type(y) != np.array and type(y) != pd.Series:
            raise FittingError("yerr is not valid. Must be one of the "
                               "following: 'obs', 'complete', "
                               "numpy.array, pandas.Series. Right now, "
                               "its {}".format(type(yerr)))

        # Calculate y from model.
        ymodel = self.hypothesis(X=X, thetas=thetas)

        # Return the likelihood of this model (with an L1 prior)
        return (- 0.5 * _np.log(2 * _np.pi * yerr**2) -
                (0.5 * ((y - ymodel)**2 / yerr**2)) -
                (self.alpha * sum(abs(thetas))))
