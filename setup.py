import rulecheck
import sys
from setuptools import setup
from setuptools import find_packages

if sys.version_info.major < 3:
    sys.exit('Python < 3 is unsupported.')


with open('README.md', encoding='utf8') as file:
    long_description = file.read()

setup(
    name='rulecheck',
    version=rulecheck.__version__,
    license='MIT',
    description='Utility to check source code against coding convention rules.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Erik Shreve",
    url='https://github.com/e-shreve/rulecheck',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Java',
        'Programming Language :: C#',
        'Topic :: Utilities'
    ],
    python_required='>=3.7',
    install_requires=[
          'lxml',
    ],
    entry_points={
        'console_scripts': [
            'rulecheck = rulecheck.engine:main',
        ],
    },    
)