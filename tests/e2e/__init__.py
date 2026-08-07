"""Suite de verificacion de punta a punta del kit instalado (SPEC-018).

Es paquete a proposito: asi `tests/` queda como basedir de todos los modulos de
la suite y tanto los escenarios como los unitarios del harness importan el
mismo `e2e.lib.*`, sin dos copias del modulo en `sys.modules`.
"""
