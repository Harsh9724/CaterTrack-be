# app/core/patches.py
import bcrypt

# If bcrypt has no __about__, create one with a __version__ attribute
if not hasattr(bcrypt, "__about__"):
    class _About:
        __version__ = getattr(bcrypt, "__version__", "0.0.0")
    bcrypt.__about__ = _About
