import os
temps = [f for f in os.listdir('.') if f.startswith('fix_') or f.startswith('test_') or f.startswith('add_')]
for f in temps:
    os.remove(f)
    print(f"Eliminado: {f}")
print("OK")
