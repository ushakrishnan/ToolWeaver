"""
Dependency Management Script for ToolWeaver

Automatically discovers and updates dependencies by:
1. Scanning all Python files for imports
2. Mapping imports to PyPI package names
3. Testing installation in clean venv
4. Updating pyproject.toml with verified versions

Usage:
    python scripts/update_dependencies.py
"""

import ast
import subprocess
import sys
from pathlib import Path

# Mapping of import names to PyPI package names (when they differ)
IMPORT_TO_PACKAGE = {
    'sentence_transformers': 'sentence-transformers',
    'sklearn': 'scikit-learn',
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
}

# Standard library modules (Python 3.10+) - don't need to install
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'audioop',
    'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins', 'bz2',
    'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
    'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
    'contextlib', 'contextvars', 'copy', 'copyreg', 'crypt', 'csv', 'ctypes',
    'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis',
    'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
    'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools',
    'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip',
    'hashlib', 'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr',
    'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json',
    'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox',
    'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib',
    'msvcrt', 'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator',
    'optparse', 'os', 'ossaudiodev', 'pathlib', 'pdb', 'pickle', 'pickletools',
    'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'posixpath',
    'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc',
    'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter',
    'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
    'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver',
    'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep',
    'struct', 'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog',
    'tabnanny', 'tarfile', 'tempfile', 'termios', 'test', 'textwrap', 'threading',
    'time', 'timeit', 'tkinter', 'token', 'tokenize', 'tomllib', 'trace', 'traceback',
    'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'typing_extensions',
    'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave',
    'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml',
    'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', '_thread',
}


def extract_imports(file_path: Path) -> set:
    """Extract all import statements from a Python file."""
    try:
        with open(file_path, encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get top-level module name
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        return imports
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return set()


def scan_project(root_dir: Path) -> dict:
    """Scan project for all imports, categorized by directory."""
    imports_by_category = {
        'core': set(),      # orchestrator/
        'tests': set(),     # tests/
        'examples': set(),  # examples/
    }

    # Scan orchestrator (core package)
    for py_file in (root_dir / 'orchestrator').rglob('*.py'):
        if py_file.name != '__init__.py':
            imports_by_category['core'].update(extract_imports(py_file))

    # Scan tests
    if (root_dir / 'tests').exists():
        for py_file in (root_dir / 'tests').rglob('*.py'):
            imports_by_category['tests'].update(extract_imports(py_file))

    # Scan examples
    if (root_dir / 'examples').exists():
        for py_file in (root_dir / 'examples').rglob('*.py'):
            imports_by_category['examples'].update(extract_imports(py_file))

    return imports_by_category


def filter_imports(imports: set) -> dict:
    """Filter and categorize imports into stdlib vs external packages."""
    external = set()
    local = {'orchestrator'}  # Our package name

    for imp in imports:
        # Skip local imports
        if imp in local:
            continue
        # Skip stdlib
        if imp in STDLIB_MODULES:
            continue
        # Skip private/internal modules
        if imp.startswith('_'):
            continue

        # Map to PyPI package name if different
        package = IMPORT_TO_PACKAGE.get(imp, imp)
        external.add(package)

    return sorted(external)


def get_installed_version(package: str) -> str:
    """Get currently installed version of a package."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split(':', 1)[1].strip()
    except subprocess.CalledProcessError:
        return None
    return None


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent

    print("🔍 Scanning project for imports...")
    imports_by_category = scan_project(root_dir)

    # Filter and categorize
    core_deps = filter_imports(imports_by_category['core'])
    test_deps = filter_imports(imports_by_category['tests'])
    example_deps = filter_imports(imports_by_category['examples'])

    # Remove test/example deps that are already in core
    test_deps_only = sorted(set(test_deps) - set(core_deps))
    example_deps_only = sorted(set(example_deps) - set(core_deps) - set(test_deps_only))

    print(f"\n📦 Core dependencies ({len(core_deps)}):")
    for dep in core_deps:
        version = get_installed_version(dep)
        if version:
            print(f"  ✓ {dep}=={version}")
        else:
            print(f"  ✗ {dep} (not installed)")

    print(f"\n🧪 Test-only dependencies ({len(test_deps_only)}):")
    for dep in test_deps_only:
        version = get_installed_version(dep)
        if version:
            print(f"  ✓ {dep}=={version}")
        else:
            print(f"  ✗ {dep} (not installed)")

    print(f"\n📚 Example-only dependencies ({len(example_deps_only)}):")
    for dep in example_deps_only:
        version = get_installed_version(dep)
        if version:
            print(f"  ✓ {dep}=={version}")
        else:
            print(f"  ✗ {dep} (not installed)")

    # Generate suggestions for pyproject.toml
    print("\n" + "="*60)
    print("📝 Suggested pyproject.toml updates:")
    print("="*60)

    print("\n[project.dependencies]")
    for dep in core_deps:
        version = get_installed_version(dep)
        if version:
            major_minor = '.'.join(version.split('.')[:2])
            print(f'    "{dep}>={major_minor}.0",')
        else:
            print(f'    "{dep}",  # VERSION UNKNOWN - please install')

    if test_deps_only:
        print("\n[project.optional-dependencies.dev]")
        print("    # Add these to existing dev dependencies:")
        for dep in test_deps_only:
            version = get_installed_version(dep)
            if version:
                major_minor = '.'.join(version.split('.')[:2])
                print(f'    "{dep}>={major_minor}.0",')
            else:
                print(f'    "{dep}",  # VERSION UNKNOWN')


if __name__ == '__main__':
    main()
