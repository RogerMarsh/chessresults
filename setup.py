# setup.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

from setuptools import setup

if __name__ == '__main__':

    long_description = open('README').read()

    setup(
        name='chessresults',
        version='5.0.2.dev0',
        description='Results database for chess games',
        author='Roger Marsh',
        author_email='roger.marsh@solentware.co.uk',
        url='http://www.solentware.co.uk',
        packages=[
            'chessresults',
            'chessresults.core', 'chessresults.help', 'chessresults.basecore',
            'chessresults.minorbases',
            'chessresults.gui', 'chessresults.gui.minorbases',
            'chessresults.db', 'chessresults.dpt', 'chessresults.sqlite',
            'chessresults.apsw', 'chessresults.unqlite', 'chessresults.vedis',
            'chessresults.tools',
            ],
        package_data={
            'chessresults.help': ['*.txt'],
            },
        long_description=long_description,
        license='BSD',
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Operating System :: OS Independent',
            'Topic :: Games/Entertainment :: Board Games',
            'Intended Audience :: End Users/Desktop',
            'Development Status :: 3 - Alpha',
            ],
        install_requires=['solentware-base==4.1.5.dev0',
                          'chesscalc==1.2.1',
                          'emailstore==1.4.2',
                          'emailextract==0.7.2',
                          'solentware-grid==2.1.3.dev0',
                          'solentware-misc==1.3',
                          ],
        dependency_links=[
            'http://solentware.co.uk/files/solentware-base-4.1.5.dev0.tar.gz',
            'http://solentware.co.uk/files/chesscalc-1.2.1.tar.gz',
            'http://solentware.co.uk/files/emailstore-1.4.2.tar.gz',
            'http://solentware.co.uk/files/emailextract-0.7.2.tar.gz',
            'http://solentware.co.uk/files/solentware-grid-2.1.3.dev0.tar.gz',
            'http://solentware.co.uk/files/solentware-misc-1.3.tar.gz',
            ],
        )