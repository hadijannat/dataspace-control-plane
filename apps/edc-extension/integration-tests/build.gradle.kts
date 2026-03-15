dependencies {
    testImplementation(project(":modules:common"))
    testImplementation(project(":modules:common:shared-model"))
    testImplementation(testFixtures(project(":modules:common:test-fixtures")))
    testImplementation(project(":modules:control-plane"))
    testImplementation(project(":modules:control-plane:policy-functions"))
    testImplementation(project(":modules:control-plane:participant-context"))
    testImplementation(project(":modules:control-plane:management-webhooks"))
    testImplementation(project(":modules:control-plane:contract-listeners"))
    testImplementation(project(":modules:data-plane"))
    testImplementation(project(":modules:data-plane:http-decorators"))
    testImplementation(project(":modules:data-plane:aas-bridge"))
    testImplementation(project(":modules:data-plane:transfer-observers"))
    testImplementation(project(":modules:auth"))
    testImplementation(project(":modules:auth:custom-web-contexts"))
    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.assertj)
}

tasks.test {
    useJUnitPlatform()
}
