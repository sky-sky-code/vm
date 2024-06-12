import uuid
import typing
from .manager import PoolManager

import importlib


def _quote_if_str(val):
    """Helper to quote a string.

    """
    if isinstance(val, str):
        return f"'{val}'"
    return val


class Column:

    def __init__(self, key: str = None, default: object = None, primary_key: object = False) -> object:
        self.key = key
        self.default = str(default) if type(default) == uuid.UUID else default
        self.primary_key = primary_key
        self._hidden_key = '__' + uuid.uuid4().hex

    __slots__ = ('key', 'default', 'primary_key', '_hidden_key')

    def __get__(self, instance, owner):
        if instance is None:
            return self
        rv = getattr(instance, self._hidden_key, None)
        if rv is None:
            rv = self.default() if callable(self.default) else self.default
            self.__set__(instance, rv)
        return rv

    def __set__(self, instance, value):
        setattr(instance, self._hidden_key, value)

    def __repr__(self):
        cn = self.__class__.__name__
        attrs = ', '.join(
            '{}={}'.format(attr, _quote_if_str(getattr(self, attr)))
            for attr in self.__slots__ if attr != '_hidden_key'
        )
        return f'{cn}({attrs})'


class ForeignKeyColumn(Column):
    def __init__(self, to, key: str = None):
        super().__init__(key=key)
        self.to_model = to


class RelatedColumn(Column):
    def __init__(self, related, key: str = None, module: str = None):
        super().__init__(key=key)
        self.module = module
        self.related_model = related

    @property
    def related(self):
        return getattr(self.module, self.related_model)


class ModelMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):

        for base in bases:
            base_dic = vars(base)
            for key, val in base_dic.items():
                if isinstance(val, Column) and key not in namespace:
                    namespace[key] = val

        for key, value in namespace.items():
            if isinstance(value, Column) and value.key is None:
                value.key = key

        return type.__new__(cls, name, bases, namespace, **kwargs)


class BaseModel(metaclass=ModelMeta):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def _columns(cls) -> typing.Iterator[typing.Tuple[str, Column]]:
        for (k, v) in vars(cls).items():
            if isinstance(v, Column):
                yield k, v

    @classmethod
    def get_related_column(cls):
        return tuple(c.key for (_, c) in cls._columns() if isinstance(c, RelatedColumn))

    @classmethod
    def get_insert_column(cls):
        return tuple(c.key for (_, c) in cls._columns() if not isinstance(c, RelatedColumn))

    @classmethod
    def get_fk(cls):
        return tuple(c.key for (_, c) in cls._columns() if isinstance(c, ForeignKeyColumn))

    @classmethod
    def attr_name_for_column(cls, column_name: str) -> str:
        for attr_name, col in cls._columns():
            if col.key == column_name:
                return attr_name
            elif attr_name == column_name:
                return column_name
        raise ValueError(column_name)

    @classmethod
    def column_names(cls) -> typing.Tuple[str]:
        return tuple(c.key for (_, c) in cls._columns())

    @classmethod
    def primary_key(cls) -> typing.Tuple[str]:
        return tuple(c.key for (_, c) in cls._columns()
                     if c.primary_key is True)

    def __setattr__(self, key, value):
        # check if the key is actually a database column name, and set the
        # appropriate key.
        try:
            key = self.attr_name_for_column(key)
        except ValueError:
            pass
        return super().__setattr__(key, value)

    def __repr__(self):
        cn = self.__class__.__name__
        attrs = tuple(
            map(self.attr_name_for_column, self.column_names())
        )
        attrs += tuple(k for k in vars(self).keys() if not k.startswith('_'))
        attr_string = ', '.join(
            map(lambda x: '{}={}'.format(x, _quote_if_str(getattr(self, x))),
                attrs)
        )
        return f'{cn}({attr_string})'


class AsyncModel(BaseModel):

    @classmethod
    def connection(cls) -> PoolManager:
        return cls._connection

    async def save(self, **kwargs):
        async with self.connection() as conn:
            async with conn.transaction():
                statement = f"""
                UPDATE {self.__class__.__name__} SET {','.join([f'{key} = ${index + 1}' for index, key in enumerate(kwargs.keys())])}
                WHERE uid = ${len(kwargs.keys()) + 1} 
                """
                row = await conn.execute(statement, *[value for value in list(kwargs.values()) + [str(self.uid)]])
    @classmethod
    async def all(cls):
        async with cls.connection() as conn:
            async with conn.transaction():
                rows = await conn.fetch(f'select * from {cls.__name__.lower()}')
        return list(dict(row) for row in rows)

    @classmethod
    async def filter(cls, **kwargs):
        async with cls.connection() as conn:
            async with conn.transaction():
                req_kwargs = ' AND '.join([f"{key} = '{value}'" for key, value in kwargs.items()])
                rows = await conn.fetch(f'select * from {cls.__name__.lower()} where {req_kwargs}')

                return list(dict(row) for row in rows)

    async def create(self):
        async with self.connection() as conn:
            async with conn.transaction():
                statement = f"""
                    INSERT INTO {self.__class__.__name__.lower()} ({','.join(self.get_insert_column())})
                    VALUES ({','.join([f'${index + 1}' for index in range(len(self.get_insert_column()))])})
                    """
                await conn.execute(statement, *[getattr(self, key) for key in self.get_insert_column()])

                result = await conn.fetchrow(
                    f"select * from {self.__class__.__name__.lower()} where uid = '{getattr(self, 'uid')}'")
                return dict(result)

    @classmethod
    async def get(cls, **kwargs):
        async with cls.connection() as conn:
            async with conn.transaction():
                req_kwargs = ' AND '.join([f"{key} = '{value}'" for key, value in kwargs.items()])
                result = await conn.fetchrow(f'select * from {cls.__name__.lower()} where {req_kwargs}')
                return None if result is None else dict(result)

    @classmethod
    async def join(cls):
        async with cls.connection() as conn:
            async with conn.transaction():
                related_model: BaseModel = getattr(cls, cls.get_related_column()[0]).related
                statement = f"""
                    SELECT * FROM {related_model.__name__} JOIN  {cls.__name__} 
                    ON {cls.__name__.lower()}.{cls.primary_key()[0]} = {related_model.__name__.lower()}.{related_model.get_fk()[0]}
                """
                rows = await conn.fetch(statement)
                return list(dict(row) for row in rows)

    def __init_subclass__(cls, connection=None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._connection = connection
