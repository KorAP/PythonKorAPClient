from setuptools import setup, find_packages

with open("Readme.md", "r") as fh:
    long_description = fh.read()

setup(
    name="KorAPClient",
    version="0.5.9.9000",
    author="Marc Kupietz",
    author_email="kupietz@ids-mannheim.de",
    description="Client package to access KorAP's web service API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www1.ids-mannheim.de/kl/projekte/korap.html",
    license="BSD",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
    ],
    scripts=['bin/korapclient'],
    test_suite='nose.collector',
    tests_require=['nose'],
    python_requires='>=3.6',
    install_requires=[
        'rpy2>=3.3',
        'plotly',
        'plotly-express',
        'pandas',
        'markdown'
    ]
)
