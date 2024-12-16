from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="warrior",
    version="0.1.0",
    description="Control software for the hardware-in-the-loop tester (HILT)",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/waterloo-rocketry/warrior',
    author='Waterloo Rocketry',
    author_email='contact@waterloorocketry.com',
    license='MIT',
    packages=find_packages(include=['warrior']),
)
