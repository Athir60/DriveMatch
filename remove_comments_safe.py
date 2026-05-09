import os

def remove_comments_from_file(filepath):
    """Remove all comments from a Python file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#!'):
            new_lines.append(line)
        elif stripped.startswith('#'):
            continue
        else:
            new_lines.append(line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ Cleaned: {filepath}")

count = 0
exclude_dirs = ['venv', '__pycache__', 'migrations', 'env']

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            remove_comments_from_file(filepath)
            count += 1

print(f"\n✅ Done! Cleaned {count} Python files.")