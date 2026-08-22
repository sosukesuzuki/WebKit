import resource, subprocess, sys, time
t0 = time.time()
p = subprocess.run(sys.argv[1:])
r = resource.getrusage(resource.RUSAGE_CHILDREN)
print(f"RUSAGE maxrss_kb={r.ru_maxrss} user={r.ru_utime:.2f} sys={r.ru_stime:.2f} wall={time.time()-t0:.2f} exit={p.returncode}")
