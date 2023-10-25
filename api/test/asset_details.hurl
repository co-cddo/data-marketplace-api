# *******************************************************
# *  These tests simply try to GET each sample asset    *
# *     in the database, to make sure that each asset   *
# *     satisfies the Pydantic model.                   *
# *******************************************************

# Address lookup
GET {{URL}}/catalogue/fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1
HTTP 200

# OS Postcodes
GET {{URL}}/catalogue/b3ae48af-c130-44ac-8341-5dead13c5427
HTTP 200

# Bathing Water
GET {{URL}}/catalogue/cd62b912-60fb-427a-bf87-a3b7c2364e6d
HTTP 200

# Bathing Water Monitoring Locations
GET {{URL}}/catalogue/e45b6315-88dd-4e2a-bb0e-0846bbfa4fd3
HTTP 200

# MoJ Data First Crown Court defendant case level dataset
GET {{URL}}/catalogue/f0a166b6-13e0-43c3-ad97-9f835f7088dd
HTTP 200

# MoJ Data First magistrates' court defendant case level dataset
GET {{URL}}/catalogue/3feff58c-faaf-484b-a436-8a80d918e6fa
HTTP 200

# Interest Restriction Return (IRR) API
GET {{URL}}/catalogue/debc41c4-159c-4c74-99de-88af20b499a2
HTTP 200