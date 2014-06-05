#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = "Corrigible",
    version = "0.1",
    packages = find_packages(),
    scripts = ['corrigible'],
    
    install_requires = None, # ['pkg>=vers']
    
    package_data = None, # somewhat strange, look at http://pythonhosted.org/setuptools/setuptools.html#installing-setuptools
    
    author = 'Fred McDavid',
    author_email = 'fred@landmetrics.com',
    description = 'Corrigible makes ansible playbooks more friendly and maintainable',
    license = 'PSF',
    keywords = 'ansible devops automated deployment',
    url = 'http://landmetrics.com/projects/corrigible'
)