plugins {
    `java-test-fixtures`
}

dependencies {
    api(libs.edc.spi.core)
    api(platform(libs.junit.bom))
    api(libs.junit.jupiter)
    api(libs.assertj)
    // EDC embedded runtime for integration tests (will resolve from EDC's test artifacts)
    // testFixturesApi("org.eclipse.edc:junit:${libs.versions.edc.get()}")
}
