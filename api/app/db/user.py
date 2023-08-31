from app.db.sparql import users_db


def new_user(user_id: str, user_email: str):
    query_results = users_db.run_update(
        "new_user", user_id=user_id, user_email=user_email
    )
    return query_results


def get_by_id(user_id: str) -> str | None:
    query_results = users_db.run_query("get_user_by_id", user_id=user_id)
    assert len(query_results) <= 1, "Found multiple users with the same email address."

    if not query_results:
        return None
    return query_results[0]
