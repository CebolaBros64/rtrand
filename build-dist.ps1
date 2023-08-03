
cxfreeze -c main.py --target-dir $args[0]
Copy-Item -Recurse resources $args[0]
