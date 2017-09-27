
import unittest
import pytest
from gpmap import GenotypePhenotypeMap
from ..mixed import EpistasisMixedRegression
import warnings

# Ignore fitting warnings
warnings.simplefilter("ignore", RuntimeWarning)

@pytest.fixture
def gpm():
    """Create a genotype-phenotype map"""
    wildtype = "000"
    genotypes =  ["000", "001", "010", "100", "011", "101", "110", "111"]
    phenotypes = [2.5838167335880149,
         2.4803514336043708,
         2.2205925336075762,
         2.1864673462520905,
         1.5622922695718136,
         1.8972733199455831,
         1.3324426002143119,
         1.7367637632162392]
    stdeviations = 0.01
    return GenotypePhenotypeMap(wildtype, genotypes, phenotypes, stdeviations=stdeviations)


class TestEpistasisMixedRegression(object):

    # Set some initial parameters for this model
    order = 3
    threshold = 1.5622922695718136
        
    def test_init(self, gpm):
        model = EpistasisMixedRegression(self.order, self.threshold)
        assert hasattr(model, "Model")
        assert hasattr(model, "Classifier")
        assert hasattr(model, "order")
        assert hasattr(model, "threshold")
        assert hasattr(model, "model_type")
    
    def test_add_gpm(self, gpm):
        model = EpistasisMixedRegression(self.order, self.threshold)
        model.add_gpm(gpm)
        assert hasattr(model, "gpm")
        assert hasattr(model.Model, "gpm")
        assert hasattr(model.Classifier, "gpm")
    
    def test_fit(self, gpm):
        model = EpistasisMixedRegression(self.order, self.threshold)
        model.add_gpm(gpm)
        model.fit(lmbda=0, A=1,B=1)
        assert hasattr(model, "Model")
        
    def test_predict(self, gpm):
        model = EpistasisMixedRegression(self.order, self.threshold)
        model.add_gpm(gpm)   
        model.fit(lmbda=0, A=1,B=1)
        predicted = model.predict(X="complete")
        assert "predict" in model.Model.Linear.Xbuilt
        assert "predict" in model.Model.Additive.Xbuilt
        assert len(predicted) == gpm.n 

    
    def test_thetas(self, gpm):
        model = EpistasisMixedRegression(self.order, self.threshold)
        model.add_gpm(gpm)   
        model.fit(lmbda=0, A=1,B=1)
        
        coefs = model.thetas
        # Tests
        assert len(coefs) == 15
    
    # def test_hypothesis(self, gpm):
    # 
    #     model = EpistasisMixedRegression(self.order, self.threshold)
    #     model.add_gpm(gpm)   
    #     model.fit(lmbda=0, A=1,B=1)
    #     
    #     predictions = model.hypothesis()
    #     # Need more thorough tests
    #     assert len(predictions) == gpm.n
    #     
    # def test_lnlikelihood(self, gpm):
    #     model = EpistasisMixedRegression(self.order, self.threshold)
    #     model.add_gpm(gpm)   
    #     model.fit(lmbda=0, A=1,B=1)
    #     
    #     # Calculate lnlikelihood
    #     lnlike = model.lnlikelihood()
    #     assert lnlike.dtype == float
