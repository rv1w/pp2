#1
from datetime import datetime,timedelta

today = datetime.now()
new_date=today - timedelta(days=5)

print(today)
print(new_date)

#2
from datetime import datetime,timedelta

today=datetime.now()
yesterday=today-timedelta(days=1)
tomorrow=today+timedelta(days=1)

print(yesterday,tomorrow)

#3

from datetime import datetime

now = datetime.now()
withno_ms = now.replace(microsecond=0)

print(now)
print(withno_ms)
#4

from datetime import datetime

date1 = datetime(2025,3,1,12,0,0)
date2 = datetime(2025,3,3,12,0,0)
dif = date2-date1

print(dif.total_seconds())

