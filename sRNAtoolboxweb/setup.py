import os
from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='srnatoolboxweb',
    version='2.0.0',
    packages=find_packages(),
    python_modules=['manage'],
    include_package_data=True,
    description='sRNAtoolbox Web Application',
    author='Antonio Rueda, Ernesto Aparicio',
    author_email='aruemar@gmail.com',
    classifiers=[
        'Environment :: Other Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11.2',
        'Intended Audience :: Other Audience',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering',
    ],
    install_requires=[
        "Django==1.11.2",
        "pytz==2017.2",
        "wheel==0.24.0",
        "dajax==1.3",
        "xlrd==1.0.0",
        "pygal==2.3.1",
        "djangorestframework==3.6.3",
        "django-tables2=1.7.1"
    ]
)