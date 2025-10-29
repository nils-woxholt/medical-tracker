import sys, pkgutil
print('Python exe:', sys.executable)
print('sys.path head:', sys.path[:3])
loader = pkgutil.find_loader('jose')
print('jose loader found:', loader is not None)
if loader:
    import jose
    print('jose version:', getattr(jose, '__version__', 'unknown'))
else:
    print('jose not importable')
