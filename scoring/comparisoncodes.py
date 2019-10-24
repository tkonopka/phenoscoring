"""
Class that defines comparison codes, e.g. true positive, etc, 
"""


from enum import Enum


class ComparisonCodes(Enum):
    """Codification of true positive, false positive, etc."""
    
    TP = "TP"
    FP = "FP"
    EP = "EP"
    AP = "AP"
    U = "U"
    TN = "TN"
    FN = "FN"
    EN = "EN"
    AN = "AN"
    
    def __str__(self):
        return str(self.value)


def comparison_code(model_val, ref_val, bg):
    """convert a set of values into ComparisonCodes codes

    :param model_val: number, value in a model
    :param ref_val: number, value associated with a reference
    :param bg: number, background value
    :return: Enum object
    """

    if model_val > bg:
        if ref_val > bg:
            result = ComparisonCodes.TP
        elif ref_val < bg:
            result = ComparisonCodes.FP
        else:
            result = ComparisonCodes.AP
    elif model_val < bg:
        if ref_val > bg:
            result = ComparisonCodes.FN
        elif ref_val < bg:
            result = ComparisonCodes.TN
        else:
            result = ComparisonCodes.AN
    else:        
        if ref_val > bg:
            result = ComparisonCodes.EP
        elif ref_val < bg:
            result = ComparisonCodes.EN
        else:
            result = ComparisonCodes.U
            
    return result            


