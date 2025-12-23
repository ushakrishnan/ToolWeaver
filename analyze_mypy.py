import re
from collections import defaultdict

# Read the mypy output
with open('mypy_output.txt', 'r') as f:
    output = f.read()

# Parse errors
files_errors = defaultdict(lambda: {'count': 0, 'errors': defaultdict(int)})
total_errors = 0

for line in output.split('\n'):
    if '.py:' in line and 'error:' in line:
        match = re.match(r'([^:]+\.py):(\d+):\s*error:\s*(.*)', line)
        if match:
            filepath, lineno, error_msg = match.groups()
            # Extract error type (text before square brackets)
            error_type = error_msg.split('[')[0].strip() if '[' in error_msg else error_msg[:60]
            files_errors[filepath]['count'] += 1
            files_errors[filepath]['errors'][error_type] += 1
            total_errors += 1

# Sort by error count
sorted_files = sorted(files_errors.items(), key=lambda x: x[1]['count'], reverse=True)

# Generate markdown summary
print("# MyPy Type Check Summary - ToolWeaver Workspace")
print("\n## Overall Statistics")
print(f"- **Total Errors**: {total_errors}")
print(f"- **Files with Errors**: {len(files_errors)}")
print(f"- **Average Errors per File**: {total_errors / len(files_errors) if files_errors else 0:.1f}")

print("\n## Top 20 Files by Error Count\n")
print("| Rank | File | Errors | Top Error Types |")
print("|------|------|--------|-----------------|")

for rank, (filepath, data) in enumerate(sorted_files[:20], 1):
    errors_count = data['count']
    # Get top 3 error types
    top_errors = sorted(data['errors'].items(), key=lambda x: x[1], reverse=True)[:3]
    error_types = "; ".join([f"{et}({c})" for et, c in top_errors])
    
    # Shorten file path for display
    short_path = filepath.replace('orchestrator\\', '').replace('_internal\\', '')
    print(f"| {rank} | `{short_path}` | {errors_count} | {error_types} |")

print("\n## Summary of Error Types (Top 15)\n")
print("| Error Type | Count | Percentage |")
print("|------------|-------|-----------|")

all_error_types = defaultdict(int)
for file_data in files_errors.values():
    for err_type, count in file_data['errors'].items():
        all_error_types[err_type] += count

sorted_error_types = sorted(all_error_types.items(), key=lambda x: x[1], reverse=True)
for err_type, count in sorted_error_types[:15]:
    percentage = (count / total_errors * 100) if total_errors > 0 else 0
    print(f"| {err_type} | {count} | {percentage:.1f}% |")

print("\n## Detailed Error Breakdown by File\n")
for rank, (filepath, data) in enumerate(sorted_files[:20], 1):
    errors_count = data['count']
    short_path = filepath.replace('orchestrator\\', '').replace('_internal\\', '')
    print(f"### {rank}. {short_path} ({errors_count} errors)")
    
    # Get all error types sorted by frequency
    sorted_errs = sorted(data['errors'].items(), key=lambda x: x[1], reverse=True)
    for err_type, count in sorted_errs[:5]:
        print(f"   - {err_type}: {count}")
    print()
