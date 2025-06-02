from qqutils.sqliteutils import (
    sqlalchemy_execute,
    sqlalchemy_get_engine,
    sqlalchemy_get_session,
    sqlite3_put,
    sqlite3_get,
    sqlite3_delete,
    sqlite3_jput,
    sqlite3_jget,
    sqlite3_dump,
    sqlite3_tables,
)


def test_sqlite3():
    import time

    k = str(time.time())
    assert sqlite3_put(k, 'b') is None
    assert sqlite3_put(k, 'c') == 'b'
    assert sqlite3_get(k) == 'c'

    k = str(time.time())
    assert sqlite3_put(k, '1') is None
    assert sqlite3_get(k, cast=int) == 1
    sqlite3_delete(k)
    assert sqlite3_get(k) is None

    k = str(time.time())
    assert sqlite3_jput(k, {'a': 1}) is None
    assert sqlite3_jput(k, {'b': 2}) == {'a': 1}
    assert sqlite3_jget(k) == {'b': 2}

    sqlite3_dump()

    assert {'name': '__cache__'} in sqlite3_tables()


def test_sqlalchemy():
    """https://www.cnblogs.com/lsdb/p/9835894.html"""
    from sqlalchemy.orm import declarative_base
    from sqlalchemy import Column, Integer, String
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'users'
        # 如果表在同一个数据库服务（datebase）的不同数据库中（schema），可使用schema参数进一步指定数据库
        # __table_args__ = {'schema': 'test_database'}

        id = Column(Integer, primary_key=True, autoincrement=True)

        name = Column(String(20))
        fullname = Column(String(32))
        password = Column(String(32))

        def __repr__(self):
            return "<User(name='%s', fullname='%s', password='%s')>" % (
                self.name, self.fullname, self.password)

    engine = sqlalchemy_get_engine("/tmp/test.db")
    session = sqlalchemy_get_session(engine)

    # 创建数据表
    User.__table__.create(engine, checkfirst=True)

    # 插入数据
    if session.query(User).count() < 3:
        session.add(User(name='wendy', fullname='Wendy Williams', password='foobar'))
        session.add(User(name='mary', fullname='Mary Contrary', password='xxg527'))
        session.add(User(name='fred', fullname='Fred Flinstone', password='blah'))
        session.commit()

    # 查询数据
    for instance in session.query(User).order_by(User.id):
        print(instance.name, instance.fullname)

    # 更新数据
    session.query(User).filter(User.name == 'wendy').update({
        'fullname': 'Wendy Williams II'
    })
    session.commit()

    # 删除数据
    session.query(User).filter(User.name == 'fred').delete()
    session.commit()

    output = sqlalchemy_execute('select * from users', engine)
    print(output)
