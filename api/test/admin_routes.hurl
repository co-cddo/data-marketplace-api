# ***********************
# *     LIST USERS      *
# ***********************

# API returns 401 if no key is provided
GET {{URL}}/users
HTTP 401

# API returns 401 if incorrect key is provided
GET {{URL}}/users
x-api-key: A
HTTP 401

# API returns 200 if correct key is provided
GET {{URL}}/users
x-api-key: {{OPS_API_KEY}}
HTTP 200
[Captures]
user_id: jsonpath "$[0]['@id']"


# ************************
# *     DELETE USER      *
# ************************

# API returns 401 if no key is provided
DELETE {{URL}}/users/{{user_id}}
HTTP 401

# API returns 401 if incorrect key is provided
GET {{URL}}/users/{{user_id}}
x-api-key: A
HTTP 401


# ***********************
# *     SET ORG         *
# ***********************

# API returns 401 if no key is provided
PUT {{URL}}/users/{{user_id}}/org
Content-Type: application/json
{
    "org": "ofsted"
}
HTTP 401

# API returns 401 if incorrect key is provided
PUT {{URL}}/users/{{user_id}}/org
x-api-key: A
Content-Type: application/json
{
    "org": "ofsted"
}
HTTP 401

# API returns 200 if correct key is provided
PUT {{URL}}/users/{{user_id}}/org
x-api-key: {{OPS_API_KEY}}
Content-Type: application/json
{
    "org": "ofsted"
}
HTTP 200

# Check that the user's org has been updated
GET {{URL}}/users/{{user_id}}
x-api-key: {{OPS_API_KEY}}
HTTP 200
[Asserts]
jsonpath "$.org.slug" == "ofsted"


# ************************
# *     PERMISSIONS      *
# ************************

# API returns 401 if no key is provided
PUT {{URL}}/users/{{user_id}}/permissions
Content-Type: application/json
{
    "add": ["OPS", "ADMINISTRATOR"],
    "remove": ["SHARE_REVIEWER", "PUBLISHER"]
}
HTTP 401

# API returns 401 if incorrect key is provided
PUT {{URL}}/users/{{user_id}}/permissions
x-api-key: A
Content-Type: application/json
{
    "add": ["OPS", "ADMINISTRATOR"],
    "remove": ["SHARE_REVIEWER", "PUBLISHER"]
}
HTTP 401

# API returns 200 if the correct key is provided
PUT {{URL}}/users/{{user_id}}/permissions
x-api-key: {{OPS_API_KEY}}
Content-Type: application/json
{
    "add": ["OPS", "ADMINISTRATOR"],
    "remove": ["SHARE_REVIEWER", "PUBLISHER"]
}
HTTP 200

# Check that the user's permissions have been updated
GET {{URL}}/users/{{user_id}}
x-api-key: {{OPS_API_KEY}}
HTTP 200
[Asserts]
jsonpath "$.permission" includes "OPS"
jsonpath "$.permission" includes "ADMINISTRATOR"
jsonpath "$.permission" not includes "SHARE_REVIEWER"
jsonpath "$.permission" not includes "PUBLISHER"

# Swap the permissions and check again
PUT {{URL}}/users/{{user_id}}/permissions
x-api-key: {{OPS_API_KEY}}
Content-Type: application/json
{
    "remove": ["OPS", "ADMINISTRATOR"],
    "add": ["SHARE_REVIEWER", "PUBLISHER"]
}
HTTP 200

# Check that the user's permissions have been updated
GET {{URL}}/users/{{user_id}}
x-api-key: {{OPS_API_KEY}}
HTTP 200
[Asserts]
jsonpath "$.permission" not includes "OPS"
jsonpath "$.permission" not includes "ADMINISTRATOR"
jsonpath "$.permission" includes "SHARE_REVIEWER"
jsonpath "$.permission" includes "PUBLISHER"