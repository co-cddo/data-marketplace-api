from typing import List, Set

from .utils import enrich_user_org, aggregate_results, aggregate_query_results_by_key
from app import model as m
from app.db.sparql import users_db
from app.utils import lookup_organisation


def new_user(user_id: str, user_email: str) -> m.RegisteredUser:
    users_db.run_update("create", user_id=user_id, user_email=user_email)
    user = get_by_id(user_id)
    return user


def _maybe_make_permission_a_list(user_dict):
    permission = user_dict.get("permission")
    if permission is None:
        return user_dict
    elif isinstance(permission, Set):
        user_dict["permission"] = list(permission)
        return user_dict
    else:
        user_dict["permission"] = [permission]
        return user_dict


def _query_result_to_user(aggregated_query_result_for_user):
    user = _maybe_make_permission_a_list(aggregated_query_result_for_user)
    user = enrich_user_org(user)
    return m.RegisteredUser.model_validate(user)


def list_users() -> List[m.RegisteredUser]:
    query_results = users_db.run_query("list")
    users = aggregate_query_results_by_key(query_results, group_key="id")
    return [_query_result_to_user(u) for u in users]


def get_by_id(user_id: str) -> m.RegisteredUser | None:
    query_results = users_db.run_query("get_by_id", user_id=user_id)
    if not query_results:
        return None
    assert (
        len({u["id"] for u in query_results}) <= 1
    ), "Found multiple users with the same email address."
    user = aggregate_results(query_results)
    return _query_result_to_user(user)


def delete_by_id(user_id: str) -> m.SPARQLUpdate:
    res = users_db.run_update("delete_by_id", user_id=user_id)
    return res


def edit_org(user_id, org):
    res = users_db.run_update("edit_org", user_id=user_id, org=org)
    return res


def complete_profile(user_id, org, jobTitle):
    res = users_db.run_update(
        "complete_profile", user_id=user_id, org=org, jobTitle=jobTitle
    )
    return res


def edit_permissions(user_id, permissions_to_add, permissions_to_remove):
    to_add = [f'"{val}"' for val in permissions_to_add]
    res = {"statusCode": 200, "message": "no update required"}
    if permissions_to_remove != []:
        res = users_db.run_update(
            "remove_permissions",
            user_id=user_id,
            to_remove=[f'"{val}"' for val in permissions_to_remove],
        )
        if res["statusCode"] != 200:
            return res
    if permissions_to_add != []:
        res = users_db.run_update("add_permissions", user_id=user_id, to_add=to_add)
    return res
