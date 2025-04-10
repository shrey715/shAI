from setuptools import setup, find_packages

setup(
    name='shai',
    version='0.1.0',
    author='Shreyas Deb',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'click',
        'requests',
        'ollama',
        'rich',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'shai=main:main',
        ],
    },
    description='A smarter bash using LLM-powered NLP',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
)