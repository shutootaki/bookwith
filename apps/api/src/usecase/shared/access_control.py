"""所有者検証の共通ヘルパー."""

from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


def resolve_owned_or_raise(
    *,
    find_for_user: Callable[[], T | None],
    find_any: Callable[[], T | None],
    not_found_exc: BaseException,
    forbidden_exc: BaseException,
) -> T:
    """所有者付き取得 → 不在時に存在確認 → 404/403 を振り分ける.

    所有者違反時の 403 と未存在の 404 を区別したい呼出箇所で使う。
    所有者検証クエリで担保するため通常は二重防御として entity 側でも
    `assert_owned_by` を呼ぶこと。
    """
    scoped = find_for_user()
    if scoped is not None:
        return scoped
    if find_any() is None:
        raise not_found_exc
    raise forbidden_exc


async def resolve_owned_or_raise_async(
    *,
    find_for_user: Callable[[], Awaitable[T | None]],
    find_any: Callable[[], Awaitable[T | None]],
    not_found_exc: BaseException,
    forbidden_exc: BaseException,
) -> T:
    """`resolve_owned_or_raise` の非同期版."""
    scoped = await find_for_user()
    if scoped is not None:
        return scoped
    if await find_any() is None:
        raise not_found_exc
    raise forbidden_exc
