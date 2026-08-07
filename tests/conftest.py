"""Raiz de las suites: existe para que `tests/` quede importable.

Con el import mode `prepend` de pytest, cada archivo recogido inserta en
`sys.path` su *basedir* (el primer directorio ancestro sin `__init__.py`). Sin
este archivo el basedir de la suite unitaria es `tests/unit`, y ni
`fixtures_proyecto` ni el paquete `e2e` serian importables desde ella. Con el
conftest aca, el basedir de este modulo es `tests/`, que queda en `sys.path`
para todas las suites.

Se carga tambien cuando se corre solo `tests/unit`, porque pytest recoge los
conftest de todos los directorios ancestros de los argumentos.
"""
