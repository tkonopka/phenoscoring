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


def comparison_code(modelval, refval, bg):
    """convert a set of variables into ComparisonCodes codes."""

    if modelval > bg:
        if refval > bg:
            result = ComparisonCodes.TP
        elif refval < bg:
            result = ComparisonCodes.FP
        else:
            result = ComparisonCodes.AP
    elif modelval < bg:
        if refval > bg:
            result = ComparisonCodes.FN
        elif refval < bg:
            result = ComparisonCodes.TN
        else:
            result = ComparisonCodes.AN
    else:        
        if refval > bg:
            result = ComparisonCodes.EP
        elif refval < bg:
            result = ComparisonCodes.EN
        else:
            result = ComparisonCodes.U
            
    return result            


