from setuptools import setup, find_packages

setup(
    name='mgp-common',
    version="0.1.5",
    license='MIT',
    author="Peter Li",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/syccxcc/MGP-common',
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],

)
