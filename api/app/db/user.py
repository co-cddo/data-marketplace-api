from typing import List

from .utils import enrich_user_org
from app import model as m
from app.db.sparql import users_db
from app.utils import lookup_organisation


def new_user(user_id: str, user_email: str) -> m.User:
    users_db.run_update("user/create", user_id=user_id, user_email=user_email)
    user = get_by_id(user_id)
    return user


def list_users() -> List[m.User]:
    query_results = users_db.run_query("user/list")
    users = [enrich_user_org(r) for r in query_results]
    return [m.User.model_validate(u) for u in users]


def get_by_id(user_id: str) -> m.User | None:
    query_results = users_db.run_query("user/get_by_id", user_id=user_id)
    assert len(query_results) <= 1, "Found multiple users with the same email address."

    if not query_results:
        return None

    user = query_results[0]
    user = enrich_user_org(user)
    return m.User.model_validate(user)


def delete_by_id(user_id: str) -> m.SPARQLUpdate:
    res = users_db.run_update("user/delete_by_id", user_id=user_id)
    return res


def edit_org(user_id, org):
    res = users_db.run_update("user/edit_org", user_id=user_id, org=org)
    return res


def complete_profile(user_id, org, role):
    res = users_db.run_update(
        "user/complete_profile", user_id=user_id, org=org, role=role
    )
    return res
