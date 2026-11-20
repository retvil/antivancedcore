"""brands package — one sub-package per Anti<Brand>Vanced product.

Each sub-package exposes:
- ``CFG``: a populated :class:`antivancedcore.brand.BrandConfig`
- ``<brand>_detect``: the brand's scan/remove engine module
- ``main.py`` / ``main_extended.py``: entry points

Import surface::

    from brands.baidu import CFG, baidu_detect
    from brands import baidu, sogou, ...
"""
