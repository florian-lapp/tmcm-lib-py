import setuptools

setuptools.setup(
    name = 'TMCM-Lib',
    description = 'Trinamic Module Library for Python',
    keywords = ['Trinamic', 'TMCM', 'TMCL', 'Stepper-Motor-Control'],
    version = '0.3.0',
    url = 'https://github.com/c0deba5e/tmcm-lib-py',
    packages = ['tmcm_lib', 'tmcm_lib.tmcm_3110'],
    install_requires = ['pyserial'],
    author = 'c0deba5e',
    author_email = 'e5abed0c@gmail.com'
)