# Trie (Prefix Tree)

Redis stores a trie named `cities`. Redis Search keeps that trie as one suggestion dictionary. Each suggestion string is a city name. Each score is that city's clicks. Each payload is the city id. Postgres stores the city rows. The index reaches Postgres only through a serializer you pass on each call.

`Serializer.serialize` and `Serializer.deserialize` are synchronous. This tutorial uses `build_trie_index` and a synchronous SQLAlchemy session.

`add` and `madd` take a city name, a `City`, and a score. Those methods call `serialize` on the serializer you pass before they talk to Redis. Redis keeps the id string as the payload, under the key `cities`. `search` reads the payloads for a prefix and deserializes each one with that serializer, so the cities come back from Postgres.

## Install

```bash
pip install "cachebind[redis]" "sqlalchemy>=2" "psycopg[binary]"
```

Postgres and Redis for a local run. The Redis 8 image includes suggestion commands.

```bash
docker run --name cachebind-postgres -e POSTGRES_PASSWORD=cachebind -e POSTGRES_DB=cachebind -p 5432:5432 -d postgres:16
docker run --name cachebind-redis -p 6379:6379 -d redis:8
```

The database URL is `postgresql+psycopg://postgres:cachebind@localhost:5432/cachebind`.

## Cities

`City` is a SQLAlchemy model. The table is `cities`, with `id`, `name`, and `clicks`. Create the table, then insert five rows.

```python
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

class Base(DeclarativeBase):
    pass


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    clicks: Mapped[int] = mapped_column(Integer)


engine = create_engine("postgresql+psycopg://postgres:cachebind@localhost:5432/cachebind")
sessions = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)

paris = City(id=1, name="Paris", clicks=900)
prague = City(id=2, name="Prague", clicks=700)
padua = City(id=3, name="Padua", clicks=200)
lyon = City(id=4, name="Lyon", clicks=400)
lisbon = City(id=5, name="Lisbon", clicks=300)

with sessions.begin() as session:
    session.add_all([paris, prague, padua, lyon, lisbon])
```

`expire_on_commit=False` keeps `paris.id` on the instance after that session closes. `serialize` reads `value.id` on every write.

The snippets in this tutorial are one program, in this order.

## Serializer

`CitySerializer` declares `Serializer[City, str]`. The builder checks that declaration. `member_type` must be `City`, and the Redis trie payload type is `str`.

`CitySerializer` takes one open `Session`. `serialize` returns `str(value.id)`. `mserialize` returns those id strings in input order. `deserialize` loads the row for the stored id and returns that `City`. A missing row raises `ValueError`. `mdeserialize` loads every stored id with one query. The query does not keep input order, so that method puts each `City` back in that order. `expunge` detaches each loaded `City` so its attributes stay available after the session closes.

Pass `serializer=CitySerializer(session)` on every index call that serializes or deserializes while `session` is open.

```python
from collections.abc import Sequence

from sqlalchemy import select

from cachebind import Serializer


class CitySerializer(Serializer[City, str]):
    def __init__(self, session: Session) -> None:
        self.session = session

    def serialize(self, value: City) -> str:
        return str(value.id)

    def deserialize(self, value: str) -> City:
        city_id = int(value)
        row = self.session.get(City, city_id)
        if row is None:
            raise ValueError(f"no city {city_id}")
        self.session.expunge(row)
        return row

    def mserialize(self, values: Sequence[City]) -> list[str]:
        return [str(value.id) for value in values]

    def mdeserialize(self, values: Sequence[str]) -> list[City]:
        ids = [int(value) for value in values]
        rows = self.session.scalars(select(City).where(City.id.in_(ids))).all()
        by_id = {row.id: row for row in rows}
        for row in rows:
            self.session.expunge(row)
        loaded: list[City] = []
        for city_id in ids:
            row = by_id.get(city_id)
            if row is None:
                raise ValueError(f"no city {city_id}")
            loaded.append(row)
        return loaded
```

## Index

Build the index once with `NoopSerializer[City, str]()` as the default serializer on the registered class. That default does not talk to Postgres. A second build with the same key raises `ValueError`. Pass the Redis client into every call. The client is created with `decode_responses=True`, so suggestion strings and payloads come back as text.

```python
from redis import Redis

from cachebind import NoopSerializer, build_trie_index
from cachebind.storage import RedisTrieStorage

cities = build_trie_index(
    "cities",
    member_type=City,
    serializer=NoopSerializer[City, str](),
    storage=RedisTrieStorage(),
)

client = Redis(decode_responses=True)
```

## Suggestions

Load the table into the trie. The suggestion string is `name`. The score is `clicks`. The payload is the id, because that is what `serialize` returns.

The suggestion string is the key inside the trie. A later entry with the same name replaces the earlier score and payload.

Each entry is `(string, member, score)`: the city name, the `City`, and the clicks.

```python
with sessions() as session:
    rows = list(session.scalars(select(City)))
    cities.madd(
        client,
        entries=[(row.name, row, float(row.clicks)) for row in rows],
        serializer=CitySerializer(session),
    )
```

`madd` runs while that session is open, so each row still has `name`, `id`, and `clicks`. It calls `mserialize` on `CitySerializer(session)` before it talks to Redis. Redis then holds five suggestions under `cities`: Paris at 900, Prague at 700, Padua at 200, Lyon at 400, and Lisbon at 300.

`search` completes a prefix. The match is case-sensitive. `P` matches every stored name that starts with `P`: Paris, Prague, and Padua. Redis ranks a match by its score, and a shorter remainder after the prefix ranks higher than a longer one with the same score. With these click counts the order is Paris, Prague, Padua. `search` then calls `mdeserialize` on their payloads through `CitySerializer(session)`, so one query loads those three rows from Postgres.

```python
with sessions() as session:
    matches = cities.search(
        client,
        prefix="P",
        serializer=CitySerializer(session),
    )
```

`matches[0].name` is `"Paris"` and `matches[0].clicks` is `900`. Then Prague, then Padua.

`limit` caps the number of cities. The default is 10. Paris outranks Padua, so a limit of one on the prefix `Pa` returns Paris.

```python
with sessions() as session:
    closer = cities.search(
        client,
        prefix="Pa",
        limit=1,
        serializer=CitySerializer(session),
    )
```

`closer[0].name` is `"Paris"`.

`Parix` is not a prefix of any stored name, so a plain search is empty.

```python
with sessions() as session:
    miss = cities.search(
        client,
        prefix="Parix",
        serializer=CitySerializer(session),
    )
```

`miss` is `[]`.

`fuzzy=True` also accepts a prefix one edit away from the stored name. `Parix` is one substitution away from `Paris`.

```python
with sessions() as session:
    fuzzy = cities.search(
        client,
        prefix="Parix",
        fuzzy=True,
        serializer=CitySerializer(session),
    )
```

`fuzzy[0].name` is `"Paris"`. A prefix shorter than three characters with `fuzzy=True` can scan the whole trie.

`length` counts suggestion strings.

```python
size = cities.length(client)
```

`size` is `5`.

`remove` drops one name. A missing name is not an error. The trie has no TTL.

```python
cities.remove(client, string="Lyon")
```

`cities.length(client)` is `4` after that. Calling `add` again for Lyon puts it back. `increment=True` adds the given score to the stored score and still replaces the payload.

```python
with sessions() as session:
    cities.add(
        client,
        string=lyon.name,
        member=lyon,
        score=float(lyon.clicks),
        serializer=CitySerializer(session),
    )
```