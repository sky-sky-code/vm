import uuid
import os
from vm.asyncorm import (PoolManager, AsyncModel,
                         Column, ForeignKeyColumn, RelatedColumn)
import sys

HOST = os.environ.get('POSTGRES_HOST', 'localhost')

manager = PoolManager(
    user='dev',
    password='dev',
    host=HOST,
    port='5432',
    database='vm'
)


class VM(AsyncModel, connection=manager):
    uid = Column(primary_key=True)
    ram = Column()
    cpu = Column()
    token = Column()

    hard_disk = RelatedColumn('HardDisk', module=sys.modules[__name__])


class HardDisk(AsyncModel, connection=manager):
    uid = Column(primary_key=True)
    hard_disk_memory = Column()
    vm = ForeignKeyColumn(VM)
