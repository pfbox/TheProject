#
# copy of date_time_arithmetic_parser.py + some functions
#
# Copyright 2021, Paul McGuire
#
#
from plusminus import BaseArithmeticParser

class UtParser(BaseArithmeticParser):
    """
    Arithmetics + base DateTime functions
    """
    def customize(self):
        from datetime import datetime

        # fmt: off
        self.add_function("now", 0, lambda: datetime.now())
        self.add_function("date", 0, lambda: datetime.now().date())
        self.add_function("time", 0, lambda: datetime.now().time())
        self.add_function("str", 1, lambda dt: str(dt))
        # fmt: on

#parser=UtParser()
#parser['a']=3
#parser.vars()