from temporalio.exceptions import ApplicationError


class EvidenceExportError(ApplicationError):
    pass


class EvidenceCollectionError(EvidenceExportError):
    pass


class ManifestBuildError(EvidenceExportError):
    pass


class SigningError(EvidenceExportError):
    pass


class ExportStorageError(EvidenceExportError):
    pass
