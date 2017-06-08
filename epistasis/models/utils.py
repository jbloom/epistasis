import numpy as np
from functools import wraps
from sklearn.preprocessing import binarize

import warnings
warnings.filterwarnings("ignore")

def sklearn_to_epistasis():
    """Decorate a scikit learn class with this function and automagically convert it into a
    epistasis sklearn model class.
    """
    def inner(cls):
        base_model = cls.__bases__[-1]
        for attr in base_model.__dict__:
            method = getattr(base_model, attr)
            setattr(cls, attr, getattr(base_model, attr))
        return cls
    return inner

def X_predictor(method):
    """Decorator to automatically generate X for predictor methods in epistasis models."""
    @wraps(method)
    def inner(self, X=None, *args, **kwargs):
        """"""
        # Build input to
        if X is None:
            X = self.X_constructor(genotypes=self.gpm.binary.complete_genotypes)
            if hasattr(self, "_complete_classes"):
                X = np.multiply(X, self._complete_classes[:, np.newaxis])
        return method(self, X=X, *args, **kwargs)
    return inner

def X_fitter(method):
    """Decorator to automatically generate X for fit methods in epistasis models.

    This takes a few things into account.
    """
    @wraps(method)
    def inner(self, X=None, y=None, *args, **kwargs):
        # If no Y is given, try to get it from
        module = self.__module__.split(".")[-1]
        if y is None:
            # Pull y from the phenotypes in a GenotypePhenotypeMap
            y = np.array(self.gpm.binary.phenotypes)

        # If X is not given, build one.
        if X is None and y is not None:
            # See if an X already exists in the model
            X = self.X_constructor(genotypes=self.gpm.binary.genotypes)

            # If the model was preprocessed, subset data.
            if hasattr(self, "_classes"):
                X = X[y > self.threshold]
                y = y[y > self.threshold]

            self.X = X
            output = method(self, X=X, y=y, *args, **kwargs)
            # Reference the model coefficients in the epistasis map.
            self.epistasis.values = np.reshape(self.coef_, (len(self.epistasis.sites),))
            return output

        else:
            # If the model was preprocessed, subset data.
            if hasattr(self, "_classes"):
                X = X[y > self.threshold]
                y = y[y > self.threshold]

            self.X = X
            output = method(self, X=X, y=y, *args, **kwargs)
            return output
    return inner
