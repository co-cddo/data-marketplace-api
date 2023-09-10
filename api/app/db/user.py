from app.db.sparql import users_db
from app import model as m


def new_user(user_id: str, user_email: str) -> m.User:
    users_db.run_update("user/create", user_id=user_id, user_email=user_email)
    user = get_by_id(user_id)
    return user


def list_users():
    query_results = users_db.run_query("user/list")
    return query_results


def get_by_id(user_id: str) -> m.User | None:
    query_results = users_db.run_query("user/get_by_id", user_id=user_id)
    assert len(query_results) <= 1, "Found multiple users with the same email address."

    if not query_results:
        return None

    return m.User.model_validate(query_results[0])


def edit_org(user_id, org):
    res = users_db.run_update("user/edit_org", user_id=user_id, org=org)
    return res


def complete_profile(user_id, org, role):
    res = users_db.run_update(
        "user/complete_profile", user_id=user_id, org=org, role=role
    )
    return res
