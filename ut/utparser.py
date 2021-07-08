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
        from .tasks import send_report_email

        # fmt: off
        self.add_function("send_report_email",5,lambda r_id,e_field,t_id,pk,changes: send_report_email(Report_id=r_id,email_field=e_field,email_template_id=t_id,pk=pk,changes=changes))
        self.add_function("now", 0, lambda: datetime.now())
        self.add_function("date", 0, lambda: datetime.now().date())
        self.add_function("time", 0, lambda: datetime.now().time())
        self.add_function("str", 1, lambda dt: str(dt))
        # fmt: on

#parser=UtParser()
#parser['a']=3
#parser.vars()