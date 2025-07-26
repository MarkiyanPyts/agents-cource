#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from financial_researcher.crew import FinancialResearcher

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run Financial Researcher crew.
    """

    inputs = {
        'company': 'Tesla',
    }

    results = FinancialResearcher().crew().kickoff(
        inputs=inputs,
    )
    print(f"Results: {results.raw}")

if __name__ == "__main__":
    run()