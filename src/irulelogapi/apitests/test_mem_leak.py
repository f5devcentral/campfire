import sys, os
import time
from pympler.tracker import SummaryTracker
import testsuites
import flaminglog.logrule as flaminglog

#runs a memory profiler
tracker = SummaryTracker()

print(tracker.print_diff())
for i in range(0,100):
    #runs all tests except cleanup
    testsuites.run_full_suite(0)
    if(i%10==0):
        print(tracker.print_diff())

#sleep to allow any garbage collection to fully finish
time.sleep(10)

print(tracker.print_diff())
print("If the '# objects' and the 'total size' are both low numbers then"
        " there is no memory leak")


