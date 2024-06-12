import abc


def _all_checks(Cls, *props) -> bool:
    """Helper for ``__subclasshook__`` methods.

    :param Cls:  The class to check for the attributes in it's ``__mro__``
    :param props:  Attribute names to ensure are in the ``Cls``.

    """
    checks = map(
        lambda x: any(x in vars(Base) for Base in Cls.__mro__),
        props
    )
    return all(checks)


class AsyncContextManagerABC(metaclass=abc.ABCMeta):
    """Abstract representation of an async context manager.

    Ensures a class has ``__aenter__`` and ``__aexit__`` methods.

    """

    @abc.abstractmethod
    async def __aenter__(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    async def __aexit__(self, exctype, excval, traceback):  # pragma: no cover
        pass

    @classmethod
    def __subclasshook__(cls, Cls):
        if cls is AsyncContextManagerABC:
            return _all_checks(Cls, '__aenter__', '__aexit__')
        return NotImplemented  # pragma: no cover
