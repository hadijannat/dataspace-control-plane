rootProject.name = "dataspace-edc-extension"

include(
    // Common utilities
    ":modules:common",
    ":modules:common:shared-model",
    ":modules:common:test-fixtures",

    // Control-plane extensions
    ":modules:control-plane",
    ":modules:control-plane:policy-functions",
    ":modules:control-plane:participant-context",
    ":modules:control-plane:management-webhooks",
    ":modules:control-plane:contract-listeners",

    // Data-plane extensions
    ":modules:data-plane",
    ":modules:data-plane:http-decorators",
    ":modules:data-plane:aas-bridge",
    ":modules:data-plane:transfer-observers",

    // Auth extensions
    ":modules:auth",
    ":modules:auth:custom-web-contexts",

    // Integration tests (always last)
    ":integration-tests",
)
