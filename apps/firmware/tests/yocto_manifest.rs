//! The Yocto recipe builds these sources from `yocto/Cargo.toml`, a separate offline
//! workspace. It must declare the same package identity and dependencies as
//! `Cargo.toml`; after changing both, refresh `yocto/Cargo.lock` and the crate
//! metadata with `just firmware-update-crates`.

use std::{
    collections::BTreeMap,
    path::{Component, Path, PathBuf},
};

const PACKAGE: &str = env!("CARGO_MANIFEST_DIR");

/// `name -> spec` for the `[dependencies]` table, one dependency per line,
/// with each `path` resolved against the manifest's directory.
fn dependencies(manifest: &str, directory: &Path) -> BTreeMap<String, String> {
    manifest
        .lines()
        .skip_while(|line| line.trim() != "[dependencies]")
        .skip(1)
        .take_while(|line| !line.trim_start().starts_with('['))
        .filter_map(|line| line.split_once('='))
        .map(|(name, spec)| (name.trim().to_owned(), resolve_path(spec.trim(), directory)))
        .collect()
}

fn resolve_path(spec: &str, directory: &Path) -> String {
    let Some((before, rest)) = spec.split_once("path = \"") else {
        return spec.to_owned();
    };
    let Some((relative, after)) = rest.split_once('"') else {
        return spec.to_owned();
    };
    let mut resolved = PathBuf::new();
    for component in directory.join(relative).components() {
        match component {
            Component::ParentDir => {
                resolved.pop();
            }
            Component::CurDir => {}
            other => resolved.push(other),
        }
    }
    format!("{before}path = \"{}\"{after}", resolved.display())
}

/// The value of a top-level `[package]` key written as `key = "value"`.
fn package_field<'a>(manifest: &'a str, key: &str) -> Option<&'a str> {
    manifest.lines().find_map(|line| {
        let (name, value) = line.split_once('=')?;
        (name.trim() == key).then(|| value.trim().trim_matches('"'))
    })
}

fn read(path: &Path) -> String {
    std::fs::read_to_string(path).unwrap_or_else(|error| panic!("{}: {error}", path.display()))
}

#[test]
fn yocto_manifest_declares_the_same_dependencies() {
    let package = Path::new(PACKAGE);
    let yocto = package.join("yocto");
    assert_eq!(
        dependencies(&read(&yocto.join("Cargo.toml")), &yocto),
        dependencies(&read(&package.join("Cargo.toml")), package),
        "apps/firmware/yocto/Cargo.toml [dependencies] differ from apps/firmware/Cargo.toml"
    );
}

#[test]
fn yocto_manifest_declares_the_same_package() {
    let manifest = read(&Path::new(PACKAGE).join("yocto/Cargo.toml"));
    for (key, expected) in [
        ("version", env!("CARGO_PKG_VERSION")),
        ("rust-version", env!("CARGO_PKG_RUST_VERSION")),
        ("license", env!("CARGO_PKG_LICENSE")),
    ] {
        assert_eq!(
            package_field(&manifest, key),
            Some(expected),
            "package.{key}"
        );
    }
}

#[test]
fn a_changed_dependency_is_detected() {
    let directory = Path::new("/repo/apps/firmware");
    let source =
        "[dependencies]\nlogger = { path = \"../../crates/logger\" }\ntokio = \"1.53.1\"\n";
    let mirror =
        "[dependencies]\nlogger = { path = \"../../../crates/logger\" }\ntokio = \"1.53.1\"\n";
    let yocto = directory.join("yocto");
    assert_eq!(
        dependencies(mirror, &yocto),
        dependencies(source, directory)
    );
    let bumped = mirror.replace("1.53.1", "1.53.3");
    assert_ne!(
        dependencies(&bumped, &yocto),
        dependencies(source, directory)
    );
    assert_ne!(
        dependencies(&format!("{mirror}serde = \"1\"\n"), &yocto),
        dependencies(source, directory)
    );
}
