import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='fy-splunk',
    version='0.1.0',
    author='李四',
    author_email='lisi@example.com',
    description='A Python package for interacting with Splunk.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/org/fy-splunk',
    packages=['splunk'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'splunk-sdk'
    ],
)