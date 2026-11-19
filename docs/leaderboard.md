# Leaderboard

Redis stores an ordered set named `leaderboard`. Each member is a user id. Each score is a float. Postgres stores the user rows. The index reaches Postgres only through a serializer you pass on each call.

`Serializer.serialize` and `Serializer.deserialize` are synchronous. This tutorial uses `build_ordered_set_index` and a synchronous SQLAlchemy session.

`add`, `rank`, `score`, and `remove` take a `User`. Those methods call `serialize` on the serializer you pass before they talk to Redis. Redis keeps the id string, under the key `leaderboard`.

## Install

```bash
pip install "cachebind[redis]" "sqlalchemy>=2" "psycopg[binary]"
```

Postgres and Redis for a local run:

```bash
docker run --name cachebind-postgres -e POSTGRES_PASSWORD=cachebind -e POSTGRES_DB=cachebind -p 5432:5432 -d postgres:16
docker run --name cachebind-redis -p 6379:6379 -d redis:7
```

The database URL is `postgresql+psycopg://postgres:cachebind@localhost:5432/cachebind`.

## Users

`User` is a SQLAlchemy model. The primary key is a UUID. Create the table, then insert five rows.

```python
import uuid

from sqlalchemy import String, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String)


engine = create_engine("postgresql+psycopg://postgres:cachebind@localhost:5432/cachebind")
sessions = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)

ada = User(id=uuid.UUID("12345678-1234-5678-1234-567812345678"), name="Ada")
grace = User(id=uuid.UUID("87654321-4321-8765-4321-876543218765"), name="Grace")
lin = User(id=uuid.UUID("11111111-1111-4111-8111-111111111111"), name="Lin")
maya = User(id=uuid.UUID("22222222-2222-4222-8222-222222222222"), name="Maya")
omar = User(id=uuid.UUID("33333333-3333-4333-8333-333333333333"), name="Omar")

with sessions.begin() as session:
    session.add_all([ada, grace, lin, maya, omar])
```

`expire_on_commit=False` keeps `ada.id` on the instance after that session closes. `serialize` reads `value.id` on every write.

The snippets in this tutorial are one program, in this order.

## Serializer

`UserSerializer` declares `Serializer[User, str]`. The builder checks that declaration. `member_type` must be `User`, and the Redis storage member type is `str`.

`UserSerializer` takes one open `Session`. `serialize` returns `str(value.id)`. `mserialize` returns those id strings in input order. `deserialize` loads the row for the stored UUID and returns that `User`. A missing row raises `ValueError`. `mdeserialize` loads every stored id with one query. The query does not keep input order, so that method puts each `User` back in that order. `expunge` detaches each loaded `User` so its attributes stay available after the session closes.

Pass `serializer=UserSerializer(session)` on every index call that serializes or deserializes while `session` is open.

```python
from collections.abc import Sequence

from sqlalchemy import select

from cachebind import Serializer


class UserSerializer(Serializer[User, str]):
    def __init__(self, session: Session) -> None:
        self.session = session

    def serialize(self, value: User) -> str:
        return str(value.id)

    def deserialize(self, value: str) -> User:
        user_id = uuid.UUID(value)
        row = self.session.get(User, user_id)
        if row is None:
            raise ValueError(f"no user {user_id}")
        self.session.expunge(row)
        return row

    def mserialize(self, values: Sequence[User]) -> list[str]:
        return [str(value.id) for value in values]

    def mdeserialize(self, values: Sequence[str]) -> list[User]:
        ids = [uuid.UUID(value) for value in values]
        rows = self.session.scalars(select(User).where(User.id.in_(ids))).all()
        by_id = {row.id: row for row in rows}
        for row in rows:
            self.session.expunge(row)
        loaded: list[User] = []
        for user_id in ids:
            row = by_id.get(user_id)
            if row is None:
                raise ValueError(f"no user {user_id}")
            loaded.append(row)
        return loaded
```

## Index

Build the index once with `NoopSerializer[User, str]()` as the default serializer on the registered class. That default does not talk to Postgres. A second build with the same key raises `ValueError`. Pass the Redis client into every call.

```python
from redis import Redis

from cachebind import NoopSerializer, build_ordered_set_index
from cachebind.storage import RedisOrderedSetStorage

leaderboard = build_ordered_set_index(
    "leaderboard",
    member_type=User,
    serializer=NoopSerializer[User, str](),
    storage=RedisOrderedSetStorage(),
)

client = Redis(decode_responses=True)
```

## Scores

`add` stores the user id with a score. Calling `add` again for the same user replaces the score.

```python
with sessions() as session:
    user_serializer = UserSerializer(session)
    leaderboard.add(client, member=maya, score=900.0, serializer=user_serializer)
    leaderboard.add(client, member=ada, score=1500.0, serializer=user_serializer)
    leaderboard.add(client, member=ada, score=1800.0, serializer=user_serializer)
    leaderboard.add(client, member=omar, score=2100.0, serializer=user_serializer)
    leaderboard.add(client, member=grace, score=2200.0, serializer=user_serializer)
    leaderboard.add(client, member=lin, score=2500.0, serializer=user_serializer)
```

From the lowest score to the highest, the board is Maya, Ada, Omar, Grace, Lin. `rank` counts that way, starting at `0`.

`rev_range_with_scores` counts from the highest score. Both ends are inclusive. The first three most rated users are indexes `0` through `2`. That call uses `mdeserialize`, so one query loads Lin, Grace, and Omar from Postgres.

```python
with sessions() as session:
    top = leaderboard.rev_range_with_scores(
        client,
        start=0,
        stop=2,
        serializer=UserSerializer(session),
    )
```

`top` is `[(lin, 2500.0), (grace, 2200.0), (omar, 2100.0)]`.

`rev_rank` counts from the highest score, starting at `0`.

```python
with sessions() as session:
    user_serializer = UserSerializer(session)
    place = leaderboard.rev_rank(client, lin, serializer=user_serializer)
    points = leaderboard.score(client, lin, serializer=user_serializer)
```

Lin's `rev_rank` is `0` and the score is `2500.0`. Grace is `1`. Maya is `4`. A missing user returns `None`.

`remove` drops one member. A missing member is not an error. Ordered sets have no TTL.

```python
with sessions() as session:
    leaderboard.remove(client, ada, serializer=UserSerializer(session))
```