from temporalio.exceptions import ApplicationError


class PublishAssetError(ApplicationError):
    pass


class MappingSnapshotError(PublishAssetError):
    pass


class PolicyCompileError(PublishAssetError):
    pass


class AssetPublishError(PublishAssetError):
    pass


class DiscoverabilityError(PublishAssetError):
    pass
