from setuptools import setup, find_packages

setup(
    name='midrc_react',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        # list additional dependencies here, for example:
        # 'numpy',
        # 'pandas',
    ],
    entry_points={
        'console_scripts': [
            'midrc-react=midrc_react.__main__:launch_react',
        ],
        'console_scripts': [
            'MIDRC-REACT=midrc_react.__main__:launch_react',
        ],
    },
)
