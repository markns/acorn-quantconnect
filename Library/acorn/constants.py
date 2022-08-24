import math

CALENDAR_DAYS_IN_YEAR = 365.25
BUSINESS_DAYS_IN_YEAR = 256
# Assume 256 business days in a year. Assume no returns are iid. Therefore, we can divide by sqrt(256)=16.
ROOT_BDAYS_INYEAR = math.sqrt(BUSINESS_DAYS_IN_YEAR)
