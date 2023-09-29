from app import model as m
from enum import Enum


class assetAction(str, Enum):
    read = "READ"
    edit = "EDIT"
    request_datashare = "REQUEST"


class organisationAction(str, Enum):
    create = "CREATE_ASSET"
    view_shares = "VIEW_SHARE_REQUESTS"
    review_shares = "REVIEW_SHARE_REQUESTS"


class UserAccessRights:
    def __init__(self, user):
        if user.org:
            self.org_id = user.org.slug

    def can_view_asset(self, asset: m.DatasetResponse | m.DataServiceResponse):
        return asset.accessRights == m.rightsStatement.open

    def can_add_asset(self, org_slug):
        return False

    def can_edit_asset(self, asset: m.DatasetResponse | m.DataServiceResponse):
        return False

    def can_request_data(self, asset: m.DatasetResponse | m.DataServiceResponse):
        return False

    def can_view_share_request(self, request: m.ShareRequest):
        return False

    def can_review_share_request(self, request: m.ShareRequest):
        return False

    def has_asset_permission(
        self, action: assetAction, asset: m.DatasetResponse | m.DataServiceResponse
    ):
        match action:
            case assetAction.read:
                return self.can_view_asset(asset)
            case assetAction.edit:
                return self.can_edit_asset(asset)
            case assetAction.request_datashare:
                return self.can_request_data(asset)
            case _:
                raise ValueError(f"Invalid action for asset: {action}")

    def has_org_permission(
        self, action: organisationAction, organisation: m.Organisation
    ):
        match action:
            case organisationAction.create:
                return self.can_add_asset(organisation.slug)
            case organisationAction.view_shares:
                return self.can_view_share_request(organisation.slug)
            case organisationAction.review_shares:
                return self.can_review_share_request(organisation.slug)
            case _:
                raise ValueError(f"Invalid action for organisation: {action}")


class MemberAccessRights(UserAccessRights):
    def can_view_asset(self, asset: m.DatasetResponse | m.DataServiceResponse):
        return True

    def can_request_data(self, asset: m.DatasetResponse | m.DataServiceResponse):
        return True


class PublisherAccessRights(MemberAccessRights):
    def can_add_asset(self, org_slug):
        return self.org_id == org_slug

    def can_edit_asset(self, asset: m.DatasetResponse | m.DataServiceResponse):
        return self.org_id == asset.organisation.slug


class ShareReviewerAccessRights(MemberAccessRights):
    def can_view_share_request(self, org_slug):
        return self.org_id == org_slug

    def can_review_share_request(self, org_slug):
        return self.org_id == org_slug


class AdminAccessRights(MemberAccessRights):
    def can_view_share_request(self, org_slug):
        return self.org_id == org_slug


class OpsAdminAccessRights(UserAccessRights):
    # OPS Admin can publish to any organisation
    def can_add_asset(self, org_slug):
        return True


class UserWithAccessRights:
    def __init__(self, user):
        self.access_rights = [UserAccessRights(user)]
        for perm in user.permission:
            match perm:
                case m.userPermission.member:
                    self.access_rights.append(MemberAccessRights(user))
                case m.userPermission.publisher:
                    self.access_rights.append(PublisherAccessRights(user))
                case m.userPermission.reviewer:
                    self.access_rights.append(ShareReviewerAccessRights(user))
                case m.userPermission.org_admin:
                    self.access_rights.append(AdminAccessRights(user))
                case m.userPermission.ops_admin:
                    self.access_rights.append(OpsAdminAccessRights(user))

    def has_asset_permission(
        self, action: assetAction, asset: m.DatasetResponse | m.DataServiceResponse
    ):
        for permission in self.access_rights:
            if permission.has_asset_permission(action, asset):
                return True
        return False

    def has_org_permission(
        self, action: organisationAction, organisation: m.Organisation
    ):
        for permission in self.access_rights:
            if permission.has_org_permission(action, organisation):
                return True
        return False
