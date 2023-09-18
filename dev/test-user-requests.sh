TOKEN=



USER_ID=
ASSET_ID=fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1


if [ -z "$USER_ID" ] || [ -z "$TOKEN" ]; then
    echo "Paste your user ID and token into the variables"
    exit 1
fi
print_with_spacing() {
    echo -e "\n\n$1"
}

compare() {
    local expected="$1"
    local result="$2"
    if [[ "${result,,}" == "${expected,,}" ]]; then
        echo -e "\e[32mOK\e[0m"  # Green text for "OK"
    else
        echo -e "\e[31mFAIL\e[0m Expected: $expected, Result: $result"  # Red text for "not ok"
    fi
}

curl_as_anon_user() {
    local path="$1"
    local expected="$2"
    local result
    result=$(curl -s -X GET "http://localhost:8000/users/$path" \
             -H 'accept: application/json')
    compare $expected $result
}

curl_as_ops_user() {
    local path="$1"
    local expected="$2"
    local result

    result=$(curl -s -X GET "http://localhost:8000/users/$path" \
         -H 'accept: application/json' \
         -H 'x-api-key: defe70c1e28bf1b5141f1e5ccb75f014811e0247d55e20562d83ff9c4a7a9c33')
    compare $expected $result
}

curl_as_user() {
    local path="$1"
    local expected="$2"
    local result

    result=$(curl -s -X GET "http://localhost:8000/users/$path" \
         -H 'accept: application/json' \
         -H "Authorization: Bearer ${TOKEN}")
    compare $expected $result
}


change_user_role() {
    local oldrole="$1"
    local role="$2"
    echo "
        Changing user role to $role from $oldrole 
        "
    curl -X 'PUT' \
         "http://localhost:8000/users/${USER_ID}/permissions" \
         -H 'accept: application/json' \
         -H 'x-api-key: defe70c1e28bf1b5141f1e5ccb75f014811e0247d55e20562d83ff9c4a7a9c33' \
         -H 'Content-Type: application/json' \
         -d "{\"add\": [\"$role\"], \"remove\": [\"$oldrole\"]}"
    echo ""
}

READ_PERM_PATH="permission/asset/$ASSET_ID/READ"
EDIT_PERM_PATH="permission/asset/$ASSET_ID/EDIT"
REQUEST_PERM_PATH="permission/asset/$ASSET_ID/REQUEST"

DWP_CREATE_PERM_PATH="permission/organisation/department-for-work-pensions/CREATE_ASSET"
DWP_REVIEW_SHARE_PERM_PATH="permission/organisation/department-for-work-pensions/REVIEW_SHARE_REQUESTS"
DWP_VIEW_SHARE_PERM_PATH="permission/organisation/department-for-work-pensions/VIEW_SHARE_REQUESTS"

OFSTED_CREATE_PERM_PATH="permission/organisation/ofsted/CREATE_ASSET"
OFSTED_REVIEW_SHARE_PERM_PATH="permission/organisation/ofsted/REVIEW_SHARE_REQUESTS"
OFSTED_VIEW_SHARE_PERM_PATH="permission/organisation/ofsted/VIEW_SHARE_REQUESTS"

print_with_spacing "----------------ANONYMOUS-------------"

echo "READ ASSET:"
curl_as_anon_user $READ_PERM_PATH "false"
echo "EDIT ASSET"
curl_as_anon_user $EDIT_PERM_PATH "false"
echo "CREATE ASSET"
curl_as_anon_user $DWP_CREATE_PERM_PATH "false"
echo "REQUEST DATASHARE FOR ASSET"
curl_as_anon_user $REQUEST_PERM_PATH "false"
echo "VIEW RECIEVED DATASHARES"
curl_as_anon_user $DWP_REVIEW_SHARE_PERM_PATH "false"
echo "REVIEW RECIEVED DATASHARES"
curl_as_anon_user $DWP_REVIEW_SHARE_PERM_PATH "false"


print_with_spacing "---------------MEMBER---------------"
change_user_role "ADMINISTRATOR"  "MEMBER"

echo "READ"
curl_as_user $READ_PERM_PATH "true"
echo "EDIT"
curl_as_user $EDIT_PERM_PATH "false"
echo " REQUEST"
curl_as_user $REQUEST_PERM_PATH "true"
echo "CREATE"
curl_as_user $DWP_CREATE_PERM_PATH "false"
echo "VIEW RECIEVED DATASHARES"
curl_as_user $DWP_VIEW_SHARE_PERM_PATH "false"
echo "REVIEW RECIEVED DATASHARES"
curl_as_user $DWP_REVIEW_SHARE_PERM_PATH "false"

print_with_spacing "---------------PUBLISHER---------------"
change_user_role "MEMBER" "PUBLISHER"

echo "READ"
curl_as_user $READ_PERM_PATH "true"
echo "EDIT"
curl_as_user $EDIT_PERM_PATH "true"
echo "REQUEST"
curl_as_user $REQUEST_PERM_PATH "true"
echo "CREATE in my org"
curl_as_user $DWP_CREATE_PERM_PATH "true"
echo "VIEW RECIEVED DATASHARES in my org"
curl_as_user $DWP_VIEW_SHARE_PERM_PATH "false"
echo "REVIEW RECIEVED DATASHARES in my org"
curl_as_user $DWP_REVIEW_SHARE_PERM_PATH "false"

echo "CREATE in another org"
curl_as_user $OFSTED_CREATE_PERM_PATH "false"
echo "VIEW RECIEVED DATASHARES in another org"
curl_as_user $OFSTED_VIEW_SHARE_PERM_PATH "false"
echo "REVIEW RECIEVED DATASHARES in another org"
curl_as_user $OFSTED_REVIEW_SHARE_PERM_PATH "false"


print_with_spacing "---------------REVIEWER---------------"
change_user_role "PUBLISHER" "SHARE_REVIEWER"

echo "READ"
curl_as_user $READ_PERM_PATH "true"
echo "EDIT"
curl_as_user $EDIT_PERM_PATH "false"
echo "REQUEST"
curl_as_user $REQUEST_PERM_PATH "true"
echo "CREATE"
curl_as_user $DWP_CREATE_PERM_PATH "false"
echo "VIEW RECIEVED DATASHARES"
curl_as_user $DWP_VIEW_SHARE_PERM_PATH "true"
echo "REVIEW RECIEVED DATASHARES"
curl_as_user $DWP_REVIEW_SHARE_PERM_PATH "true"


print_with_spacing "---------------ORG ADMIN---------------"
change_user_role "SHARE_REVIEWER" "ADMINISTRATOR"

echo "READ"
curl_as_user $READ_PERM_PATH "true"
echo "EDIT"
curl_as_user $EDIT_PERM_PATH "false"
echo "REQUEST"
curl_as_user $REQUEST_PERM_PATH "true"
echo "CREATE"
curl_as_user $DWP_CREATE_PERM_PATH "false"
echo "VIEW RECIEVED DATASHARES"
curl_as_user $DWP_VIEW_SHARE_PERM_PATH "true"
echo "REVIEW RECIEVED DATASHARES"
curl_as_user $DWP_REVIEW_SHARE_PERM_PATH "false"

print_with_spacing "---------------MULTI ADMIN---------------"

curl -X 'PUT' \
  "http://localhost:8000/users/${USER_ID}/permissions" \
  -H 'accept: application/json' \
  -H 'x-api-key: defe70c1e28bf1b5141f1e5ccb75f014811e0247d55e20562d83ff9c4a7a9c33' \
  -H 'Content-Type: application/json' \
  -d '{
  "add": ["ADMINISTRATOR", "PUBLISHER", "SHARE_REVIEWER", "MEMBER"]
}'

echo "READ"
curl_as_user $READ_PERM_PATH "true"
echo "EDIT"
curl_as_user $EDIT_PERM_PATH "true"
echo "REQUEST"
curl_as_user $REQUEST_PERM_PATH "true"
echo "CREATE"
curl_as_user $DWP_CREATE_PERM_PATH "true"
echo "VIEW RECIEVED DATASHARES"
curl_as_user $DWP_VIEW_SHARE_PERM_PATH "true"
echo "REVIEW RECIEVED DATASHARES"
curl_as_user $DWP_REVIEW_SHARE_PERM_PATH "true"
